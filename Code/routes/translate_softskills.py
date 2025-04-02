import os
import json
import re
import openai
from flask import Blueprint, request, jsonify

translate_softskills_bp = Blueprint('translate_softskills_bp', __name__, url_prefix='/translate_softskills')

@translate_softskills_bp.route('/translate', methods=['POST'])
def translate_softskills():
    data = request.get_json() or {}
    user_input = data.get("user_input", "").strip()
    activity_data = data.get("activity_data", {})

    if not user_input:
        return jsonify({"error": "Données insuffisantes pour la traduction."}), 400

    # On n'utilise pas forcément activity_data ici, selon besoin
    prompt = f"""
Tu es expert en habiletés socio-cognitives (HSC).

Qualités proposées par l'utilisateur : {user_input}

Retourne 3 à 5 HSC au format JSON (liste). 
EXEMPLE d'objet :
{{
  "habilete": "Planification",
  "niveau": "2 (Acquisition)",
  "justification": "Explique comment ça couvre la qualité {user_input} ..."
}}

Donne UNIQUEMENT le tableau JSON, pas de texte avant/après.
"""
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        return jsonify({"error": "Clé OpenAI manquante."}), 500

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Assistant spécialisé en habiletés socio-cognitives."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=800
        )
        ai_response = response.choices[0].message['content'].strip()
        # On tente de parser en JSON
        proposals = json.loads(ai_response)  # doit être un tableau
        return jsonify({"proposals": proposals}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
