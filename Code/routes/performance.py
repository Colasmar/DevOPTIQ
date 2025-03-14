from flask import Blueprint, request, jsonify
from Code.extensions import db
from Code.models.models import Performance

performance_bp = Blueprint('performance', __name__, url_prefix='/performance')

@performance_bp.route('/add', methods=['POST'])
def add_performance():
    """
    Ajoute une performance pour une donnée de sortie.
    JSON attendu : { "data_id": <int>, "name": "<str>", "description": "<str>" (optionnel) }
    """
    data = request.get_json() or {}
    data_id = data.get("data_id")
    name = data.get("name", "").strip()
    description = data.get("description", "").strip()
    
    if not data_id or not name:
        return jsonify({"error": "data_id and name are required"}), 400

    # Vérifier qu'il n'existe pas déjà une performance pour cette donnée
    existing = Performance.query.filter_by(data_id=data_id).first()
    if existing:
        return jsonify({"error": "Performance already exists for this data"}), 400

    new_perf = Performance(name=name, description=description, data_id=data_id)
    db.session.add(new_perf)
    db.session.commit()
    return jsonify({
        "id": new_perf.id,
        "name": new_perf.name,
        "description": new_perf.description,
        "data_id": new_perf.data_id
    }), 201

@performance_bp.route('/<int:perf_id>', methods=['PUT'])
def update_performance(perf_id):
    """
    Modifie une performance existante.
    JSON attendu : { "name": "<str>", "description": "<str>" (optionnel) }
    """
    data = request.get_json() or {}
    new_name = data.get("name", "").strip()
    new_description = data.get("description", "").strip()
    
    if not new_name:
        return jsonify({"error": "name is required"}), 400

    perf = Performance.query.get(perf_id)
    if not perf:
        return jsonify({"error": "Performance not found"}), 404

    perf.name = new_name
    perf.description = new_description
    db.session.commit()
    return jsonify({
        "id": perf.id,
        "name": perf.name,
        "description": perf.description,
        "data_id": perf.data_id
    }), 200

@performance_bp.route('/<int:perf_id>', methods=['DELETE'])
def delete_performance(perf_id):
    """
    Supprime une performance.
    """
    perf = Performance.query.get(perf_id)
    if not perf:
        return jsonify({"error": "Performance not found"}), 404

    db.session.delete(perf)
    db.session.commit()
    return jsonify({"message": "Performance deleted"}), 200
