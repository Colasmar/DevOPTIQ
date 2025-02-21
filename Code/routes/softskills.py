from flask import Blueprint, request, jsonify, current_app
import openai
import json

softskills_bp = Blueprint('softskills_bp', __name__, url_prefix='/softskills')

@softskills_bp.route('/propose', methods=['POST'])
def propose_softskills():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Aucune donnée reçue"}), 400
    
    activity_info = data.get("activity", "")
    competencies_info = data.get("competencies", "")

    # Liste officielle des 15 habiletés socio-cognitives selon la norme X50-766
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

    # Explication des niveaux (chapitre 6.2 de la norme X50-766)
    # 1 => "Aptitude", 2 => "Acquisition", 3 => "Maîtrise", 4 => "Excellence"
    prompt = f"""
Analyse les informations suivantes concernant une activité :
{activity_info}

Les compétences déjà définies pour cette activité sont :
{competencies_info}

En te basant sur la norme X50-766 (chapitre 6.2) et sur la liste ci-dessous d'habiletés socio-cognitives,
propose 3 à 4 habiletés essentielles pour bien tenir l'activité. Pour chaque habileté,
indique un niveau (1,2,3 ou 4) selon :
- 1 => "Aptitude"
- 2 => "Acquisition"
- 3 => "Maîtrise"
- 4 => "Excellence"

{x50_766_hsc}

Donne ta réponse au format JSON sous forme d'une liste d'objets :
[
  {{ "habilete": "Nom de l'habileté (choisir uniquement parmi les 15 ci-dessus)", "niveau": "1..4" }},
  ...
]
Respecte strictement ces 4 niveaux (pas de 0 ou 5) et ne propose que des habiletés issues de la liste ci-dessus.
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # ou "gpt-4o" selon votre configuration
            messages=[
                {"role": "system", "content": "Tu es un expert en habiletés socio-cognitives X50-766."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        ai_message = response.choices[0].message['content'].strip()
        proposals = json.loads(ai_message)
        return jsonify(proposals)
    except json.JSONDecodeError:
        current_app.logger.error(f"Réponse IA non valide (JSONDecodeError) : {ai_message}")
        return jsonify({"error": "La réponse de l'IA n'est pas un JSON valide."}), 500
    except Exception as e:
        current_app.logger.error(f"Erreur dans propose_softskills: {str(e)}")
        return jsonify({"error": "Erreur lors de la récupération des habiletés socio-cognitives."}), 500

@softskills_bp.route('/translate', methods=['POST'])
def translate_softskills():
    data = request.get_json()
    if not data or 'user_input' not in data:
        return jsonify({"error": "Aucune donnée reçue pour la traduction."}), 400
    
    user_input = data.get("user_input", "").strip()
    
    # Liste officielle des 15 habiletés socio-cognitives selon la norme X50-766
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

    # Les niveaux autorisés : 1 => "Aptitude", 2 => "Acquisition", 3 => "Maîtrise", 4 => "Excellence"
    prompt = f"""
Voici un texte libre exprimé par un utilisateur décrivant ce qu'il considère comme soft skills :
"{user_input}"

Traduisez ce texte en une liste d'habiletés socio-cognitives parmi la liste suivante (norme X50-766)
et attribuez à chacune un niveau entre 1 et 4, où :
1 = Aptitude,
2 = Acquisition,
3 = Maîtrise,
4 = Excellence.

{x50_766_hsc}

Donnez votre réponse au format JSON sous forme d'une liste d'objets :
[
  {{ "habilete": "Nom de l'habileté", "niveau": "1..4" }},
  ...
]
Ne proposez que des habiletés issues de cette liste.
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu es un expert en habiletés socio-cognitives selon la norme X50-766."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        ai_message = response.choices[0].message['content'].strip()
        proposals = json.loads(ai_message)
        return jsonify(proposals)
    except json.JSONDecodeError:
        current_app.logger.error(f"Réponse IA non valide (JSONDecodeError) dans translate_softskills : {ai_message}")
        return jsonify({"error": "La réponse de l'IA n'est pas un JSON valide."}), 500
    except Exception as e:
        current_app.logger.error(f"Erreur dans translate_softskills: {str(e)}")
        return jsonify({"error": "Erreur lors de la traduction des soft skills."}), 500
