from flask import Blueprint, jsonify, request
from Code.extensions import db
from Code.models.models import Activities

# Définir le blueprint pour les activités
activities_bp = Blueprint('activities', __name__, url_prefix='/activities')

@activities_bp.route('/', methods=['GET'])
def get_activities():
    """Récupère toutes les activités depuis la base de données."""
    try:
        activities = Activities.query.all()
        return jsonify([
            {"id": activity.id, "name": activity.name, "description": activity.description}
            for activity in activities
        ]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@activities_bp.route('/', methods=['POST'])
def create_activity():
    """Crée une nouvelle activité dans la base de données."""
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Invalid input. 'name' is required."}), 400

    try:
        new_activity = Activities(name=data['name'], description=data.get('description'))
        db.session.add(new_activity)
        db.session.commit()
        return jsonify({
            "id": new_activity.id,
            "name": new_activity.name,
            "description": new_activity.description
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
