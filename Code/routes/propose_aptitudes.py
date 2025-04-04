import os, json, openai
from flask import Blueprint, request, jsonify

propose_aptitudes_bp = Blueprint('propose_aptitudes_bp', __name__, url_prefix='/propose_aptitudes')

@propose_aptitudes_bp.route('/propose', methods=['POST'])
def propose_aptitudes():
    data = request.get_json()
    activity_data = data.get("activity_data", {})

    prompt = f"""
    Analyse l'activité suivante :
    Nom : {activity_data.get('name')}
    Description : {activity_data.get('description')}
    Tâches : {activity_data.get('tasks')}
    Outils : {activity_data.get('tools')}

    Liste entre 5 et 10 propositions pertinentes d'"Aptitudes" nécessaires pour réaliser cette activité, en tableau JSON brut :
    ["Aptitude 1", "Aptitude 2", "..."]
    """

    openai.api_key = os.getenv("OPENAI_API_KEY")
    response
