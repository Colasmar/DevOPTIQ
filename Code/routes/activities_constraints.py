from flask import request, jsonify
from Code.extensions import db
from Code.models.models import Constraint, Data
from .activities_bp import activities_bp

@activities_bp.route('/constraints/add', methods=['POST'])
def add_constraint():
    """
    Ajoute une contrainte. JSON: { "activity_id": <int>, "description": "<str>" }
    """
    payload = request.get_json() or {}
    activity_id = payload.get("activity_id")
    desc = payload.get("description","").strip()
    if not activity_id or not desc:
        return jsonify({"error": "activity_id & description are required"}), 400

    new_c = Constraint(activity_id=activity_id, description=desc)
    db.session.add(new_c)
    db.session.commit()
    return jsonify({"message": "Contrainte ajoutée"}), 200

@activities_bp.route('/data/add', methods=['POST'])
def add_data():
    """
    Ajoute un Data. JSON: { "name":"...", "type":"..." }
    """
    payload = request.get_json() or {}
    nm = payload.get("name","").strip()
    ty = payload.get("type","").strip()
    if not nm or not ty:
        return jsonify({"error": "name & type are required"}), 400

    new_d = Data(name=nm, type=ty)
    db.session.add(new_d)
    db.session.commit()
    return jsonify({"message": "Donnée ajoutée"}), 200
