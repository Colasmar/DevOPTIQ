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
    Génère 3 ou 4 habiletés socio-cognitives en se basant sur la norme X50-766.
    Tient compte du contexte détaillé : nom de l'activité, tâches, outils, environnement,
    compétences existantes, etc., afin de suggérer des niveaux plus réalistes.
    
    JSON attendu en entrée :
    {
      "activity": "Nom de l'activité",
      "tasks": "Description des tâches",
      "tools": "Outils utilisés",
      "environment": "Environnement de travail",
      "competencies": "Compétences existantes"
    }
    """
    data = request.get_json() or {}
    activity_info = data.get("activity", "").strip()
    tasks_info = data.get("tasks", "").strip()
    tools_info = data.get("tools", "").strip()
    environment_info = data.get("environment", "").strip()
    competencies_info = data.get("competencies", "").strip()

    if not activity_info and not tasks_info and not tools_info and not environment_info:
        # Au moins un champ de description est souhaité
        return jsonify({"error": "Aucune information sur l'activité ou le contexte n'a été fournie."}), 400

    # Liste officielle X50-766 (extrait) pour référence
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

    # Construction d'un prompt plus contextuel
    prompt = f"""
Vous êtes un expert en habiletés sociocognitives selon la norme X50-766.
Voici des informations détaillées sur une activité et son contexte :

- Nom de l'activité : {activity_info}
- Tâches : {tasks_info}
- Outils : {tools_info}
- Environnement : {environment_info}
- Compétences existantes : {competencies_info}

En tenant compte de ces éléments, propose 3 ou 4 habiletés sociocognitives pertinentes parmi la liste X50-766 ci-dessous, 
en indiquant un niveau entre 1 et 4 (1 = Aptitude, 4 = Excellence).
Le niveau doit être justifié par la difficulté, la complexité, l'autonomie requise, la répétitivité, etc.

{ x50_766_hsc }

Le résultat final doit être un tableau JSON, par exemple :
[
  {{
    "habilete": "Auto-organisation",
    "niveau": "2",
    "justification": "Niveau intermédiaire car..."
  }},
  ...
]

Ne propose pas plus de 4 habiletés. Ne propose pas d'habiletés en dehors de cette liste.
"""

    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        return jsonify({"error": "Clé OpenAI manquante (OPENAI_API_KEY)."}), 500

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu es un assistant spécialisé en habiletés socio-cognitives X50-766."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=800
        )
        raw_text = response['choices'][0]['message']['content'].strip()
        proposals = json.loads(raw_text)
        return jsonify(proposals), 200
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la proposition de HSC : {str(e)}"}), 500

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
    Reçoit un texte libre (user_input) et renvoie une liste d'HSC (3 à 5).
    On applique la même logique d'ajustement des niveaux, en se basant sur X50-766.
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
Voici un texte libre décrivant des soft skills ou un contexte d'activité :
"{user_input}"

Analyse ce texte et propose 3 à 5 habiletés sociocognitives issues de la norme X50-766
en indiquant un niveau de 1 à 4, justifié brièvement (1 = Aptitude, 4 = Excellence).
N'utilise que la liste suivante :
{x50_766_hsc}

Le résultat doit être un tableau JSON, par exemple :
[
  {{
    "habilete": "Auto-organisation",
    "niveau": "2",
    "justification": "Raisons ..."
  }},
  ...
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
                {"role": "system", "content": "Tu es un expert en habiletés sociocognitives X50-766."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=800
        )
        ai_message = response.choices[0].message['content'].strip()
        proposals = json.loads(ai_message)
        return jsonify({"proposals": proposals}), 200
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la traduction des softskills : {str(e)}"}), 500

@softskills_bp.route('/<int:softskill_id>', methods=['PUT'])
def update_softskill(softskill_id):
    """
    Met à jour une softskill existante.
    JSON attendu : { "habilete": <str>, "niveau": <str> }
    """
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
    """
    Supprime une softskill existante.
    Retourne un JSON avec un message de confirmation ou une erreur.
    """
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
