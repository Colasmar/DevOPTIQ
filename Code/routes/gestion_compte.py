from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from Code.extensions import db
from Code.models.models import User, Role, UserRole

gestion_compte_bp = Blueprint('gestion_compte', __name__, url_prefix='/comptes')

@gestion_compte_bp.route('/')
def list_users():
    roles = Role.query.all()
    role_users = {
        role.name: User.query.join(UserRole).filter(UserRole.role_id == role.id).all()
        for role in roles
    }
    users = User.query.all()
    # version affiche uniquement les managers avec subordonnées
    #  managers = User.query.filter(User.subordinates.any()).all()

    # version affiche tout les users ayant le role manager
    manager_role = Role.query.filter_by(name="manager").first()
    managers = (
        User.query.join(UserRole)
        .filter(UserRole.role_id == manager_role.id)
        .all()
        if manager_role else []
    )

    return render_template(
        'gestion_compte.html',
        role_users=role_users,
        roles=roles,
        users=users,
        managers=managers
    )

@gestion_compte_bp.route('/create', methods=['POST'])
def create_user():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    age = request.form.get('age')
    email = request.form['email']
    password = request.form['password']  
    role_id = int(request.form['role_id'])
    status = request.form['status']

    user = User(first_name=first_name, last_name=last_name, age=age, email=email, password=password, status=status)
    db.session.add(user)
    db.session.commit()

    user_role = UserRole(user_id=user.id, role_id=role_id)
    db.session.add(user_role)
    db.session.commit()
    
    return redirect(url_for('gestion_compte.list_users'))

@gestion_compte_bp.route('/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    User.query.filter_by(id=user_id).delete()
    db.session.commit()
    return redirect(url_for('gestion_compte.list_users'))



@gestion_compte_bp.route('/update/<int:user_id>', methods=['GET', 'POST'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    roles = Role.query.all()

    if request.method == 'POST':
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.age = request.form.get('age')
        user.email = request.form['email']
        user.status = request.form['status']

        # Mise à jour du rôle
        new_role_id = int(request.form['role_id'])
        user_role = UserRole.query.filter_by(user_id=user.id).first()
        if user_role:
            user_role.role_id = new_role_id
        else:
            db.session.add(UserRole(user_id=user.id, role_id=new_role_id))

        db.session.commit()
        return redirect(url_for('gestion_compte.list_users'))

    current_role = UserRole.query.filter_by(user_id=user.id).first()
    return render_template('edit_user.html', user=user, roles=roles, current_role=current_role)

@gestion_compte_bp.route('/managers')
def get_managers():
    managers = User.query.filter(User.subordinates.any()).all()
    return jsonify([
        {
            "id": m.id,
            "name": f"{m.first_name} {m.last_name}",
            "subordinates": [
                {"id": s.id, "name": f"{s.first_name} {s.last_name}"}
                for s in m.subordinates
            ]
        }
        for m in managers
    ])

@gestion_compte_bp.route('/assign_manager', methods=['POST'])
def assign_manager():
    manager_id = int(request.form['manager_id'])
    multi = request.form.get('multi_select', '0') == '1'

    if multi:
        user_ids = request.form.getlist('user_ids[]')
        for user_id in user_ids:
            user = User.query.get(int(user_id))
            if user:
                user.manager_id = manager_id
    else:
        user_id = request.form.get('user_id')
        if user_id:
            user = User.query.get(int(user_id))
            if user:
                user.manager_id = manager_id


    db.session.commit()

    # Récupérer la nouvelle liste des subordonnés
    subordinates = User.query.filter_by(manager_id=manager_id).all()
    # Retourner en JSON
    return jsonify({
        'status': 'success',
        'subordinates': [
            {'id': s.id, 'name': f"{s.first_name} {s.last_name}"}
            for s in subordinates
        ]
    })


@gestion_compte_bp.route('/remove_collaborator/<int:user_id>', methods=['POST'])
def remove_collaborator(user_id):
    user = User.query.get(user_id)
    if user:
        user.manager_id = None
        db.session.commit()
    return redirect(url_for('gestion_compte.list_users'))

@gestion_compte_bp.route('/users')
def get_all_users():
    users = User.query.all()
    return jsonify([
        {'id': u.id, 'name': f"{u.first_name} {u.last_name}"}
        for u in users
    ])

@gestion_compte_bp.route('/manager/<int:manager_id>/subordinates')
def get_subordinates(manager_id):
    manager = User.query.get_or_404(manager_id)
    subordinates = manager.subordinates  
    return jsonify({
        'subordinates': [
            {'id': s.id, 'name': f"{s.first_name} {s.last_name}"}
            for s in subordinates
        ]
    })

