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

    # Contenu du prompt remplacé par celui du deuxième fichier
    prompt = f"""
Tu es un expert en organisation du travail et en accessibilité inclusive.

À partir de la description suivante d'une activité professionnelle :

{activity_name}

Analyse les points suivants :
1. **Handicaps particulièrement adaptés** : lesquels pourraient apporter une véritable valeur ajoutée à cette activité, et pourquoi ?
2. **Sans aménagement majeur** : cette activité peut-elle être tenue par une personne en situation de handicap sans adaptation spécifique ? Dans quel(s) cas ?
3. **Avec aménagements simples** : si des aménagements légers permettraient de la rendre accessible, lesquels recommandes-tu ?
4. **Contraintes majeures à étudier** : quelles limitations rendent l’activité plus complexe ou bloquante selon certains handicaps ? Et quelles pistes pour lever ces obstacles ?

Donne une réponse **structurée en 4 paragraphes**, en respectant les titres ci-dessus, sans jargon médical, et en te basant uniquement sur les éléments présents dans la description de l’activité.
    """

    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        return jsonify({"error": "Clé DeepAI manquante (OPENAI_API_KEY)."}), 500
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu es un assistant expert en accessibilité et organisation inclusive du travail."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        raw_text = response['choices'][0]['message']['content'].strip()
        lines = [l.strip() for l in raw_text.split("\n") if l.strip()]

        # FALLBACK : si < 3 lignes => tenter un split sur '. '
        if len(lines) < 3:
            import re
            splitted = re.split(r'\.\s+', raw_text)
            splitted = [s.strip() for s in splitted if s.strip()]
            if len(splitted) > len(lines):
                lines = splitted

        # On force lines à 10 maximum si l'IA en renvoie plus
        if len(lines) > 10:
            lines = lines[:10]

        return jsonify({"proposals": lines}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500