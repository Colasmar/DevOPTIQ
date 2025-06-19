import os
import json
import openai
from flask import Blueprint, request, jsonify

propose_aptitudes_bp = Blueprint('propose_aptitudes_bp', __name__, url_prefix='/propose_aptitudes')

@propose_aptitudes_bp.route('/propose', methods=['POST'])
def propose_aptitudes():
    """
    Analyse l'activité et génère entre 5 et 7 aptitudes pertinentes
    sous forme de phrases simples, sans numérotation ni puce.
    """
    data = request.get_json() or {}
    activity_name = data.get("name", "Activité sans nom")
    input_data_value = data.get("input_data", "")
    output_data_value = data.get("output_data", "")
    tasks_list = data.get("tasks", [])
    tools_list = data.get("tools", [])
    constraints_list = data.get("constraints", [])
    competencies_list = data.get("competencies", [])
    outgoing_list = data.get("outgoing", [])

    # Construire texte tâches, outils, contraintes, etc.
    tasks_text = "\n".join([f"- {t}" for t in tasks_list]) or "Aucune tâche"
    tools_text = ", ".join(tools_list) or "Aucun outil"
    constraints_text = "\n".join([f"- {c.get('description','')}" for c in constraints_list]) or "Aucune contrainte"
    comps_text = ", ".join([c.get("description", "") for c in competencies_list]) or "Aucune compétence"
    perf_text = "\n".join([
        f"- {o['performance']['name']}: {o['performance'].get('description', '')}"
        for o in outgoing_list if o.get("performance")
    ]) or "Aucune performance"

    prompt = f"""
Tu es un assistant expert en analyse d'activités professionnelles.

À partir des éléments suivants, rédige entre 5 et 7 **aptitudes clés** que la personne doit posséder pour bien réaliser cette activité.
Ne donne que des phrases directes, sans puces ni numérotation. Chaque aptitude doit être une phrase brève, claire, pratique.

Activité : {activity_name}
Entrées : {input_data_value}
Sorties : {output_data_value}

Tâches :
{tasks_text}

Outils :
{tools_text}

Contraintes :
{constraints_text}

Compétences existantes :
{comps_text}

Performances attendues :
{perf_text}
"""

    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        return jsonify({"error": "Clé OpenAI manquante (OPENAI_API_KEY)."}), 500

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu es un assistant spécialisé en analyse d'activité et recrutement par les aptitudes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=800
        )
        raw_text = response['choices'][0]['message']['content'].strip()

        # Nettoyage
        lines = [l.strip("-• \n") for l in raw_text.split("\n") if l.strip()]

        # Fallback si nécessaire
        if len(lines) < 3:
            import re
            fallback = re.split(r'\.\s+', raw_text)
            lines = [s.strip() for s in fallback if s.strip()]

        # Limite max
        if len(lines) > 10:
            lines = lines[:10]

        return jsonify({"proposals": lines}), 200

    except Exception as e:
        return jsonify({"error": f"Erreur lors de la proposition d'aptitudes : {str(e)}"}), 500
