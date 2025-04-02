import os
import json
import openai
from flask import Blueprint, request, jsonify

translate_softskills_bp = Blueprint('translate_softskills_bp', __name__, url_prefix='/translate_softskills')

@translate_softskills_bp.route('/translate', methods=['POST'])
def translate_softskills():
    """
    Reçoit { user_input: "...", activity_data: { ... } },
    et renvoie { "proposals": [...] } : un tableau de 3..5 HSC JSON
    extraites EXCLUSIVEMENT de la liste X50-766.
    """
    data = request.get_json() or {}
    user_input = data.get("user_input", "").strip()
    activity_data = data.get("activity_data", {})

    if not user_input:
        return jsonify({"error": "Aucun texte saisi pour la traduction."}), 400

    # Extraire divers champs depuis activity_data
    activity_name = activity_data.get("name", "Activité sans nom")
    tasks_list = activity_data.get("tasks", [])
    constraints_list = activity_data.get("constraints", [])
    outgoing_list = activity_data.get("outgoing", [])

    # Construire T1, T2..., etc.
    def make_enumeration(prefix, items):
        lines = []
        for i, it in enumerate(items, start=1):
            if isinstance(it, dict):
                desc = it.get("description", "")
                lines.append(f"{prefix}{i}: {desc}")
            else:
                lines.append(f"{prefix}{i}: {it}")
        return "\n".join(lines) if lines else f"(Aucune {prefix.strip()})"

    tasks_text = make_enumeration("T", tasks_list)
    constraints_text = make_enumeration("C", constraints_list)
    # Pour les performances
    perf_lines = []
    perf_idx = 1
    for o in outgoing_list:
        perf = o.get("performance")
        if perf:
            name = perf.get("name", "")
            desc = perf.get("description", "")
            perf_lines.append(f"P{perf_idx}: {name} - {desc}")
            perf_idx += 1
    perf_text = "\n".join(perf_lines) if perf_lines else "(Aucune performance)"

    # Liste X50-766
    x50_766_hsc = """
Liste officielle X50-766 :
- Auto-évaluation
- Auto-régulation
- Auto-organisation
- Auto-mobilisation
- Sensibilité sociale
- Adaptation relationnelle
- Coopération
- Raisonnement logique
- Planification
- Arbitrage
- Traitement de l’information
- Synthèse
- Conceptualisation
- Flexibilité mentale
- Projection
- Approche globale
"""

    # Prompt IA, en insistant pour n'utiliser QUE la liste X50-766
    prompt = f"""
Tu es un expert en habiletés socio-cognitives, norme X50-766.
L'utilisateur a saisi : "{user_input}".

Activité : {activity_name}

Tâches :
{tasks_text}

Contraintes :
{constraints_text}

Performances :
{perf_text}

Voici la liste COMPLETE des habiletés X50-766 (n'utilise QUE ces termes) :
{x50_766_hsc}

Exigences :
1) Génère 3..5 habiletés, sous forme d'un tableau JSON brut (pas de texte hors JSON).
2) Chaque entrée = {{
    "habilete": <str parmi la liste ci-dessus>,
    "niveau": "X (Label)",  (ex: "2 (Acquisition)")
    "justification": "..."
}}
3) "justification" doit mentionner explicitement "{user_input}" et faire référence aux T(i), C(i) ou P(i) si pertinent.
4) N'UTILISE PAS d'autres habiletés que celles de la liste X50-766.
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
            temperature=0.4,
            max_tokens=1200
        )
        ai_text = response.choices[0].message['content'].strip()

        # On parse le JSON renvoyé
        proposals = json.loads(ai_text)
        if not isinstance(proposals, list):
            return jsonify({"error": "Le JSON renvoyé n'est pas un tableau d'objets."}), 400

        # On renvoie le tout
        return jsonify({"proposals": proposals}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
