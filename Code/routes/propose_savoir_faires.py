import os
import json
import openai
from flask import Blueprint, request, jsonify

propose_savoir_faires_bp = Blueprint('propose_savoir_faires_bp', __name__)

@propose_savoir_faires_bp.route('/propose_savoir_faires', methods=['POST'])
def propose_savoir_faires():
    """
    Reçoit { "activity_data": {...} } en JSON
    Renvoie { "proposals": [ ... ] } => liste de Savoir-Faire
    Endpoint : POST /propose_savoir_faires
    """
    data = request.get_json() or {}
    activity_data = data.get("activity_data", {})

    prompt = f"""
    Analyse l'activité suivante :
    Nom : {activity_data.get('name')}
    Description : {activity_data.get('description')}
    Tâches : {activity_data.get('tasks')}
    Outils : {activity_data.get('tools')}

    Liste entre 5 et 10 "Savoir-Faire" sous forme de tableau JSON brut :
    ["Savoir-Faire 1", "Savoir-Faire 2", "..."]
    """

    try:
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            return jsonify({"error": "Clé OpenAI manquante (OPENAI_API_KEY)."}), 500

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=800
        )
        raw_text = response.choices[0].message['content'].strip()

        proposals = json.loads(raw_text)
        if not isinstance(proposals, list):
            return jsonify({"error": "L'IA n'a pas renvoyé un tableau JSON.", "raw_text": raw_text}), 500

        return jsonify({"proposals": proposals}), 200

    except Exception as e:
        return jsonify({"error": f"Erreur propose_savoir_faires: {str(e)}"}), 500
