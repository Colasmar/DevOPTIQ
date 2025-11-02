# Code/routes/propose_aptitudes.py
from flask import Blueprint, request, jsonify, current_app
from .propose_common import (
    build_activity_context,
    openai_client_or_none,
    dummy_from_context,
)

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


@bp_propose_aptitudes.route("/propose_aptitudes/propose", methods=["POST"])
def propose_aptitudes():
    """
    Version tolérante :
    - si OPENAI_API_KEY absente → on renvoie un fallback 200 avec quelques aptitudes génériques
      construites à partir de l’activité -> pas de 500 en prod
    - si OpenAI répond → on normalise en liste de lignes
    """
    try:
        activity = request.get_json(force=True) or {}
        ctx = build_activity_context(activity)

        client, err = openai_client_or_none()
        if client is None:
            # ✅ pas de clé ou erreur d'init → fallback
            return (
                jsonify(
                    {
                        "proposals": dummy_from_context(ctx, "aptitude"),
                        "source": err,
                    }
                ),
                200,
            )

        prompt = f"""{PROMPT_HEADER_APTITUDES}

=== CONTEXTE ===
{ctx}
"""
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un assistant inclusion & ergonomie du travail, précis et positif.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        text = resp.choices[0].message.content.strip()

        # On découpe en lignes pour que le JS ait toujours le même format
        lines = [l.strip("-• ").strip() for l in text.splitlines() if l.strip()]
        if not lines:
            lines = ["Aptitudes non déterminées."]

        return jsonify({"proposals": lines}), 200

    except Exception as e:
        current_app.logger.exception(e)
        # même en cas d'erreur on renvoie 200 avec un message,
        # pour ne pas faire planter le front
        return (
            jsonify(
                {
                    "proposals": ["Aptitudes non déterminées (erreur serveur)."],
                    "error": str(e),
                }
            ),
            200,
        )
