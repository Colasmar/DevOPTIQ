import os
import json
import openai
from flask import Blueprint, request, jsonify

propose_savoir_faires_bp = Blueprint('propose_savoir_faires_bp', __name__, url_prefix='/propose_savoir_faires')

@propose_savoir_faires_bp.route('/propose', methods=['POST'])
def propose_savoir_faires():
    """
    Reçoit { "activity_data": {...} } en JSON
    Renvoie { "proposals": [ ... ] } => liste de Savoir-Faires
    Endpoint : POST /propose_savoir_faires
    """
    data = request.get_json() or {}
    activity_name = data.get("name", "Activité sans nom")
    input_data_value = data.get("input_data", "")
    output_data = data.get("output_data", "")

    if isinstance(output_data, dict):
        output_data_value = output_data.get("text", "")
    else:
        output_data_value = output_data


    prompt = f"""
    
Pour rappel, un savoir-faire comme présenter dans cette application représente un savoir faire est une application pratique dans une situation donnée.
exemple : faire un tableau croisé dynamique ou encore réaliser une analyse de bilan comptable. contrairement au savoir qui se défini simplement comme une connaissance purement théorique le savoir faire lui représente la mise en pratique de connaissance donnant lieu a un résultat découlant de l'associasion d'un savoir et d'une expérience ainsi le savoir faire se définit.
Rédigez entre 5 et 10 propositions de savoir-faires
chacun sur une nouvelle ligne distincte, 
sans puce ni numérotation, 
en commençant par un verbe d'action.

Activité : {activity_name}
Entrées : {input_data_value}
Sorties : {output_data_value}
"""

    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        return jsonify({"error": "Clé OpenAI manquante (OPENAI_API_KEY)."}), 500
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
           messages=[
                {"role": "system", "content": "Vous êtes un assistant spécialisé en savoir-faires."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=600
        )
        raw_text = response['choices'][0]['message']['content'].strip()

        lines = [l.strip() for l in raw_text.split("\n") if l.strip()]

        # FALLBACK : si < 3 lignes => tenter un split sur '. '
        if len(lines) < 3:
            splitted = re.split(r'\.\s+', raw_text)
            splitted = [s.strip() for s in splitted if s.strip()]
            if len(splitted) > len(lines):
                lines = splitted

        # On force lines à 3 maximum si l'IA en renvoie plus
        if len(lines) > 10:
            lines = lines[:10]

        return jsonify({"proposals": lines}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500