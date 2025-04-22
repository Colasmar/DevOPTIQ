import os
import json
import openai
from flask import Blueprint, request, jsonify

propose_aptitudes_bp = Blueprint('propose_aptitudes_bp', __name__, url_prefix='/propose_aptitudes')

@propose_aptitudes_bp.route('/propose', methods=['POST'])
def propose_aptitudes():
    """
    Reçoit { "activity_data": {...} } en JSON
    Renvoie { "proposals": [ ... ] } => liste de Aptitudes
    Endpoint : POST /propose_aptitudes
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

une aptitude est d'abord inée en termes physique et intellectuel, certaines aptitudes peuvent se développer (avec des exercices), d'autres peuvent régrésser(ex: maladie, age important), lorsque certaines aptitudes sont dégradées par rapport au standard on les appellent des handicaps. 
En te basant sur la taxonomie classique des handicaps visibles et invisibles, en analysant les tâches de l'activités et leurs contexte et en prenant en compte ta connaissance du monde du travail et des conditions de travail en général propose nous en commençant par le mot limite suivit de la contrainte en termes d'aptitude qui empêcherait de tenir l'activité et par recommander suivi des types de handicaps visibles ou invisibles qui pourraient renforcer la performance de l'activité.

Rédigez entre 5 à 7  propositions d'aptitudes', 
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
                {"role": "system", "content": "Vous êtes un assistant spécialisé en aptitudes."},
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
    



        