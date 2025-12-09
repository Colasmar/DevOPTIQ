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
    # On se base uniquement sur la liste des HSC du rôle, transmise par le client
    hsc_list = data.get("hsc_list", [])

    # Nouveau prompt amélioré pour se concentrer exclusivement sur les HSC fournies
    prompt = f"""
Vous êtes un expert en développement des habiletés sociocognitives (HSC) et en accompagnement professionnel.
Votre mission est de générer un plan d'onboarding exclusivement axé sur les HSC suivantes : {hsc_list}.
Le plan devra comporter quatre parties distinctes :

1) **Module de formation/entrainement** :
   - Proposez une ou plusieurs formations courtes, chacune durant entre 0,5 et 2 jours, sans dépasser un total de 3 jours.
   - La formation doit porter uniquement sur le développement des HSC listées.
   - Précisez pour chaque formation les objectifs, la durée, la Méthode (en utilisant le terme "Méthode" sans ajouter "enseignement") et des critères d’évaluation objectifs pouvant être mesurés à la fin de la formation et dans les semaines suivantes.

2) **Retour d’Expérience (REX)** :
   - Décrivez une session de REX personnalisée qui s’appuie sur les HSC listées, en expliquant comment animer la session et en donnant des exemples concrets d’analyse des situations vécues pour améliorer ces HSC.

3) **Coaching d’Équipe** :
   - Donnez des conseils précis pour un coaching d’équipe visant à soutenir le développement des HSC du rôle.
   - Concentrez-vous sur des stratégies pour renforcer la coopération, l’auto-organisation et l’adaptation, en lien avec les HSC fournies.

4) **Parcours d’Apprentissage Autonome** :
   - Proposez un parcours d’apprentissage autonome incluant des exemples concrets de contenus de micro-formations en ligne, des exercices pratiques et des quiz, spécifiquement conçus pour développer les HSC listées.

Assurez-vous que le plan se centre uniquement sur les HSC mentionnées dans la liste et n’intègre aucune autre compétence ou soft skill. 
Répondez sous forme de texte structuré avec des titres clairs pour chaque partie.
"""

    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        return jsonify({"error": "Clé OpenAI manquante (OPENAI_API_KEY)."}), 500

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Vous êtes un assistant spécialisé en développement des HSC et en accompagnement professionnel."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=1500
        )
        onboarding_plan = response['choices'][0]['message']['content'].strip()

        # Sauvegarder le plan dans la base
        role.onboarding_plan = onboarding_plan
        db.session.commit()

        return jsonify({
            "message": "Plan d'onboarding généré avec succès",
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
        return jsonify({"error": "Aucun plan d'onboarding généré pour ce rôle."}), 404
    return jsonify({"onboarding_plan": role.onboarding_plan}), 200
