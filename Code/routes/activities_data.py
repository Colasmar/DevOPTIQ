# Code/routes/activities_data.py
# ----------------------------------------------------------------------
# Fichier qui gère la route /activities/<activity_id>/details,
# renvoyant toutes les infos nécessaires (name, description, tasks, tools, etc.)
# On force un nom et une description par défaut si l'activité en DB est incomplète.
# ----------------------------------------------------------------------

from flask import jsonify, request
from .activities_bp import activities_bp
from Code.extensions import db
from Code.models.models import Activities, Task, Role, Performance, Link, Data, Constraint, Competency, Softskill

@activities_bp.route('/<int:activity_id>/details', methods=['GET'])
def get_activity_details(activity_id):
    """
    Retourne un JSON décrivant l’activité <activity_id> :
    {
      "id": ...,
      "name": ...,
      "description": ...,
      "tasks": [...],
      "tools": [...],
      "constraints": [...],
      "competencies": [...],
      "outgoing": [...]
      ...
    }
    """
    activity = Activities.query.get(activity_id)
    if not activity:
        return jsonify({"error": "Activité non trouvée"}), 404

    # On sécurise le nom et la description :
    # si c'est vide ou None, on met des valeurs par défaut.
    safe_name = activity.name.strip() if activity.name else ""
    if not safe_name:
        safe_name = f"Activité-{activity.id} (Nom indisponible)"

    safe_description = (activity.description or "").strip()
    if not safe_description:
        safe_description = "Aucune description disponible."

    # Tâches => simple liste de noms
    tasks_list = [t.name for t in activity.tasks]

    # Outils => cumulés depuis toutes les tasks
    tools_list = []
    for t in activity.tasks:
        for tl in t.tools:
            if tl.name not in tools_list:
                tools_list.append(tl.name)

    # Contraintes
    constraints_list = [{"description": c.description} for c in activity.constraints]

    # Compétences existantes
    competencies_list = [{"description": comp.description} for comp in activity.competencies]

    # Performances "sortantes"
    outgoing_data = []
    all_links = Link.query.filter_by(source_activity_id=activity.id).all()
    for link in all_links:
        perf_obj = link.performance
        if perf_obj:
            outgoing_data.append({"performance": {
                "name": perf_obj.name,
                "description": perf_obj.description
            }})
        else:
            outgoing_data.append({"performance": None})

    # On renvoie un dict global
    activity_data = {
        "id": activity.id,
        "name": safe_name,                 # Non vide
        "description": safe_description,   # Non vide
        "tasks": tasks_list,
        "tools": tools_list,
        "constraints": constraints_list,
        "competencies": competencies_list,
        "outgoing": outgoing_data,
        "input_data": "Aucune donnée d'entrée (placeholder)",
        "output_data": "Aucune donnée de sortie (placeholder)"
    }

    return jsonify(activity_data), 200
