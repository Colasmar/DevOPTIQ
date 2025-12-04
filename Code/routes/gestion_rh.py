from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from Code.extensions import db
from Code.models.models import User, Role, UserRole
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

gestion_rh_bp = Blueprint('gestion_rh', __name__, url_prefix='/gestion_rh')

@gestion_rh_bp.route('/')
def gestion_rh_home():
    row = db.session.execute(text("SELECT * FROM entreprise_settings LIMIT 1")).mappings().fetchone()
    settings = dict(row) if row else {}
    roles = Role.query.order_by(Role.name).all()
    users = User.query.order_by(User.last_name).all()
    return render_template('gestion_rh.html', settings=settings, roles=roles, users=users)

@gestion_rh_bp.route('/update_settings', methods=['POST'])
def update_settings():
    data = request.form
    db.session.execute("DELETE FROM entreprise_settings")
    db.session.execute(text("""
        INSERT INTO entreprise_settings (work_hours_per_day, work_days_per_week, work_weeks_per_year, work_days_per_year)
        VALUES (:h, :d, :w, :y)
    """), {
        "h": data.get("work_hours_per_day"),
        "d": data.get("work_days_per_week"),
        "w": data.get("work_weeks_per_year"),
        "y": data.get("work_days_per_year")
    })
    db.session.commit()
    return redirect(url_for('gestion_rh.gestion_rh_home'))

@gestion_rh_bp.route('/assign_roles', methods=['POST'])
def assign_roles():
    user_id = request.form.get("user_id")
    role_ids = request.form.getlist("role_ids")
    db.session.query(UserRole).filter_by(user_id=user_id).delete()
    for rid in role_ids:
        db.session.add(UserRole(user_id=user_id, role_id=rid))
    db.session.commit()
    return redirect(url_for('gestion_rh.gestion_rh_home'))


import csv
from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@gestion_rh_bp.route('/import_roles', methods=['POST'])
def import_roles():
    file = request.files['role_file']
    if file and file.filename.endswith('.csv'):
        filepath = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(filepath)

        with open(filepath, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row:  # première colonne = nom du rôle
                    name = row[0].strip()
                    if name:
                        try:
                            db.session.execute(text("INSERT INTO roles (name) VALUES (:name)"), {'name': name})
                        except IntegrityError:
                            db.session.rollback()  # si doublon, ignorer
                        else:
                            db.session.commit()
    return redirect(url_for('gestion_rh.gestion_rh_home'))


@gestion_rh_bp.route('/update_single_setting', methods=['POST'])
def update_single_setting():
    key = request.form.get("key")
    value = request.form.get("value")

    # Récupère ou crée la ligne entreprise_settings
    row = db.session.execute(text("SELECT * FROM entreprise_settings LIMIT 1")).fetchone()
    if not row:
        db.session.execute(text("""
            INSERT INTO entreprise_settings (work_hours_per_day, work_days_per_week, work_weeks_per_year, work_days_per_year)
            VALUES (NULL, NULL, NULL, NULL)
        """))
        db.session.commit()

    # Effectue une mise à jour du champ concerné
    db.session.execute(text(f"""
        UPDATE entreprise_settings SET {key} = :val
    """), {'val': value})
    db.session.commit()
    return jsonify(success=True)



@gestion_rh_bp.route('/role', methods=['POST'])
def create_or_update_role():
    role_id = request.form.get('id')
    name = request.form.get('name').strip()

    if role_id:
        role = Role.query.get(role_id)
        if role:
            role.name = name
    else:
        new_role = Role(name=name)
        db.session.add(new_role)
    db.session.commit()
    return jsonify(success=True)

@gestion_rh_bp.route('/delete_role/<int:role_id>', methods=['POST'])
def delete_role(role_id):
    role = Role.query.get(role_id)
    if role:
        db.session.delete(role)
        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False), 404


@gestion_rh_bp.route('/collaborateurs')
def get_collaborateurs():
    search = request.args.get('search', '').lower()
    role_filter = request.args.get('role', '')

    query = db.session.query(User).join(UserRole, isouter=True).join(Role, isouter=True)

    if search:
        query = query.filter((User.first_name + ' ' + User.last_name).ilike(f"%{search}%"))

    if role_filter:
        query = query.filter(Role.name == role_filter)

    users = query.order_by(User.last_name).all()

    # Récupération manuelle des rôles pour chaque user
    user_roles = db.session.execute(text("""
        SELECT ur.user_id, r.name
        FROM user_roles ur
        JOIN roles r ON r.id = ur.role_id
    """)).fetchall()

    user_roles_map = {}
    for row in user_roles:
        user_roles_map.setdefault(row[0], []).append(row[1])

    return jsonify([
        {
            "id": u.id,
            "name": f"{u.first_name} {u.last_name}",
            "roles": user_roles_map.get(u.id, [])
        }
        for u in users
    ])


@gestion_rh_bp.route('/collaborateur_roles', methods=['POST'])
def update_collaborateur_roles():
    user_id = request.form.get('user_id')
    new_roles = request.form.getlist('role_ids[]')  # tableau de IDs
    db.session.query(UserRole).filter_by(user_id=user_id).delete()
    for rid in new_roles:
        db.session.add(UserRole(user_id=user_id, role_id=int(rid)))
    db.session.commit()
    return jsonify(success=True)


@gestion_rh_bp.route('/update_collaborator_name', methods=['POST'])
def update_collaborator_name():
    """
    Met à jour le nom d'un collaborateur.
    Body JSON: { "user_id": int, "name": "Prénom Nom" }
    """
    data = request.get_json()
    user_id = data.get('user_id')
    full_name = data.get('name', '').strip()
    
    if not user_id or not full_name:
        return jsonify(success=False, error="Données manquantes"), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify(success=False, error="Utilisateur non trouvé"), 404
    
    # Séparer prénom et nom (prend le premier mot comme prénom, le reste comme nom)
    parts = full_name.split(' ', 1)
    if len(parts) == 2:
        user.first_name = parts[0]
        user.last_name = parts[1]
    else:
        # Si un seul mot, on le met en prénom
        user.first_name = full_name
        user.last_name = ''
    
    db.session.commit()
    return jsonify(success=True, first_name=user.first_name, last_name=user.last_name)


@gestion_rh_bp.route('/assign_manager', methods=['POST'])
def assign_manager():
    data = request.get_json()
    manager_id = data.get('manager_id')
    assignments = data.get('assignments', [])  # liste de { user_id, role_id }

    if not manager_id or not assignments:
        return jsonify({'error': 'Paramètres manquants'}), 400

    for a in assignments:
        user = User.query.get(a['user_id'])
        if user:
            user.manager_id = manager_id

    db.session.commit()
    return jsonify({'success': True})



@gestion_rh_bp.route('/roles')
def get_all_roles():
    roles = Role.query.order_by(Role.name).all()
    return jsonify([{'id': r.id, 'name': r.name} for r in roles])

@gestion_rh_bp.route('/users_by_roles')
def get_users_by_roles():
    role_ids = request.args.get('roles', '')
    role_ids = [int(rid) for rid in role_ids.split(',') if rid.isdigit()]
    user_roles = UserRole.query.filter(UserRole.role_id.in_(role_ids)).all()

    users_map = {}
    for ur in user_roles:
        user = ur.user
        if user.id not in users_map:
            users_map[user.id] = {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'roles': []
            }
        users_map[user.id]['roles'].append(ur.role.name)

    return jsonify(list(users_map.values()))

@gestion_rh_bp.route('/users_with_roles')
def get_users_with_roles():
    users = User.query.all()
    result = []
    for user in users:
        roles = [ur.role.name for ur in user.user_roles if ur.role is not None]
        if roles:
            result.append({
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'roles': roles
            })
    return jsonify(result)

@gestion_rh_bp.route('/users_with_role')
def get_users_with_role():
    role_name = request.args.get('role')
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        return jsonify([])
    users = db.session.query(User).join(UserRole).filter(UserRole.role_id == role.id).all()
    return jsonify([{'id': u.id, 'first_name': u.first_name, 'last_name': u.last_name} for u in users])