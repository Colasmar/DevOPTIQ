# Code/routes/propose_softskills.py
import json
import re
from flask import Blueprint, request, jsonify, current_app
from .propose_common import (
    build_activity_context,
    openai_client_or_none,
    dummy_from_context,
)

bp_propose_softskills = Blueprint("propose_softskills", __name__)

# --------------------------------------------------------------------
# 🔥 SUPER PROMPT – VERSION OPTIMISÉE POUR GPT, 100% JSON
# --------------------------------------------------------------------
PROMPT_HEADER_HSC = """
Tu es un expert en analyse du travail, en sciences cognitives et en ingénierie des compétences.

🎯 Objectif : Générer 3 à 8 Habiletés Sociocognitives (HSC) pertinentes pour l’activité fournie.

Pour CHAQUE HSC, tu dois générer un objet JSON contenant STRICTEMENT :

{
  "habilete": "<nom court de l'HSC>",
  "niveau": "<1,2,3 ou 4> (texte inclus)",
  "justification": "<1 ou 2 phrases>"
}

📌 Les niveaux doivent être formulés EXACTEMENT ainsi :
- "1 (Aptitude)"
- "2 (Acquisition)"
- "3 (Maîtrise)"
- "4 (Excellence)"

📌 Les HSC doivent appartenir aux catégories officielles :
- Auto-organisation
- Planification
- Traitement de l'information
- Coopération
- Flexibilité mentale
- Arbitrage
- Conceptualisation
- Approche globale
- Adaptation relationnelle

📌 Format IMPÉRATIF :
Tu réponds UNIQUEMENT par un TABLEAU JSON VALIDE :
[
  {"habilete": "...", "niveau": "...", "justification": "..."},
  {...}
]

AUCUN texte avant, AUCUN texte après, AUCUN backtick Markdown.
"""

# --------------------------------------------------------------------
# OUTILS : extraction JSON propre
# --------------------------------------------------------------------
def clean_json_response(text):
    text = re.sub(r'^```(?:json)?\s*', '', text.strip())
    text = re.sub(r'\s*```$', '', text.strip())
    
    start_bracket = text.find('[')
    start_brace = text.find('{')
    
    if start_bracket == -1 and start_brace == -1:
        return text
    
    if start_bracket == -1:
        start = start_brace
    elif start_brace == -1:
        start = start_bracket
    else:
        start = min(start_bracket, start_brace)
    
    if text[start] == '[':
        end = text.rfind(']')
    else:
        end = text.rfind('}')
    
    if end == -1 or end < start:
        return text
    
    return text[start:end+1]


# --------------------------------------------------------------------
# ROUTE PRINCIPALE
# --------------------------------------------------------------------
@bp_propose_softskills.route("/propose_softskills/propose", methods=["POST"])
def propose_softskills():
    """
    Retourne TOUJOURS un tableau JSON d'HSC {habilete, niveau, justification}.
    Gère :
    - Absence de clé API → fallback local simple
    - Réponse OpenAI imparfaite → nettoyage + fallback
    """
    try:
        activity = request.get_json(force=True) or {}
        ctx = build_activity_context(activity)

        client, err = openai_client_or_none()
        if client is None:
            # Fallback sans IA
            base = dummy_from_context(ctx, "hsc")
            proposals = [
                {
                    "habilete": item,
                    "niveau": "2 (Acquisition)",
                    "justification": "Proposition générée sans IA (clé OpenAI absente).",
                }
                for item in base
            ]
            return jsonify({"proposals": proposals, "source": err}), 200

        # --- Construction du prompt IA ---
        prompt = f"""{PROMPT_HEADER_HSC}

=== CONTEXTE DE L'ACTIVITÉ ===
{ctx}
"""

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un assistant RH expert. "
                        "Tu DOIS répondre uniquement en JSON valide. "
                        "Jamais de texte extérieur, jamais de markdown."
                    )
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.15,
        )

        text = resp.choices[0].message.content.strip()
        cleaned_text = clean_json_response(text)

        proposals = []
        parsed_ok = False

        # --- Tentative de parsing JSON ---
        try:
            data = json.loads(cleaned_text)
            if isinstance(data, dict):
                data = [data]

            niveau_map = {
                "1": "1 (Aptitude)",
                "2": "2 (Acquisition)",
                "3": "3 (Maîtrise)",
                "4": "4 (Excellence)"
            }

            for item in data:
                raw_niveau = item.get("niveau", "2")
                if isinstance(raw_niveau, str):
                    num = re.findall(r"\d", raw_niveau)
                    raw_niveau = num[0] if num else "2"
                elif isinstance(raw_niveau, int):
                    raw_niveau = str(raw_niveau)

                level = niveau_map.get(raw_niveau, "2 (Acquisition)")

                proposals.append({
                    "habilete": item.get("habilete", "Habileté"),
                    "niveau": level,
                    "justification": item.get("justification", ""),
                })

            parsed_ok = True

        except Exception as e:
            current_app.logger.warning(f"[HSC JSON FAIL] {e} | TEXT={cleaned_text[:200]}")

        # --- Fallback texte si JSON illisible ---
        if not parsed_ok or not proposals:
            lines = [
                l.strip("-•* ").strip()
                for l in text.splitlines()
                if l.strip() and not l.strip().startswith("```")
            ]
            for line in lines:
                if len(line) > 3:
                    proposals.append({
                        "habilete": line[:100],
                        "niveau": "2 (Acquisition)",
                        "justification": "",
                    })

        # --- Fallback ultime ---
        if not proposals:
            proposals = [
                {
                    "habilete": "Communication professionnelle",
                    "niveau": "2 (Acquisition)",
                    "justification": "Habileté de base requise pour l'activité.",
                }
            ]

        return jsonify({"proposals": proposals}), 200

    except Exception as e:
        current_app.logger.exception(e)
        return jsonify({
            "proposals": [
                {
                    "habilete": "Habileté non déterminée (erreur serveur).",
                    "niveau": "2 (Acquisition)",
                    "justification": "",
                }
            ],
            "error": str(e),
        }), 200
