import os
import json
import openai
from flask import Blueprint, request, jsonify
from Code.models.models import Activities, db

propose_savoirs_bp = Blueprint('propose_savoirs_bp', __name__, url_prefix='/propose_savoirs')


@propose_savoirs_bp.route('/propose', methods=['POST'])  # Modification ici
def propose_savoirs():
    """
    Génère de 5 à 7 propositions de compétences. 
    Si l'IA renvoie tout sur une ligne, on fait un fallback 
    pour découper en 5 à 7 phrases.
    """
    data = request.get_json() or {}
    activity_name = data.get("name", "Activité sans nom")
    input_data_value = data.get("input_data", "")
    output_data = data.get("output_data", "")

    if isinstance(output_data, dict):
        output_data_value = output_data.get("text", "")
    else:
        output_data_value = output_data

    # Prompt pour l'IA
    prompt = f"""

Pour rappel, un savoir comme présenter dans cette application représente des connaissances générique ou nécessaires concernant un ensemnle d'éléments.
Ce n'est pas l'application de cette connaissance, qui s'apparente au savoir-faire, mais bien a la simple connaissance théorique du sujet.
Rédigez entre 5 à 7  propositions de savoirs, 
chacun sur une nouvelle ligne distincte, 
sans puce ni numérotation, 
en commençant par un verbe d'action.

Activité : {activity_name}
Entrées : {input_data_value}
Sorties : {output_data_value}
"""

    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        return jsonify({"error": "Clé DeepAI manquante (OPENAI_API_KEY)."}), 500

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Vous êtes un assistant spécialisé en savoirs."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=600
        )
        raw_text = response['choices'][0]['message']['content'].strip()

        # Séparer les lignes de texte
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