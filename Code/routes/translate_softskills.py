import os
import json
import openai
from flask import Blueprint, request, jsonify

translate_softskills_bp = Blueprint('translate_softskills_bp', __name__, url_prefix='/translate_softskills')

@translate_softskills_bp.route('/translate', methods=['POST'])
def translate_softskills():
    data = request.get_json() or {}
    user_input = data.get("user_input", "").strip()
    activity_data = data.get("activity_data", {})

    if not user_input or not activity_data:
        return jsonify({"error": "Données insuffisantes pour la traduction."}), 400

    activity_name = activity_data.get("name", "Activité sans nom")
    tasks = activity_data.get("tasks", [])
    constraints = activity_data.get("constraints", [])
    performances = [o.get("performance") for o in activity_data.get("outgoing", []) if o.get("performance")]

    tasks_text = "\n".join([f"T{i+1}: {task}" for i, task in enumerate(tasks)])
    constraints_text = "\n".join([f"C{i+1}: {constraint.get('description')}" for i, constraint in enumerate(constraints)])
    perf_text = "\n".join([f"P{i+1}: {perf.get('name', '')}" for i, perf in enumerate(performances)])

    prompt = f"""
Tu es expert en habiletés socio-cognitives (HSC).

Qualités proposées par l'utilisateur : {user_input}

Activité concernée : {activity_name}

Tâches :
{tasks_text if tasks else 'Aucune tâche spécifiée'}

Contraintes :
{constraints_text if constraints else 'Aucune contrainte spécifiée'}

Performances :
{perf_text if perf_text else 'Aucune performance précisée'}

Liste officielle X50-766 des HSC :
Relation à soi : Auto-évaluation, Auto-régulation, Auto-organisation, Auto-mobilisation
Relation à l’autre : Sensibilité sociale, Adaptation relationnelle, Coopération
Relation à l’action : Raisonnement logique, Planification, Arbitrage
Relation au savoir : Traitement de l’information, Synthèse, Conceptualisation
Relation à la complexité : Flexibilité mentale, Projection, Approche globale

Pour chaque HSC proposée, indique clairement :
- « habilete » : nom de l'HSC
- « niveau » : chiffre (1 à 4) et niveau écrit (acquisition, maîtrise...)
- « justification » : précise explicitement comment l'habileté couvre les qualités («{user_input} ») en lien avec au moins une tâche (T(i)), contrainte (C(i)) ou performance (P(i)).

IMPORTANT :
- N'utilise JAMAIS les mots « compétence » ou « soft skill », uniquement « habileté » ou « qualité ».
- Réponds UNIQUEMENT avec un tableau JSON (3 à 5 objets), sans aucun texte avant ni après.
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
            max_tokens=1200
        )
        ai_response = response.choices[0].message['content'].strip()
        proposals = json.loads(ai_response)
        return jsonify({"proposals": proposals}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
