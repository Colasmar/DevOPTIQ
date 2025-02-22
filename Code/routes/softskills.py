# Code/routes/softskills.py

import os
import openai
import json
from flask import Blueprint, request, jsonify, current_app
from Code.extensions import db
from Code.models.models import Softskill

softskills_bp = Blueprint('softskills_bp', __name__, url_prefix='/softskills')

@softskills_bp.route('/propose', methods=['POST'])
def propose_softskills():
    """
    Gère la proposition de 3 à 4 habiletés socio-cognitives selon la norme X50-766,
    renvoyées en format JSON (habilete, niveau).
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Aucune donnée reçue"}), 400
    
    activity_info = data.get("activity", "")
    competencies_info = data.get("competencies", "")

    x50_766_hsc = """
Les habiletés socio-cognitives officielles de la norme X50-766 sont :
Relation à soi :
 - Auto-évaluation
 - Auto-régulation
 - Auto-organisation
 - Auto-mobilisation
Relation à l’autre :
 - Sensibilité sociale
 - Adaptation relationnelle
 - Coopération
Relation à l’action :
 - Raisonnement logique
 - Planification
 - Arbitrage
Relation au savoir :
 - Traitement de l’information
 - Synthèse
 - Conceptualisation
Relation à la complexité :
 - Flexibilité mentale
 - Projection
 - Approche globale
"""
    prompt = f"""
Voici une activité avec ses compétences existantes :

Activité : {activity_info}
Compétences existantes : {competencies_info}

Propose 3 ou 4 habiletés socio-cognitives (norme X50-766) jugées essentielles pour cette activité.
Pour chaque habileté, indique un niveau parmi (1=Aptitude, 2=Acquisition, 3=Maîtrise, 4=Excellence).
Réponds au format JSON, par exemple :
[
  {{"habilete": "Auto-évaluation", "niveau": "2"}},
  {{"habilete": "Planification", "niveau": "3"}}
]
"""

    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        return jsonify({"error": "Clé OpenAI manquante (OPENAI_API_KEY)."}), 500

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu es un expert en habiletés socio-cognitives X50-766."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=400
        )
        ai_message = response.choices[0].message['content'].strip()
        proposals = json.loads(ai_message)
        return jsonify(proposals)
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la récupération des habiletés socio-cognitives : {str(e)}"}), 500

@softskills_bp.route('/add', methods=['POST'])
def add_softskill():
    """
    Enregistre une softskill (HSC) dans la table 'softskills'.
    JSON attendu : { "activity_id": <int>, "habilete": <str>, "niveau": <str> }
    """
    data = request.get_json() or {}
    activity_id = data.get("activity_id")
    habilete = data.get("habilete", "").strip()
    niveau = data.get("niveau", "").strip()
    if not activity_id or not habilete or not niveau:
        return jsonify({"error": "activity_id, habilete and niveau are required"}), 400

    new_softskill = Softskill(activity_id=activity_id, habilete=habilete, niveau=niveau)
    try:
        db.session.add(new_softskill)
        db.session.commit()
        return jsonify({
            "id": new_softskill.id,
            "activity_id": new_softskill.activity_id,
            "habilete": new_softskill.habilete,
            "niveau": new_softskill.niveau
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@softskills_bp.route('/translate', methods=['POST'])
def translate_softskills():
    """
    Reçoit un texte libre (user_input) et renvoie une liste d'HSC
    sous forme JSON (habilete, niveau).
    """
    data = request.get_json() or {}
    user_input = data.get("user_input", "").strip()
    if not user_input:
        return jsonify({"error": "Aucune donnée reçue pour la traduction."}), 400

    x50_766_hsc = """
Les habiletés socio-cognitives officielles de la norme X50-766 sont :
Relation à soi :
 - Auto-évaluation
 - Auto-régulation
 - Auto-organisation
 - Auto-mobilisation
Relation à l’autre :
 - Sensibilité sociale
 - Adaptation relationnelle
 - Coopération
Relation à l’action :
 - Raisonnement logique
 - Planification
 - Arbitrage
Relation au savoir :
 - Traitement de l’information
 - Synthèse
 - Conceptualisation
Relation à la complexité :
 - Flexibilité mentale
 - Projection
 - Approche globale
"""
    prompt = f"""
Voici un texte libre décrivant des soft skills :
"{user_input}"

Traduisez ce texte en une liste d'habiletés socio-cognitives issues de la norme X50-766,
et attribuez à chacune un niveau (1=Aptitude, 2=Acquisition, 3=Maîtrise, 4=Excellence).
Répondez au format JSON, par exemple :
[
  {{"habilete": "Auto-évaluation", "niveau": "2"}},
  {{"habilete": "Planification", "niveau": "3"}}
]
N'utilisez que les habiletés ci-dessous :
{x50_766_hsc}
"""

    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        return jsonify({"error": "Clé OpenAI manquante (OPENAI_API_KEY)."}), 500

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu es un expert en habiletés socio-cognitives selon la norme X50-766."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=400
        )
        ai_message = response.choices[0].message['content'].strip()
        proposals = json.loads(ai_message)
        return jsonify({"proposals": proposals})
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la traduction des softskills : {str(e)}"}), 500
