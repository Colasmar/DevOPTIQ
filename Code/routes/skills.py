from flask import Blueprint, request, jsonify
import os
import openai
from Code.extensions import db
from Code.models.models import Competency

# Initialisation du blueprint pour les compétences
skills_bp = Blueprint('skills', __name__, url_prefix='/skills')

@skills_bp.route('/propose', methods=['POST'])
def propose_skills():
    """
    Génère exactement 3 propositions de compétences via l'IA (NF X50-124).
    Reçoit en JSON les informations de l'activité, notamment :
      - name, input_data, output_data, tasks, outgoing, tools.
    Les propositions sont basées sur une synthèse des tâches et des connexions sortantes.
    Si aucune tâche n'est renseignée, renvoie un message "Saisissez d'abord des tâches".
    """
    print("DEBUG: /skills/propose route called")

    data = request.get_json() or {}
    activity_name = data.get("name", "Activité sans nom")
    input_data_value = data.get("input_data", "")

    # Gestion du champ output_data : s'il est un dict, extraire le texte principal
    output_data = data.get("output_data", "")
    if isinstance(output_data, dict):
        output_data_value = output_data.get("text", "")
    else:
        output_data_value = output_data

    # Extraction de la liste des tâches en se concentrant sur le nom uniquement
    tasks_data = data.get("tasks", [])
    tasks_list = []
    if tasks_data and isinstance(tasks_data, list):
        for t in tasks_data:
            if isinstance(t, dict):
                tasks_list.append(t.get("name", ""))
            else:
                tasks_list.append(str(t))
    # Si aucune tâche n'est renseignée, renvoyer une erreur
    if not tasks_list or all(not t.strip() for t in tasks_list):
        return jsonify({"error": "Saisissez d'abord des tâches"}), 400
    tasks_str = ", ".join([t.strip() for t in tasks_list if t.strip()])

    # Extraction de la liste des connexions sortantes en se concentrant sur le nom de la cible
    outgoing_data = data.get("outgoing", [])
    outgoing_list = []
    if outgoing_data and isinstance(outgoing_data, list):
        for conn in outgoing_data:
            if isinstance(conn, dict):
                # On privilégie "target_name", sinon "data_name"
                val = conn.get("target_name", conn.get("data_name", "")).strip()
                outgoing_list.append(val)
            else:
                outgoing_list.append(str(conn).strip())
    outgoing_str = ", ".join([x for x in outgoing_list if x]) if outgoing_list else "Aucune connexion sortante"

    # Extraction de la liste des outils en se concentrant sur le nom uniquement
    tools_data = data.get("tools", [])
    tools_list = []
    if tools_data and isinstance(tools_data, list):
        for t in tools_data:
            if isinstance(t, dict):
                tools_list.append(t.get("name", "").strip())
            else:
                tools_list.append(str(t).strip())
    tools_str = ", ".join([t for t in tools_list if t]) if tools_list else "Aucun outil"

    prompt = f"""
Vous êtes un expert en gestion des compétences selon la norme NF X50-124.
Proposez exactement 3 formulations de compétences pour l'activité suivante, sans numéroter ni lister les phrases :

- Nom de l'activité : {activity_name}
- Données d'entrée : {input_data_value}
- Données de sortie : {output_data_value}
- Tâches : {tasks_str}
- Connexions sortantes : {outgoing_str}
- Outils : {tools_str}

Contraintes :
- Chaque phrase doit être rédigée en une seule phrase sans utiliser de listes ni de numérotation.
- Ne mentionnez pas l'environnement ni le niveau de performance.
- Chaque phrase doit commencer par un verbe d'action.
- Générez exactement 3 phrases, chacune sur une nouvelle ligne, sans préfixe du type "1)" ou "2)".
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

@skills_bp.route('/<int:competency_id>', methods=['PUT'])
def update_competency(competency_id):
    """
    Met à jour une compétence existante.
    JSON attendu : { "description": <str> }
    """
    data = request.get_json() or {}
    new_desc = data.get("description", "").strip()
    if not new_desc:
        return jsonify({"error": "description is required"}), 400

    comp = Competency.query.get(competency_id)
    if not comp:
        return jsonify({"error": "Competency not found"}), 404

    try:
        comp.description = new_desc
        db.session.commit()
        return jsonify({
            "id": comp.id,
            "description": comp.description
        }), 200
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
