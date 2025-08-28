# routes/propose_savoir_faires.py
from flask import Blueprint, request, jsonify, current_app
import os

bp_propose_sf = Blueprint("propose_savoir_faires", __name__)

PROMPT_HEADER_SAVOIR_FAIRES = """
Analyse les informations d’activité ci-dessous et propose uniquement des SAVOIR-FAIRE
concrets et opérationnels, formulés par verbes d’action.

Règles :
- Chaque item commence par un verbe d’action (Utiliser, Maîtriser, Vérifier, Rédiger, Structurer, Appliquer, Contrôler, Analyser, Consolider, Documenter…)
- Précise toujours sur quoi ou avec quoi le savoir-faire s’exerce (procédure, outil, norme, donnée, contrainte, rôle…)
- Les savoir-faire doivent être spécifiques et contextualisés, pas vagues ni génériques.
- Ne répète pas les tâches textuellement, déduis l’apprentissage concret nécessaire.
- Limite la réponse à 3 à 7 items maximum.
- Sortie attendue : liste à puces, une ligne par savoir-faire.
"""

def _build_activity_context(activity_json: dict) -> str:
    # compat: on accepte le JSON tel que renvoyé par /activities/<id>/details
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
    # Utilise l’API OpenAI via la variable d’environnement OPENAI_API_KEY
    from openai import OpenAI
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return None, "Clé OpenAI manquante (OPENAI_API_KEY)."
    return OpenAI(api_key=key), None

@bp_propose_sf.route("/propose_savoir_faires/propose", methods=["POST"])
def propose_savoir_faires():
    try:
        activity = request.get_json(force=True) or {}
        ctx = _build_activity_context(activity)

        client, err = _openai_client()
        if err:
            return jsonify({"error": err}), 500

        prompt = f"""{PROMPT_HEADER_SAVOIR_FAIRES}

=== CONTEXTE ===
{ctx}
"""
        # Appel OpenAI — modèle à adapter si tu as un autre par défaut
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un assistant RH/formation, précis et concis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )
        text = resp.choices[0].message.content.strip()

        # Parse simple: on découpe par lignes commençant par tirets/puces
        lines = [l.strip("-• ").strip() for l in text.splitlines() if l.strip()]
        lines = [l for l in lines if l]  # filtre vides

        return jsonify({"proposals": lines})

    except Exception as e:
        current_app.logger.exception(e)
        return jsonify({"error": str(e)}), 500
