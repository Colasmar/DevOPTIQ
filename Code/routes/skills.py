# Code/routes/skills.py

import os
import openai
from flask import Blueprint, request, jsonify
from Code.extensions import db
from Code.models.models import Competency

skills_bp = Blueprint('skills', __name__, url_prefix='/skills')

@skills_bp.route('/propose', methods=['POST'])
def propose_skills():
    """
    Génère 2 ou 3 propositions de compétences via l'IA, selon la norme NF X50-124.
    Reçoit en JSON les infos de l'activité (name, input_data, output_data, tasks, tools).
    """
    data = request.get_json() or {}
    activity_name = data.get("name", "Activité sans nom")
    input_data_value = data.get("input_data", "")
    output_data_value = data.get("output_data", "")

    # Extraire la liste de tâches
    tasks_data = data.get("tasks", [])
    if tasks_data and isinstance(tasks_data[0], dict):
        tasks_list = [t.get("name", "") for t in tasks_data]
    else:
        tasks_list = tasks_data if isinstance(tasks_data, list) else []
    tasks_str = ", ".join(tasks_list) if tasks_list else ""

    # Extraire la liste d'outils
    tools_data = data.get("tools", [])
    if tools_data and isinstance(tools_data[0], dict):
        tools_list = [t.get("name", "") for t in tools_data]
    else:
        tools_list = tools_data if isinstance(tools_data, list) else []
    tools_str = ", ".join(tools_list) if tools_list else ""

    prompt = f"""
Vous êtes un expert en gestion des compétences selon la norme NF X50-124.
Proposez 2 ou 3 phrases de compétences pour l'activité suivante :

- Nom : {activity_name}
- Données d'entrée : {input_data_value}
- Données de sortie : {output_data_value}
- Tâches : {tasks_str or "Aucune tâche"}
- Outils : {tools_str or "Aucun outil"}

Contraintes :
1) Chaque phrase doit être rédigée en une seule phrase sans utiliser de listes.
2) Ne mentionnez pas l'environnement ni le niveau de performance.
3) Ne listez pas explicitement "Données, Tâches, Outils".
4) Chaque phrase doit commencer par un verbe d'action.
5) Générez exactement 2 ou 3 phrases, chacune sur une nouvelle ligne.
"""

    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        return jsonify({"error": "Clé OpenAI manquante (OPENAI_API_KEY)."}), 500

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Vous êtes un assistant spécialisé en compétences NF X50-124."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=400
        )
        raw_text = response['choices'][0]['message']['content'].strip()
        lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
        return jsonify({"proposals": lines}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@skills_bp.route('/add', methods=['POST'])
def add_competency():
    """
    Ajoute une compétence dans la table 'competencies'.
    JSON attendu : { "activity_id": <int>, "description": <str> }
    """
    data = request.get_json() or {}
    activity_id = data.get("activity_id")
    description = data.get("description", "").strip()
    if not activity_id or not description:
        return jsonify({"error": "activity_id and description are required"}), 400

    comp = Competency(activity_id=activity_id, description=description)
    try:
        db.session.add(comp)
        db.session.commit()
        return jsonify({
            "id": comp.id,
            "activity_id": comp.activity_id,
            "description": comp.description
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@skills_bp.route('/<int:competency_id>', methods=['DELETE'])
def delete_competency(competency_id):
    comp = Competency.query.get(competency_id)
    if not comp:
        return jsonify({"error": "Competency not found"}), 404
    try:
        db.session.delete(comp)
        db.session.commit()
        return jsonify({"message": "Competency deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
