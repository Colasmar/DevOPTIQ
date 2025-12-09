# Code/routes/translate_softskills.py
import os
import json
import re
from flask import Blueprint, request, jsonify, current_app

translate_softskills_bp = Blueprint('translate_softskills_bp', __name__, url_prefix='/translate_softskills')


def get_openai_client():
    """
    Retourne un client OpenAI (nouvelle API >= 1.0) ou None si pas de clé.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None, "Clé OpenAI manquante (OPENAI_API_KEY)."
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        return client, None
    except Exception as e:
        return None, str(e)


def clean_json_response(text):
    """
    Nettoie la réponse de l'IA pour extraire le JSON pur.
    Supprime les backticks markdown, le texte avant/après le JSON.
    """
    # Supprimer les blocs de code markdown ```json ... ``` ou ``` ... ```
    text = re.sub(r'^```(?:json)?\s*', '', text.strip())
    text = re.sub(r'\s*```$', '', text.strip())
    
    # Chercher le premier [ et le dernier ]
    start = text.find('[')
    end = text.rfind(']')
    
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    
    # Sinon chercher { et }
    start = text.find('{')
    end = text.rfind('}')
    
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    
    return text


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
- Traitement de l'information
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
1) Génère 3 à 5 habiletés, sous forme d'un tableau JSON brut (pas de texte hors JSON, pas de backticks markdown).
2) Chaque entrée = {{
    "habilete": <str parmi la liste ci-dessus>,
    "niveau": "X (Label)",  (ex: "2 (Acquisition)")
    "justification": "..."
}}
3) "justification" doit mentionner explicitement "{user_input}" et faire référence aux T(i), C(i) ou P(i) si pertinent.
4) N'UTILISE PAS d'autres habiletés que celles de la liste X50-766.
5) RÉPONDS UNIQUEMENT AVEC LE TABLEAU JSON, sans aucun texte avant ou après.
"""

    # 🔥 Utiliser la nouvelle API OpenAI
    client, err = get_openai_client()
    if client is None:
        return jsonify({"error": err}), 500

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # ou "gpt-4" si disponible
            messages=[
                {"role": "system", "content": "Tu es un assistant spécialisé en habiletés socio-cognitives X50-766. Tu réponds UNIQUEMENT en JSON valide, sans markdown ni texte supplémentaire."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=1200
        )
        ai_text = response.choices[0].message.content.strip()
        
        # 🔥 Nettoyer la réponse
        cleaned_text = clean_json_response(ai_text)

        # On parse le JSON renvoyé
        try:
            proposals = json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            current_app.logger.error(f"JSON parse error: {e}. Raw text: {ai_text[:500]}")
            return jsonify({"error": f"Erreur de parsing JSON: {str(e)}"}), 400
            
        if not isinstance(proposals, list):
            # Si c'est un objet unique, le mettre dans une liste
            if isinstance(proposals, dict):
                proposals = [proposals]
            else:
                return jsonify({"error": "Le JSON renvoyé n'est pas un tableau d'objets."}), 400

        # Normaliser les niveaux
        niveau_map = {
            "1": "1 (Aptitude)",
            "2": "2 (Acquisition)", 
            "3": "3 (Maîtrise)",
            "4": "4 (Excellence)"
        }
        
        for p in proposals:
            niveau = p.get("niveau", "2")
            if isinstance(niveau, int) or (isinstance(niveau, str) and niveau.isdigit()):
                p["niveau"] = niveau_map.get(str(niveau), "2 (Acquisition)")

        # On renvoie le tout
        return jsonify({"proposals": proposals}), 200

    except Exception as e:
        current_app.logger.exception(e)
        return jsonify({"error": str(e)}), 500