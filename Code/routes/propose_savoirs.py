from flask import Blueprint, request, jsonify
from Code.models.models import Activities, db

propose_savoirs_bp = Blueprint('propose_savoirs', __name__)

@propose_savoirs_bp.route('/propose_savoirs', methods=['POST'])
def propose_savoirs():
    data = request.get_json()

    activity_id = data.get('activity_id')
    if not activity_id:
        return jsonify({"error": "activity_id manquant dans la requête"}), 400

    activity = Activities.query.get(activity_id)
    if not activity:
        return jsonify({"error": "Activité non trouvée"}), 404

    message = f"Activité concernée : \nNom : {activity.name}\nDescription : {activity.description or 'Aucune description'}"
    return jsonify({"message": message}), 200
