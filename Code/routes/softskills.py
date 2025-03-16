import os
import openai
import json
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from Code.extensions import db
from Code.models.models import Softskill

softskills_bp = Blueprint('softskills_bp', __name__, url_prefix='/softskills')

@softskills_bp.route('/propose', methods=['POST'])
def propose_softskills():
    """
    Génère 3 ou 4 habiletés socio-cognitives (X50-766) avec niveau (1..4) et justification,
    basées sur les infos complètes de l'activité (qu'on reçoit en JSON).
    """
    data = request.get_json() or {}

    tasks_list = data.get("tasks", [])
    if not tasks_list or len(tasks_list) == 0:
        return jsonify({"error": "Saisissez d'abord des tâches"}), 400

    activity_name = data.get("name", "Activité sans nom")
    input_data_value = data.get("input_data", "")
    output_data_value = data.get("output_data", "")
    tools = data.get("tools", [])
    competencies = data.get("competencies", [])
    constraints = data.get("constraints", [])
    outgoing = data.get("outgoing", [])

    # Récupérer les performances depuis outgoing => performance
    performances_list = []
    for o in outgoing:
        perf = o.get("performance")
        if perf:
            p_name = perf.get("name", "Performance")
            p_desc = perf.get("description", "")
            performances_list.append(f"{p_name}: {p_desc}")

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

    tasks_str = ", ".join(tasks_list) if tasks_list else "Aucune tâche"
    tools_str = ", ".join(tools) if tools else "Aucun outil"
    comps_str = ", ".join([c.get("description", "") for c in competencies]) or "Aucune compétence"
    constraints_str = ", ".join([c.get("description", "") for c in constraints]) or "Aucune contrainte"
    performances_str = "; ".join(performances_list) or "Aucune performance"

    prompt = f"""
Vous êtes un expert en habiletés socio-cognitives selon la norme X50-766.
Voici les informations sur une activité :

- Nom de l'activité : {activity_name}
- Données d'entrée : {input_data_value}
- Données de sortie : {output_data_value}
- Tâches : {tasks_str}
- Outils : {tools_str}
- Compétences existantes : {comps_str}
- Contraintes/Exigences : {constraints_str}
- Performances visées : {performances_str}

En vous basant sur la liste X50-766 ci-dessous, proposez 3 ou 4 habiletés pertinentes,
avec un niveau (1..4) et une justification succincte qui fait référence aux tâches,
contraintes et performances ci-dessus (citez-les si nécessaire).

{x50_766_hsc}

Répondez sous forme de tableau JSON (3 ou 4 objets).
Ne proposez jamais plus de 4 objets.
"""

    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        return jsonify({"error": "Clé OpenAI manquante (OPENAI_API_KEY)."}), 500

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # ou "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "Tu es un assistant spécialisé en habiletés socio-cognitives X50-766."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1200
        )
        raw_text = response['choices'][0]['message']['content'].strip()
        proposals = json.loads(raw_text)

        return jsonify(proposals), 200
    except Exception as e:
        print("ERREUR dans propose_softskills:", e)
        return jsonify({"error": f"Erreur lors de la proposition de HSC : {str(e)}"}), 500


@softskills_bp.route('/add', methods=['POST'])
def add_softskill():
    """
    Enregistre ou met à jour une softskill (HSC).
    JSON attendu : { "activity_id": <int>, "habilete": <str>, "niveau": <str>, "justification": <str> (optionnel) }
    Compare les niveaux pour éviter d'enregistrer un niveau plus bas que l'existant.
    """
    data = request.get_json() or {}
    activity_id = data.get("activity_id")
    habilete = data.get("habilete", "").strip()
    niveau = data.get("niveau", "").strip()
    justification = data.get("justification", "").strip()

    if not activity_id or not habilete or not niveau:
        return jsonify({"error": "activity_id, habilete and niveau are required"}), 400

    try:
        new_level_int = int(niveau)
    except ValueError:
        new_level_int = 0

    existing = Softskill.query.filter(
        func.lower(Softskill.habilete) == habilete.lower(),
        Softskill.activity_id == activity_id
    ).first()

    try:
        if existing:
            old_level_int = 0
            try:
                old_level_int = int(existing.niveau)
            except ValueError:
                pass

            # Si le nouveau niveau est supérieur, on met à jour
            if new_level_int > old_level_int:
                existing.niveau = str(new_level_int)
                existing.habilete = habilete
                if justification:
                    existing.justification = justification
                db.session.commit()

            return jsonify({
                "id": existing.id,
                "activity_id": existing.activity_id,
                "habilete": existing.habilete,
                "niveau": existing.niveau,
                "justification": existing.justification or ""
            }), 200
        else:
            new_softskill = Softskill(
                activity_id=activity_id,
                habilete=habilete,
                niveau=str(new_level_int),
                justification=justification
            )
            db.session.add(new_softskill)
            db.session.commit()
            return jsonify({
                "id": new_softskill.id,
                "activity_id": new_softskill.activity_id,
                "habilete": new_softskill.habilete,
                "niveau": new_softskill.niveau,
                "justification": new_softskill.justification or ""
            }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@softskills_bp.route('/translate', methods=['POST'])
def translate_softskills():
    """
    Gère plusieurs softskills en langage naturel (user_input) et renvoie
    3..5 habiletés X50-766 (en JSON), avec justification contextualisée :
     - Référence explicite aux softskills du user_input
     - Référence explicite aux tâches (T1..Tn), contraintes (C1..Cn) et performances (P1..Pn)
       pour démontrer en quoi l'habileté contribue concrètement à l'intérêt de l'activité.
    """
    data = request.get_json() or {}
    user_input = data.get("user_input", "").strip()
    activity_data = data.get("activity_data", {})

    if not user_input:
        return jsonify({"error": "Aucune donnée reçue pour la traduction."}), 400

    activity_name = activity_data.get("name", "Activité sans nom")
    input_data_value = activity_data.get("input_data", "")
    output_data_value = activity_data.get("output_data", "")
    tasks_list = activity_data.get("tasks", [])
    tools_list = activity_data.get("tools", [])
    competencies_list = activity_data.get("competencies", [])
    constraints_list = activity_data.get("constraints", [])
    outgoing_list = activity_data.get("outgoing", [])

    # Extraire performances depuis outgoing
    performances_list = []
    for o in outgoing_list:
        perf = o.get("performance")
        if perf:
            p_name = perf.get("name", "Performance")
            p_desc = perf.get("description", "")
            performances_list.append(f"{p_name}: {p_desc}")

    # Génération d'étiquettes T1..Tn, C1..Cn, P1..Pn
    tasks_labels = []
    for i, t in enumerate(tasks_list, start=1):
        tasks_labels.append(f"T{i}: {t}")
    constraints_labels = []
    for i, c in enumerate(constraints_list, start=1):
        desc = c.get("description", "").strip()
        constraints_labels.append(f"C{i}: {desc}")
    perf_labels = []
    for i, p_info in enumerate(performances_list, start=1):
        perf_labels.append(f"P{i}: {p_info}")

    tasks_text = "\n".join(tasks_labels) if tasks_labels else "Aucune tâche"
    constraints_text = "\n".join(constraints_labels) if constraints_labels else "Aucune contrainte"
    perf_text = "\n".join(perf_labels) if perf_labels else "Aucune performance"

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

    # Prompt renforcé avec exemple détaillé
    prompt = f"""
IMPORTANT : Réponds EXCLUSIVEMENT par un tableau JSON brut (3..5 objets), sans texte avant/après.
Chaque objet doit être au format : {{ "habilete": <str>, "niveau": <str>, "justification": <str> }}
Exemple d'objet (pour user_input = "humour, rigueur") :
  {{
    "habilete": "Sensibilité sociale",
    "niveau": "2",
    "justification": "Explique comment cette habileté, en combinant 'humour' et 'rigueur', permet de mieux réaliser T1 (Analyse des retours clients), respecte C1 (Délai de 48h) et contribue à P1 (Zéro erreur)."
  }}

Données réelles :

Soft skills en langage naturel : "{user_input}"

Activité : {activity_name}
Données d'entrée : {input_data_value}
Données de sortie : {output_data_value}

Tâches :
{tasks_text}

Contraintes :
{constraints_text}

Performances :
{perf_text}

Outils : {", ".join(tools_list) if tools_list else "Aucun outil"}
Compétences existantes : {", ".join([c.get("description", "") for c in competencies_list]) or "Aucune"}

Liste X50-766 :
{x50_766_hsc}

EXIGENCES :
1) Propose un ensemble minimal d'HSC (3..5 objets) pour couvrir toutes les soft skills du user_input.
2) Dans chaque justification, indique comment l'habileté répond concrètement aux soft skills du user_input
   ET comment elle s'appuie sur au moins une tâche (T(i)), une contrainte (C(i)) et une performance (P(i)) pour contribuer à l'intérêt de l'activité.
3) Si plusieurs soft skills s'opposent (par exemple, humour vs rigueur), explique comment l'habileté aide à les arbitrer ou les combiner.
4) N'emploie jamais le terme "compétence" : utilise "habileté" ou "capacité".
5) Donne un niveau entre 1 et 4 pour chaque HSC.
6) Réponds uniquement par un tableau JSON (pas de texte hors du JSON), et ne dépasse pas 5 objets.
7) Dans chaque justification, fais au moins une référence explicite aux tâches, contraintes et performances (ex. T1, C1, P1).
8) Explique précisément en quoi l'habileté contribue à l'intérêt global de l'activité en se référant aux informations spécifiques fournies.

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
            max_tokens=1200
        )
        ai_message = response.choices[0].message['content'].strip()

        print("DEBUG /softskills/translate => AI raw output:\n", ai_message)

        proposals = json.loads(ai_message)
        return jsonify({"proposals": proposals}), 200

    except Exception as e:
        print("DEBUG: Erreur parse JSON =>", e)
        return jsonify({"error": f"Erreur lors de la traduction des softskills : {str(e)}"}), 500


@softskills_bp.route('/<int:softskill_id>', methods=['PUT'])
def update_softskill(softskill_id):
    """
    Met à jour une softskill existante.
    JSON attendu : { "habilete": <str>, "niveau": <str>, "justification": <str> (optionnel) }
    """
    data = request.get_json() or {}
    new_habilete = data.get("habilete", "").strip()
    new_niveau = data.get("niveau", "").strip()
    new_justification = data.get("justification", "").strip()

    if not new_habilete or not new_niveau:
        return jsonify({"error": "habilete and niveau are required"}), 400

    ss = Softskill.query.get(softskill_id)
    if not ss:
        return jsonify({"error": "Softskill not found"}), 404

    try:
        ss.habilete = new_habilete
        ss.niveau = new_niveau
        if new_justification:
            ss.justification = new_justification
        db.session.commit()
        return jsonify({
            "id": ss.id,
            "habilete": ss.habilete,
            "niveau": ss.niveau,
            "justification": ss.justification or ""
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@softskills_bp.route('/<int:softskill_id>', methods=['DELETE'])
def delete_softskill(softskill_id):
    """
    Supprime une softskill existante.
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
