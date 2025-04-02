# Code/routes/aptitudes.py

from flask import Blueprint, request, jsonify, render_template
from Code.extensions import db
from Code.models.models import Activities, Aptitude

aptitudes_bp = Blueprint('aptitudes_bp', __name__, url_prefix='/aptitudes')

@aptitudes_bp.route('/<int:activity_id>/add', methods=['POST'])
def add_aptitude(activity_id):
    data = request.get_json() or {}
    desc = data.get("description", "").strip()
    if not desc:
        return jsonify({"error": "description is required"}), 400

    activity = Activities.query.get(activity_id)
    if not activity:
        return jsonify({"error": "Activity not found"}), 404

    try:
        new_ap = Aptitude(description=desc, activity_id=activity_id)
        db.session.add(new_ap)
        db.session.commit()
        return jsonify({
            "id": new_ap.id,
            "description": new_ap.description
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@aptitudes_bp.route('/<int:activity_id>/<int:ap_id>', methods=['PUT'])
def update_aptitude(activity_id, ap_id):
    data = request.get_json() or {}
    new_desc = data.get("description", "").strip()
    if not new_desc:
        return jsonify({"error": "description is required"}), 400

    ap_obj = Aptitude.query.filter_by(id=ap_id, activity_id=activity_id).first()
    if not ap_obj:
        return jsonify({"error": "Aptitude not found"}), 404

    try:
        ap_obj.description = new_desc
        db.session.commit()
        return jsonify({
            "id": ap_obj.id,
            "description": ap_obj.description
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@aptitudes_bp.route('/<int:activity_id>/<int:ap_id>', methods=['DELETE'])
def delete_aptitude(activity_id, ap_id):
    ap_obj = Aptitude.query.filter_by(id=ap_id, activity_id=activity_id).first()
    if not ap_obj:
        return jsonify({"error": "Aptitude not found"}), 404

    try:
        db.session.delete(ap_obj)
        db.session.commit()
        return jsonify({"message": "Aptitude deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@aptitudes_bp.route('/<int:activity_id>/render', methods=['GET'])
def render_aptitudes(activity_id):
    activity = Activities.query.get(activity_id)
    if not activity:
        return jsonify({"error": "Activité non trouvée"}), 404
    return render_template('activity_aptitudes.html', activity=activity)
