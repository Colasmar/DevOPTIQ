import os
import openai
import json
from flask import Blueprint, request, jsonify
from Code.extensions import db
from Code.models.models import Softskill

softskills_bp = Blueprint('softskills_bp', __name__, url_prefix='/softskills')

@softskills_bp.route('/propose', methods=['POST'])
def propose_softskills():
    """
    Propose 3-4 habiletés socio-cognitives (HSC) via l'IA, renvoyées en JSON.
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

Propose 3 ou 4 habiletés socio-cognitives officielles (norme X50-766) jugées essentielles pour cette activité.
Utilise uniquement la liste suivante (n'invente pas d'autres habiletés) :
{x50_766_hsc}

Pour chaque habileté, indique un niveau entre 1 et 4 (1 = Aptitude, 4 = Excellence).
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
    Reçoit un texte libre (user_input) et renvoie une liste d'HSC.
    Pour limiter la réponse à 3 à 5 HSC, le prompt demande explicitement de ne pas proposer plus de 5 objets.
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

Analyse ce texte dans le contexte de l'activité et des tâches associées, et traduis-le en une liste de 3 à 5 habiletés socio-cognitives issues de la norme X50-766.
Utilise uniquement la liste suivante (n'invente pas d'autres habiletés) :
{x50_766_hsc}

Pour chaque habileté, attribue un niveau entre 1 et 4 (1 = Aptitude, 4 = Excellence).
Réponds au format JSON, par exemple :
[
  {{"habilete": "Auto-évaluation", "niveau": "2"}},
  {{"habilete": "Planification", "niveau": "3"}}
]

Ne propose jamais plus de 5 objets dans le tableau.
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

@softskills_bp.route('/<int:softskill_id>', methods=['PUT'])
def update_softskill(softskill_id):
    data = request.get_json() or {}
    new_habilete = data.get("habilete", "").strip()
    new_niveau = data.get("niveau", "").strip()
    if not new_habilete or not new_niveau:
        return jsonify({"error": "habilete and niveau are required"}), 400

    ss = Softskill.query.get(softskill_id)
    if not ss:
        return jsonify({"error": "Softskill not found"}), 404

    try:
        ss.habilete = new_habilete
        ss.niveau = new_niveau
        db.session.commit()
        return jsonify({
            "id": ss.id,
            "habilete": ss.habilete,
            "niveau": ss.niveau
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@softskills_bp.route('/<int:softskill_id>', methods=['DELETE'])
def delete_softskill(softskill_id):
    ss = Softskill.query.get(softskill_id)
    if not ss:
        return jsonify({"error": "Softskill not found"}), 404
    try:
        db.session.delete(ss)
        db.session.commit()
        return jsonify({"message": "Softskill deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
