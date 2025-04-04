import os, json, openai
from flask import Blueprint, request, jsonify

propose_savoir_faires_bp = Blueprint('propose_savoir_faires_bp', __name__, url_prefix='/propose_savoir_faires')

@propose_savoir_faires_bp.route('/propose', methods=['POST'])
def propose_savoir_faires():
    data = request.get_json()
    activity_data = data.get("activity_data", {})

    prompt = f"""
    Analyse l'activité suivante :
    Nom : {activity_data.get('name')}
    Description : {activity_data.get('description')}
    Tâches : {activity_data.get('tasks')}
    Outils : {activity_data.get('tools')}

    Liste entre 5 et 10 propositions pertinentes de "Savoir-Faire" nécessaires pour réaliser cette activité, en tableau JSON brut :
    ["Savoir-Faire 1", "Savoir-Faire 2", "..."]
    """

    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=800
    )

    proposals = json.loads(response.choices[0].message['content'].strip())
    return jsonify({"proposals": proposals}), 200
