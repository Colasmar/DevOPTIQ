import os, json, openai
from flask import Blueprint, request, jsonify

propose_savoirs_bp = Blueprint('propose_savoirs_bp', __name__, url_prefix='/propose_savoirs')

@propose_savoirs_bp.route('/propose', methods=['POST'])
def propose_savoirs():
    data = request.get_json()
    activity_data = data.get("activity_data", {})

    prompt = f"""
    Analyse l'activité suivante :
    Nom : {activity_data.get('name')}
    Description : {activity_data.get('description')}
    Tâches : {activity_data.get('tasks')}
    Outils : {activity_data.get('tools')}

    Liste de manière précise et pertinente entre 5 et 10 "Savoirs" nécessaires pour réaliser cette activité, sous forme de tableau JSON brut :
    ["Savoir 1", "Savoir 2", "..."]
    """

    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=800
    )

    proposals = json.loads(response.choices[0].message['content'].strip())
    return jsonify({"proposals": proposals}), 200
