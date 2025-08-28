# routes/propose_savoirs.py
from flask import Blueprint, request, jsonify, current_app
import os

bp_propose_savoirs = Blueprint("propose_savoirs", __name__)

PROMPT_HEADER_SAVOIRS = """
Analyse les informations de l’activité ci-dessous ainsi que la liste des savoir-faire associés.
Propose uniquement des SAVOIRS (connaissances) nécessaires pour tenir l’activité.

Règles :
- Les savoirs sont des connaissances à acquérir (règles, normes, principes, bases techniques, méthodologies, procédures, réglementations, référentiels…). Ne les formule pas comme des verbes d’action.
- Distingue-toi des savoir-faire : n’exprime pas une action, mais la connaissance sous-jacente (ex.: « Règles de nomenclature catalogue », « Procédure interne de transfert », « Principes de faisabilité technique »).
- Appuie-toi sur les éléments de l’activité (contraintes, outils, données, performances, rôles, environnement, risques) ET sur les savoir-faire fournis pour dériver les connaissances nécessaires.
- Complète par des savoirs TRANSVERSES requis par le contexte (SST, RGPD, qualité/traçabilité, sécurité de l’information, environnement, etc.).
- Priorise la précision et la contextualisation : cite normes/référentiels quand ils sont connus/mentionnés.
- 3 à 8 items maximum.
- Sortie attendue : liste à puces, 1 ligne par savoir (formulation nominale, sans verbe d’action).
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

@bp_propose_savoirs.route("/propose_savoirs/propose", methods=["POST"])
def propose_savoirs():
    try:
        payload = request.get_json(force=True) or {}
        activity = dict(payload)
        savoir_faires = payload.get("savoir_faires") or []  # transmis par le frontend fusion

        ctx = _build_activity_context(activity)
        sf_block = "- " + "\n- ".join(savoir_faires) if savoir_faires else "-"

        client, err = _openai_client()
        if err:
            return jsonify({"error": err}), 500

        prompt = f"""{PROMPT_HEADER_SAVOIRS}

=== CONTEXTE ACTIVITÉ ===
{ctx}

=== SAVOIR-FAIRE ASSOCIÉS ===
{sf_block}
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
        lines = [l.strip("-• ").strip() for l in text.splitlines() if l.strip()]
        lines = [l for l in lines if l]

        return jsonify({"proposals": lines})

    except Exception as e:
        current_app.logger.exception(e)
        return jsonify({"error": str(e)}), 500
