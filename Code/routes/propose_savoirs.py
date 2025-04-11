# Code/routes/propose_savoirs.py
import os
import json
import openai
from flask import Blueprint, request, jsonify
from Code.models.models import db

propose_savoirs_bp = Blueprint('propose_savoirs_bp', __name__, url_prefix='/propose_savoirs')

@propose_savoirs_bp.route('/propose', methods=['POST'])
def propose():
    """
    Reçoit { "activity_data": {...} } en JSON
    Renvoie { "proposals": [...] } => liste de Savoirs
    """
    data = request.get_json() or {}
    activity_data = data.get("activity_data", {})

    # Extraction (optionnel)
    safe_name = activity_data.get("name") or "Activité sans nom"
    safe_desc = activity_data.get("description") or "Aucune description"
    tasks = activity_data.get("tasks", [])
    tools = activity_data.get("tools", [])

    prompt = f"""
IMPORTANT : Réponds EXCLUSIVEMENT par un tableau JSON brut (pas de texte avant/après).
Exemple : ["Savoir 1","Savoir 2","Savoir 3"]

Analyse l'activité suivante :
Nom : {safe_name}
Description : {safe_desc}
Tâches : {tasks}
Outils : {tools}

Liste entre 5 et 7 Savoirs, au format tableau JSON :
["Savoir 1", "Savoir 2", ...]
    """

    try:
        # Clé OpenAI
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

        # On parse la réponse en JSON
        proposals = json.loads(raw_text)  # => si l'IA n'a pas renvoyé un JSON brut => erreur

        if not isinstance(proposals, list):
            return jsonify({
                "error": "L'IA n'a pas renvoyé un tableau JSON.",
                "raw_text": raw_text
            }), 500

        return jsonify({"proposals": proposals}), 200

    except Exception as e:
        return jsonify({"error": f"Erreur propose_savoirs: {str(e)}"}), 500
