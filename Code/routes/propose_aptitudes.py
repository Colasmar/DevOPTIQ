# routes/propose_aptitudes.py
from flask import Blueprint, request, jsonify, current_app
import os

bp_propose_aptitudes = Blueprint("propose_aptitudes", __name__)

PROMPT_HEADER_APTITUDES = """
Analyse l’activité décrite ci-dessous et identifie :
1) Les APTITUDES spécifiques sollicitées par l’ensemble de l’activité (physiques, sensorielles, cognitives, organisationnelles), en précisant si elles sont faibles, modérées ou fortes.
2) Les possibilités d’intégration de personnes en situation de handicap, présentées de façon positive et inclusive, selon 3 niveaux :
   - Intégration facilitée ou apport spécifique (handicaps particulièrement adaptés, pouvant constituer un atout).
   - Intégration possible sans aménagement majeur.
   - Intégration possible avec aménagements simples (outils, organisation, ergonomie…).

Règles :
- Ne cite pas les handicaps à éviter. Reste centré sur les possibilités et apports positifs.
- Les aptitudes doivent être neutres et factuelles (ex.: attention soutenue, mémoire de travail, endurance physique légère).
- Les propositions d’intégration tiennent compte de la capacité à réaliser l’ensemble de l’activité.
- Pour chaque niveau d’intégration, propose 2 à 5 exemples concrets et opérationnels.
- Sois précis et en lien direct avec contraintes, outils, données ou performances.
- Sortie attendue :
   Section A – Aptitudes spécifiques sollicitées
   Section B – Intégration de personnes en situation de handicap (3 niveaux)
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

@bp_propose_aptitudes.route("/propose_aptitudes/propose", methods=["POST"])
def propose_aptitudes():
    try:
        activity = request.get_json(force=True) or {}
        ctx = _build_activity_context(activity)

        client, err = _openai_client()
        if err:
            return jsonify({"error": err}), 500

        prompt = f"""{PROMPT_HEADER_APTITUDES}

=== CONTEXTE ===
{ctx}
"""
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un assistant inclusion & ergonomie du travail, précis et positif."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )
        text = resp.choices[0].message.content.strip()

        # On renvoie tel quel (ton JS affiche dans un modal avec checkboxes)
        # Si besoin, on découpe en lignes pour uniformiser.
        lines = [l.strip("-• ").strip() for l in text.splitlines() if l.strip()]
        return jsonify({"proposals": lines})
    except Exception as e:
        current_app.logger.exception(e)
        return jsonify({"error": str(e)}), 500
