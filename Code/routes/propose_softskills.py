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

PROMPT_HEADER_HSC = """
Analyse l'activité (tâches, contraintes, outils, données, performances) et propose 3 à 8
Habiletés Socio-Cognitives (HSC) structurées sous forme d'objets JSON avec :
- habilete: libellé court (ex: "Attention soutenue", "Analyse critique")
- niveau: "1 (Aptitude)", "2 (Acquisition)", "3 (Maîtrise)" ou "4 (Excellence)"
- justification: 1 à 2 phrases sur le lien avec l'activité

IMPORTANT: Réponds UNIQUEMENT avec un tableau JSON valide, sans texte avant ou après, sans backticks markdown.
Exemple de format attendu:
[{"habilete": "Analyse critique", "niveau": "2 (Acquisition)", "justification": "..."}]
"""


def clean_json_response(text):
    """
    Nettoie la réponse de l'IA pour extraire le JSON pur.
    Supprime les backticks markdown, le texte avant/après le JSON.
    """
    # Supprimer les blocs de code markdown ```json ... ``` ou ``` ... ```
    text = re.sub(r'^```(?:json)?\s*', '', text.strip())
    text = re.sub(r'\s*```$', '', text.strip())
    
    # Chercher le premier [ ou { et le dernier ] ou }
    start_bracket = text.find('[')
    start_brace = text.find('{')
    
    if start_bracket == -1 and start_brace == -1:
        return text  # Pas de JSON trouvé
    
    # Prendre le premier qui apparaît
    if start_bracket == -1:
        start = start_brace
    elif start_brace == -1:
        start = start_bracket
    else:
        start = min(start_bracket, start_brace)
    
    # Trouver la fin correspondante
    if text[start] == '[':
        end = text.rfind(']')
    else:
        end = text.rfind('}')
    
    if end == -1 or end < start:
        return text
    
    return text[start:end+1]


@bp_propose_softskills.route("/propose_softskills/propose", methods=["POST"])
def propose_softskills():
    """
    Version tolérante :
    - si pas de clé OpenAI → on renvoie 3 HSC génériques en fonction de l'activité
    - si OpenAI renvoie juste du texte → on retransforme en tableau d'objets
    -> de cette façon, ton JS a toujours un tableau d'objets {habilete, niveau, justification}
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
                    "niveau": "2 (Acquisition)",
                    "justification": "Proposition générée sans IA (clé OpenAI absente).",
                }
                for item in base
            ]
            return jsonify({"proposals": proposals, "source": err}), 200

        prompt = f"""{PROMPT_HEADER_HSC}

=== CONTEXTE DE L'ACTIVITÉ ===
{ctx}
"""

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un assistant RH/formation expert en habiletés socio-cognitives. Tu réponds UNIQUEMENT en JSON valide, sans markdown ni texte supplémentaire."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        text = resp.choices[0].message.content.strip()
        
        # 🔥 Nettoyer la réponse (supprimer backticks, etc.)
        cleaned_text = clean_json_response(text)

        proposals = []
        parsed_ok = False

        # 1) Tentative JSON
        try:
            data = json.loads(cleaned_text)
            if isinstance(data, dict):
                data = [data]
            for item in data:
                habilete = item.get("habilete") or item.get("label") or item.get("name") or "Habileté"
                niveau = item.get("niveau") or item.get("level") or "2 (Acquisition)"
                
                # S'assurer que le niveau a le bon format
                if isinstance(niveau, int) or (isinstance(niveau, str) and niveau.isdigit()):
                    niveau_map = {
                        "1": "1 (Aptitude)",
                        "2": "2 (Acquisition)", 
                        "3": "3 (Maîtrise)",
                        "4": "4 (Excellence)"
                    }
                    niveau = niveau_map.get(str(niveau), "2 (Acquisition)")
                
                proposals.append({
                    "habilete": habilete,
                    "niveau": niveau,
                    "justification": item.get("justification") or "",
                })
            parsed_ok = True
        except json.JSONDecodeError as e:
            current_app.logger.warning(f"JSON parse failed: {e}. Text was: {cleaned_text[:200]}")
            parsed_ok = False

        # 2) Fallback texte → on découpe en lignes (dernier recours)
        if not parsed_ok or not proposals:
            lines = [l.strip("-•* ").strip() for l in text.splitlines() if l.strip() and not l.strip().startswith("```")]
            for line in lines:
                # Ignorer les lignes qui ressemblent à du JSON partiel
                if line.startswith('{') or line.startswith('[') or line.startswith('"') or line.startswith('}') or line.startswith(']'):
                    continue
                if len(line) > 3:  # Ignorer les lignes trop courtes
                    proposals.append({
                        "habilete": line[:100],  # Limiter la longueur
                        "niveau": "2 (Acquisition)",
                        "justification": "",
                    })

        # 3) Fallback ultime si toujours vide
        if not proposals:
            proposals = [
                {
                    "habilete": "Communication professionnelle",
                    "niveau": "2 (Acquisition)",
                    "justification": "Habileté de base requise pour cette activité.",
                }
            ]

        return jsonify({"proposals": proposals}), 200

    except Exception as e:
        current_app.logger.exception(e)
        # On ne casse pas le front
        return (
            jsonify({
                "proposals": [
                    {
                        "habilete": "Habileté non déterminée (erreur serveur).",
                        "niveau": "2 (Acquisition)",
                        "justification": "",
                    }
                ],
                "error": str(e),
            }),
            200,
        )