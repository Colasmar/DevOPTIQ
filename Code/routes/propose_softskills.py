# Code/routes/propose_softskills.py
from flask import Blueprint, request, jsonify, current_app
from .propose_common import (
    build_activity_context,
    openai_client_or_none,
    dummy_from_context,
)

bp_propose_softskills = Blueprint("propose_softskills", __name__)

PROMPT_HEADER_HSC = """
Analyse l’activité (tâches, contraintes, outils, données, performances) et propose 3 à 8
Habiletés Socio-Cognitives (HSC) structurées sous forme d’objets JSON avec :
- habilete: libellé court (ex: "Attention soutenue", "Analyse critique")
- niveau: 1 à 4 (ou un label lisible)
- justification: 1 à 2 phrases sur le lien avec l’activité
Réponds uniquement avec des items (pas de texte hors liste).
"""


@bp_propose_softskills.route("/propose_softskills/propose", methods=["POST"])
def propose_softskills():
    """
    Version tolérante :
    - si pas de clé OpenAI → on renvoie 3 HSC génériques en fonction de l’activité
    - si OpenAI renvoie juste du texte → on retransforme en tableau d’objets
    -> de cette façon, ton JS a toujours un tableau d’objets {habilete, niveau, justification}
    """
    try:
        activity = request.get_json(force=True) or {}
        ctx = build_activity_context(activity)

        client, err = openai_client_or_none()
        if client is None:
            # ✅ fallback sans IA
            base = dummy_from_context(ctx, "hsc")
            proposals = [
                {
                    "habilete": item,
                    "niveau": "2",
                    "justification": "Proposition générée sans IA (clé OpenAI absente).",
                }
                for item in base
            ]
            return jsonify({"proposals": proposals, "source": err}), 200

        prompt = f"""{PROMPT_HEADER_HSC}

=== CONTEXTE ===
{ctx}
"""

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un assistant RH/formation, précis et concis."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        text = resp.choices[0].message.content.strip()

        # le modèle peut renvoyer soit du vrai JSON, soit une liste à puces
        # => on tente un parse JSON d'abord
        proposals = []
        parsed_ok = False

        # 1) tentative JSON brut
        if text.startswith("[") or text.startswith("{"):
            try:
                import json

                data = json.loads(text)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    proposals.append(
                        {
                            "habilete": item.get("habilete") or item.get("label") or "Habilete",
                            "niveau": str(item.get("niveau") or "2"),
                            "justification": item.get("justification") or "",
                        }
                    )
                parsed_ok = True
            except Exception:
                parsed_ok = False

        # 2) fallback texte → on découpe en lignes
        if not parsed_ok:
            lines = [l.strip("-• ").strip() for l in text.splitlines() if l.strip()]
            for line in lines:
                proposals.append(
                    {
                        "habilete": line,
                        "niveau": "2",
                        "justification": "",
                    }
                )

        if not proposals:
            proposals = [
                {
                    "habilete": "Communication professionnelle",
                    "niveau": "2",
                    "justification": "",
                }
            ]

        return jsonify({"proposals": proposals}), 200

    except Exception as e:
        current_app.logger.exception(e)
        # on ne casse pas le front
        return (
            jsonify(
                {
                    "proposals": [
                        {
                            "habilete": "Habileté non déterminée (erreur serveur).",
                            "niveau": "2",
                            "justification": "",
                        }
                    ],
                    "error": str(e),
                }
            ),
            200,
        )
