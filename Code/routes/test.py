# Code/routes/competences.py

from flask import Blueprint, jsonify, session, render_template, request
from Code.extensions import db
from Code.models.models import Competency, Role, Activities, User, UserRole  # Assure-toi que UserRole est bien importé

competences_bp = Blueprint('competences_bp', __name__, url_prefix='/competences')

@competences_bp.route('/view', methods=['GET'])
def competences_view():
    return render_template('competences_view.html')

@competences_bp.route('/managers', methods=['GET'])
def get_managers():
    try:
        # Récupérer le rôle "Manager"
        role_manager = Role.query.filter_by(name='manager').first()
        if not role_manager:
            return jsonify([])

        # Récupérer tous les utilisateurs liés à ce rôle
        managers = User.query.join(UserRole).filter(UserRole.role_id == role_manager.id).all()

        manager_data = [{'id': manager.id, 'name': f"{manager.first_name} {manager.last_name}"} for manager in managers]
        return jsonify(manager_data)
    except Exception as e:
        import traceback
        traceback.print_exc()  # Pour voir l'erreur dans la console serveur
        return jsonify({'error': str(e)}), 500

@competences_bp.route('/collaborators', methods=['GET'])
def get_collaborators():
    try:
        # Récupérer l'id du rôle "manager"
        role_manager = Role.query.filter_by(name='manager').first()
        if not role_manager:
            return jsonify([])

        # Récupérer tous les user_id qui ont le rôle "manager"
        manager_user_ids = db.session.query(UserRole.user_id).filter_by(role_id=role_manager.id).all()
        manager_user_ids = [uid for (uid,) in manager_user_ids]

        # Récupérer tous les utilisateurs qui sont liés à ces managers (si vous avez une relation directe)
        # Sinon, vous pouvez aussi faire une requête pour tous les utilisateurs liés à ces managers
        # ici, on suppose que le lien entre managers et collaborateurs est dans user_roles
        collaborators = (
            User.query
            .join(UserRole, User.id == UserRole.user_id)
            .filter(UserRole.role_id != role_manager.id)  # Exclure les managers eux-mêmes si besoin
            .filter(UserRole.user_id.in_(manager_user_ids))
            .all()
        )

        collaborator_data = [{'id': c.id, 'first_name': c.first_name, 'last_name': c.last_name} for c in collaborators]
        return jsonify(collaborator_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@competences_bp.route('/all_users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    user_data = [{'id': user.id, 'name': f"{user.first_name} {user.last_name}"} for user in users]
    return jsonify(user_data)

@competences_bp.route('/add_collaborator', methods=['POST'])
def add_collaborator():
    data = request.json
    manager_id = data.get('manager_id')
    user_id = data.get('user_id')
    role_id = data.get('role_id')

    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'Utilisateur introuvable'}), 404

    # Associer le collaborateur au manager
    user.manager_id = manager_id

    # Changer son rôle si besoin
    user.role_id = role_id

    db.session.commit()

    return jsonify({'success': True})
