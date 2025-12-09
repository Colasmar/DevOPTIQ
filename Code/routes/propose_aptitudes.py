from flask import Blueprint, request, jsonify, current_app
import re
from .propose_common import build_activity_context, openai_client_or_none, dummy_from_context

bp_propose_aptitudes = Blueprint("propose_aptitudes", __name__)

PROMPT_HEADER_APTITUDES = """
Analyse l’activité ci-dessous et produis UNIQUEMENT deux listes à puces, sans aucun titre ou sous-titre :

- APTITUDES (5 à 10 items) : chaque ligne = "<catégorie> — <libellé> (<intensité>) : <justification courte>"
  Ex: "Cognitives — Attention soutenue (modérée) : nécessaire pour ..."

- INCLUSION (3 à 6 items) : suggestions d’intégration positives et concrètes
  Ex: "Aménagement du poste (support écran ajustable) : limiter la fatigue visuelle."

Aucun texte hors listes, aucun en-tête, aucun numéro.
"""

def _filter_lines(text: str):
    lines = []
    for raw in text.splitlines():
        t = raw.strip()
        if not t:  # vide
            continue
        if t.startswith("#"):  # titres markdown
            continue
        if re.match(r"^\d+[\).\s]", t):  # 1) 2. etc.
            continue
        t = t.lstrip("-• ").strip()
        if t.endswith(":"):  # sous-titres
            continue
        # on garde seulement les phrases informatives
        if len(t) < 3: 
            continue
        lines.append(t)
    return lines

@bp_propose_aptitudes.route("/propose_aptitudes/propose", methods=["POST"])
def propose_aptitudes():
    try:
        activity = request.get_json(force=True) or {}
        ctx = build_activity_context(activity)
        client, err = openai_client_or_none()
        if client is None:
            # fallback court : 3 aptitudes basées sur le contexte
            return jsonify({"proposals": dummy_from_context(ctx, "aptitude"), "source": err}), 200

        prompt = f"""{PROMPT_HEADER_APTITUDES}

=== CONTEXTE ===
{ctx}
"""
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":"Tu es un assistant inclusion & ergonomie du travail, précis et positif."},
                {"role":"user","content":prompt},
            ],
            temperature=0.2,
        )
        text = resp.choices[0].message.content.strip()
        lines = _filter_lines(text)

        # si le modèle a malgré tout renvoyé des blocs, on garde seulement les lignes "proposables"
        if not lines:
            lines = ["Attention soutenue (modérée) : utile pour tenir l'activité.", 
                     "Organisation personnelle (modérée) : prioriser et suivre les étapes.",
                     "Perception visuelle (faible) : lire, vérifier et corriger des données."]

        return jsonify({"proposals": lines}), 200
    except Exception as e:
        current_app.logger.exception(e)
        return jsonify({"proposals": [], "error": str(e)}), 200
