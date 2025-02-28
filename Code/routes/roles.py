# Code/routes/roles.py

from flask import Blueprint, request, jsonify
from sqlalchemy import text
from Code.extensions import db
from Code.models.models import Role

roles_bp = Blueprint('roles', __name__, url_prefix='/roles')

@roles_bp.route('/list', methods=['GET'])
def list_roles():
    """
    Retourne la liste de tous les rôles, triés par ordre alphabétique.
    """
    roles = Role.query.order_by(Role.name).all()
    data = [{"id": r.id, "name": r.name} for r in roles]
    return jsonify(data), 200

@roles_bp.route('/garant/activity/<int:activity_id>', methods=['POST'])
def set_garant_role(activity_id):
    """
    Affecte un rôle Garant à une activité.
    JSON attendu : { "role_name": "<str>" }
    - Si le rôle n'existe pas, on le crée
    - On supprime l'ancien Garant (s'il existe)
    - On insère le nouveau (status='Garant')
    """
    data = request.get_json() or {}
    role_name = data.get("role_name", "").strip()
    if not role_name:
        return jsonify({"error": "role_name is required"}), 400

    # Vérifier si le rôle existe déjà
    existing = Role.query.filter_by(name=role_name).first()
    if not existing:
        existing = Role(name=role_name)
        db.session.add(existing)
        db.session.commit()

    # Supprimer l'ancien Garant
    db.session.execute(
        text("DELETE FROM activity_roles WHERE activity_id=:aid AND status='Garant'"),
        {"aid": activity_id}
    )
    # Ajouter le nouveau
    db.session.execute(
        text("INSERT INTO activity_roles (activity_id, role_id, status) VALUES (:aid, :rid, 'Garant')"),
        {"aid": activity_id, "rid": existing.id}
    )
    db.session.commit()

    return jsonify({
        "message": f"Rôle Garant '{existing.name}' assigné à l'activité {activity_id}",
        "role": {"id": existing.id, "name": existing.name}
    }), 200
