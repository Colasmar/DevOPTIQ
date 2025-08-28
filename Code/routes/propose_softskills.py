# Code/routes/propose_softskills.py
from flask import Blueprint, request, jsonify, current_app
import os

bp_propose_softskills = Blueprint("propose_softskills", __name__)

PROMPT_HEADER_HSC = """
Analyse l’activité (tâches, contraintes, outils, données, performances) et propose 3 à 8
Habiletés Socio-Cognitives (HSC) structurées sous forme d’objets JSON avec :
- habilete: libellé court (ex: "Attention soutenue", "Analyse critique")
- niveau: 1 à 4 (ou un label lisible)
- justification: 1 à 2 phrases sur le lien avec l’activité
Réponds uniquement avec des items (pas de texte hors liste).
"""

def _build_activity_context(activity_json: dict) -> str:
    title = activity_json.get("title") or activity_json.get("name") or ""
    description = activity_json.get("description") or ""
    inputs = activity_json.get("input_data") or []
    outputs = activity_json.get("output_data") or []
    tools = activity_json.get("tools") or activity_json.get("outils") or []
    constraints = activity_json.get("constraints") or []
    tasks = activity_json.get("tasks") or []

    def norm_list(lst):
        if not lst: return "-"
        return "\n".join([f"- {str(x)}" for x in lst])

    return f"""# Activité
Titre: {title}
Description: {description}

# Données d'entrée
{norm_list(inputs)}

# Données de sortie
{norm_list(outputs)}

# Outils
{norm_list(tools)}

# Contraintes
{norm_list(constraints)}

# Tâches
{norm_list(tasks)}
"""

def _openai_client():
    from openai import OpenAI
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return None, "Clé OpenAI manquante (OPENAI_API_KEY)."
    return OpenAI(api_key=key), None

@bp_propose_softskills.route("/propose_softskills/propose", methods=["POST"])
def propose_softskills():
    try:
        activity = request.get_json(force=True) or {}
        ctx = _build_activity_context(activity)

        client, err = _openai_client()
        if err:
            return jsonify({"error": err}), 500

        prompt = f"""{PROMPT_HEADER_HSC}

=== CONTEXTE ===
{ctx}
"""
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un assistant RH/formation, précis et concis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )
        text = resp.choices[0].message.content.strip()

        # Parsing simple : si ton frontend attend un tableau d'objets {habilete, niveau, justification}
        # et que le modèle a renvoyé des puces, tu peux fallback :
        items = []
        for line in [l for l in text.splitlines() if l.strip()]:
            items.append({
                "habilete": line.strip("-• ").strip(),
                "niveau": "2 (Acquisition)",
                "justification": ""
            })

        return jsonify({"proposals": items})

    except Exception as e:
        current_app.logger.exception(e)
        return jsonify({"error": str(e)}), 500
