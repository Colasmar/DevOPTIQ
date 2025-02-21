import os
import openai
from flask import Blueprint, request, jsonify

skills_bp = Blueprint('skills', __name__, url_prefix='/skills')

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise Exception("La variable d'environnement OPENAI_API_KEY n'est pas définie.")

@skills_bp.route('/propose', methods=['POST'])
def propose_skills():
    """
    Endpoint pour proposer 2 ou 3 compétences sous forme de phrase unique,
    en s'appuyant sur les données de l'activité, conformément à la norme X50-124,
    sans mentionner l'environnement ni la performance.
    """
    data = request.get_json() or {}

    # Extraction des infos de l'activité
    activity_name = data.get("name", "Activité non renseignée")
    input_data_value = data.get("input_data", "")
    output_data_value = data.get("output_data", "")
    
    # Tâches : peuvent être envoyées sous forme de liste de dictionnaires ou de chaînes
    tasks_data = data.get("tasks", [])
    if tasks_data and isinstance(tasks_data[0], dict):
        tasks_list = [t.get("name", "") for t in tasks_data]
    elif tasks_data and isinstance(tasks_data[0], str):
        tasks_list = tasks_data
    else:
        tasks_list = []
    tasks_str = ", ".join(tasks_list) if tasks_list else ""

    # Outils (si vous les transmettez côté front, sinon laissez vide)
    tools_data = data.get("tools", [])
    if tools_data and isinstance(tools_data[0], dict):
        tools_list = [t.get("name", "") for t in tools_data]
    elif tools_data and isinstance(tools_data[0], str):
        tools_list = tools_data
    else:
        tools_list = []
    tools_str = ", ".join(tools_list) if tools_list else ""

    # Construction du prompt
    prompt = f"""
Vous êtes un expert en gestion des compétences selon la norme NF X50-124.
Vous devez proposer 2 ou 3 compétences pour l'activité suivante :

- Nom : {activity_name}
- Données d'entrée : {input_data_value}
- Données de sortie : {output_data_value}
- Tâches : {tasks_str if tasks_str else "Aucune tâche"}
- Outils : {tools_str if tools_str else "Aucun outil"}

Contraintes :
1) Une compétence doit être rédigée en **une seule phrase** (sans puces ni liste),
   en s'appuyant sur les données ci-dessus.
2) N'évoquez ni l'environnement de travail ni le niveau de performance.
3) Suivez la logique du Tableau 7.1 (NF X50-124) mais **sans** faire un listing 
   "Données d'entrée:..., Données de sortie:..., Tâches:..., Outils:...".
4) Chaque phrase doit commencer par un verbe d'action et mentionner en filigrane 
   (sans mot-clé explicite) les éléments importants (entrées, tâches, outils, sorties).
5) Proposez exactement 2 ou 3 phrases de compétences.

Exemple (à titre indicatif, vous en produirez 2 ou 3) :
"**Compétence :** Sélectionner les composants requis en s'appuyant sur la demande initiale et 
les tâches d'évaluation, afin de livrer une configuration validée, en mobilisant les outils 
de suivi appropriés."

Générez maintenant 2 ou 3 phrases similaires, chacune sur une nouvelle ligne.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",  # ou "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "Vous êtes un assistant spécialisé en gestion des compétences NF X50-124."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=400
        )

        raw_text = response['choices'][0]['message']['content'].strip()
        # Découper en lignes pour que le front puisse les afficher distinctement
        lines = [l.strip() for l in raw_text.split("\n") if l.strip()]

        return jsonify({"proposals": lines}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
