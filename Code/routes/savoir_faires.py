# Code/routes/savoir_faires.py

from flask import Blueprint, request, jsonify, render_template
from Code.extensions import db
from Code.models.models import Activities, SavoirFaire

savoir_faires_bp = Blueprint('savoir_faires_bp', __name__, url_prefix='/savoir_faires')

@savoir_faires_bp.route('/<int:activity_id>/add', methods=['POST'])
def add_savoir_faire(activity_id):
    data = request.get_json() or {}
    desc = data.get("description", "").strip()
    if not desc:
        return jsonify({"error": "description is required"}), 400

    activity = Activities.query.get(activity_id)
    if not activity:
        return jsonify({"error": "Activity not found"}), 404

    try:
        new_sf = SavoirFaire(description=desc, activity_id=activity_id)
        db.session.add(new_sf)
        db.session.commit()
        return jsonify({
            "id": new_sf.id,
            "description": new_sf.description
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@savoir_faires_bp.route('/<int:activity_id>/<int:sf_id>', methods=['PUT'])
def update_savoir_faire(activity_id, sf_id):
    data = request.get_json() or {}
    new_desc = data.get("description", "").strip()
    if not new_desc:
        return jsonify({"error": "description is required"}), 400

    sf_obj = SavoirFaire.query.filter_by(id=sf_id, activity_id=activity_id).first()
    if not sf_obj:
        return jsonify({"error": "SavoirFaire not found"}), 404

    try:
        sf_obj.description = new_desc
        db.session.commit()
        return jsonify({
            "id": sf_obj.id,
            "description": sf_obj.description
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@savoir_faires_bp.route('/<int:activity_id>/<int:sf_id>', methods=['DELETE'])
def delete_savoir_faire(activity_id, sf_id):
    sf_obj = SavoirFaire.query.filter_by(id=sf_id, activity_id=activity_id).first()
    if not sf_obj:
        return jsonify({"error": "SavoirFaire not found"}), 404

    try:
        db.session.delete(sf_obj)
        db.session.commit()
        return jsonify({"message": "SavoirFaire deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@savoir_faires_bp.route('/<int:activity_id>/render', methods=['GET'])
def render_savoir_faires(activity_id):
    activity = Activities.query.get(activity_id)
    if not activity:
        return jsonify({"error": "Activité non trouvée"}), 404
    return render_template('activity_savoir_faires.html', activity=activity)
