import os
import json
import openai
from flask import Blueprint, request, jsonify
from Code.extensions import db

propose_softskills_bp = Blueprint('propose_softskills_bp', __name__, url_prefix='/propose_softskills')

@propose_softskills_bp.route('/propose', methods=['POST'])
def propose_softskills():
    """
    Analyse l'activité (tâches, outils, constraints, etc.) et renvoie 3..5 HSC
    sous forme d'un tableau JSON d'objets :
      [
        {
          "habilete": "...",
          "niveau": "2 (acquisition)",
          "justification": "..."
        },
        ...
      ]
    """
    data = request.get_json() or {}
    tasks_list = data.get("tasks", [])
    tools_list = data.get("tools", [])
    competencies_list = data.get("competencies", [])
    constraints_list = data.get("constraints", [])
    outgoing_list = data.get("outgoing", [])

    activity_name = data.get("name", "Activité sans nom")
    input_data_value = data.get("input_data", "")
    output_data_value = data.get("output_data", "")

    # Extraire performances depuis outgoing
    performances_list = []
    for o in outgoing_list:
        perf = o.get("performance")
        if perf:
            p_name = perf.get("name", "Performance")
            p_desc = perf.get("description", "")
            performances_list.append(f"{p_name}: {p_desc}")

    # Génération d'étiquettes T(i), C(i), P(i)
    tasks_labels = [f"T{i}: {t}" for i, t in enumerate(tasks_list, start=1)]
    constraints_labels = [f"C{i}: {c.get('description','')}" for i, c in enumerate(constraints_list, start=1)]
    perf_labels = [f"P{i}: {p}" for i, p in enumerate(performances_list, start=1)]

    tasks_text = "\n".join(tasks_labels) if tasks_labels else "Aucune tâche"
    constraints_text = "\n".join(constraints_labels) if constraints_labels else "Aucune contrainte"
    perf_text = "\n".join(perf_labels) if perf_labels else "Aucune performance"
    tools_text = ", ".join(tools_list) if tools_list else "Aucun outil"
    comps_text = ", ".join([c.get("description", "") for c in competencies_list]) or "Aucune compétence"

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

    # Prompt principal : on veut 3..5 objets JSON
    prompt = f"""
IMPORTANT : Réponds EXCLUSIVEMENT par un tableau JSON brut (3 à 5 objets), sans texte avant/après.
Chaque objet doit être au format : {{
  "habilete": <str>,
  "niveau": <str>,
  "justification": <str>
}}

Exemple d'objet (pour "Analyse des retours clients") :
  {{
    "habilete": "Planification",
    "niveau": "2 (acquisition)",
    "justification": "Explique comment cette habileté s'applique à T1 (Analyse retours), C1 (Délai 48h) et P1 (Zéro erreur)."
  }}

Activité : {activity_name}
Données d'entrée : {input_data_value}
Données de sortie : {output_data_value}

Tâches :
{tasks_text}

Contraintes :
{constraints_text}

Performances :
{perf_text}

Outils : {tools_text}
Compétences existantes : {comps_text}

Liste X50-766 :
{x50_766_hsc}

EXIGENCES :
1) Propose un ensemble de 3 à 5 habiletés, en lien avec les informations ci-dessus.
2) Dans "niveau", indique un chiffre (1..4) ET son label entre parenthèses. Ex: "2 (acquisition)"
3) Dans "justification", fais référence explicitement à au moins une tâche (T(i)), une contrainte (C(i)) et une performance (P(i)) quand c'est pertinent.
4) Ne réponds qu'avec un tableau JSON brut (pas de texte hors du JSON).
"""

    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        return jsonify({"error": "Clé OpenAI manquante (OPENAI_API_KEY)."}), 500

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un assistant spécialisé en habiletés socio-cognitives X50-766."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=1200
        )
        ai_message = response.choices[0].message['content'].strip()
        # On parse le JSON renvoyé
        proposals = json.loads(ai_message)  # tableau d'objets

        # On renvoie {"proposals": [ ... ]}
        return jsonify({"proposals": proposals}), 200

    except Exception as e:
        return jsonify({"error": f"Erreur lors de la proposition de HSC : {str(e)}"}), 500
