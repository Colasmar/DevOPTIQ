from flask import Blueprint, request, jsonify
import os
import openai
from Code.extensions import db
from Code.models.models import Role

onboarding_bp = Blueprint('onboarding', __name__, url_prefix='/roles')

@onboarding_bp.route('/<int:role_id>/onboarding/generate', methods=['POST'])
def generate_onboarding(role_id):
    role = Role.query.get(role_id)
    if not role:
        return jsonify({"error": "Role not found"}), 404

    data = request.get_json() or {}
    hsc_list = data.get("hsc_list", [])

    # Prompt pour générer un plan d'onboarding inspiré des diapos PPT
    prompt = f"""
Vous êtes un expert en développement des habiletés sociocognitives (HSC) et en accompagnement professionnel.
Nous avons un rôle nommé "{role.name}" qui nécessite le développement de certaines HSC :
{hsc_list}

En vous inspirant de la structure suivante (cf. diapos 12 à 14 du PPT), proposez un plan d'accompagnement complet :

1) Indiquez clairement les modules de formation ou d'accompagnement, chacun visant une ou plusieurs HSC parmi la liste suivante : {hsc_list}.
2) Pour chaque module, précisez les objectifs, la durée, la méthode (ex: exercice pratique, jeu de rôle, REX, etc.), et comment les HSC concernées sont développées.
3) Organisez votre plan en plusieurs parties distinctes (comme : "Plan de développement des HSC", "Retour d’Expérience (REX)", "Coaching d’Équipe", "Parcours d’Apprentissage Autonome", etc.).
4) Veillez à mentionner explicitement le lien entre chaque partie et les HSC ciblées.

Répondez sous forme de texte structuré, clair et concis.
"""

    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        return jsonify({"error": "Clé OpenAI manquante (OPENAI_API_KEY)."}), 500

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Vous êtes un assistant spécialisé en habiletés sociocognitives et formation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=1200
        )
        onboarding_plan = response['choices'][0]['message']['content'].strip()

        # Sauvegarder le plan dans la base
        role.onboarding_plan = onboarding_plan
        db.session.commit()

        return jsonify({
            "message": "Plan d'on boarding généré avec succès",
            "onboarding_plan": onboarding_plan
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@onboarding_bp.route('/<int:role_id>/onboarding', methods=['GET'])
def get_onboarding(role_id):
    role = Role.query.get(role_id)
    if not role:
        return jsonify({"error": "Role not found"}), 404
    if not role.onboarding_plan:
        return jsonify({"error": "Aucun plan d'on boarding généré pour ce rôle."}), 404
    return jsonify({"onboarding_plan": role.onboarding_plan}), 200

