import os
import json
import re
import openai
from flask import Blueprint, request, jsonify
from Code.extensions import db

translate_softskills_bp = Blueprint('translate_softskills_bp', __name__, url_prefix='/translate_softskills')

@translate_softskills_bp.route('/translate', methods=['POST'])
def translate_softskills():
    """
    Reçoit { user_input: "...", activity_data: { ... } },
    et renvoie { proposals: [...] } : un tableau de 3..5 HSC JSON
    en tenant compte du contexte (tâches, constraints, etc.).
    """
    data = request.get_json() or {}
    user_input = data.get("user_input", "").strip()
    activity_data = data.get("activity_data", {})

    if not user_input:
        return jsonify({"error": "Texte insuffisant pour la traduction."}), 400

    # On récupère divers champs du activity_data
    activity_name = activity_data.get("name", "Activité sans nom")
    tasks = activity_data.get("tasks", [])
    constraints = activity_data.get("constraints", [])
    outgoing = activity_data.get("outgoing", [])
    
    # Mettons les tasks sous forme T1, T2...
    tasks_list = []
    for i, t in enumerate(tasks, start=1):
        tasks_list.append(f"T{i}: {t}")

    # Idem constraints
    constraints_list = []
    for i, c in enumerate(constraints, start=1):
        desc = c.get("description", "")
        constraints_list.append(f"C{i}: {desc}")

    # Performances / outgoing
    perf_list = []
    for i, o in enumerate(outgoing, start=1):
        p = o.get("performance")
        if p:
            name = p.get("name", "")
            desc = p.get("description", "")
            perf_list.append(f"P{i}: {name} - {desc}")

    tasks_text = "\n".join(tasks_list) if tasks_list else "(Aucune tâche)"
    constraints_text = "\n".join(constraints_list) if constraints_list else "(Aucune contrainte)"
    perf_text = "\n".join(perf_list) if perf_list else "(Aucune performance)"

    # Prompt
    prompt = f"""
Tu es un expert en habiletés socio-cognitives (HSC).
L'utilisateur propose : "{user_input}".

Activité concernée : {activity_name}

Tâches :
{tasks_text}

Contraintes :
{constraints_text}

Performances :
{perf_text}

Objectif :
- Générer 3 à 5 habiletés socio-cognitives (au format JSON) 
  chacune sous forme : {{
    "habilete": "...",
    "niveau": "2 (Acquisition)",
    "justification": "..."
  }}
- Dans "justification", il faut faire explicitement référence 
  au user_input ("{user_input}") et éventuellement T(i), C(i), P(i).

Réponds UNIQUEMENT par le tableau JSON, sans texte avant/après.
"""

    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        return jsonify({"error": "Clé OpenAI manquante (OPENAI_API_KEY)."}), 500

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu es un assistant spécialisé en habiletés socio-cognitives."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=1200
        )
        ai_response = response.choices[0].message['content'].strip()
        # On parse le JSON
        proposals = json.loads(ai_response)
        if not isinstance(proposals, list):
            return jsonify({"error": "Le JSON retourné n'est pas un tableau."}), 400

        return jsonify({"proposals": proposals}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
