from flask import jsonify, request
from .activities_bp import activities_bp
from Code.extensions import db
from Code.models.models import Activities, Task, Role, Performance, Link, Data, Constraint, Competency, Softskill
from sqlalchemy import text

@activities_bp.route('/<int:activity_id>/details', methods=['GET'])
def get_activity_details(activity_id):
    """
    Route utilisée par "Proposer compétence", "Proposer HSC", "Traduire softskills", etc.
    Renvoie un JSON décrivant tasks, tools, constraints, outgoing performances...
    """
    activity = Activities.query.get(activity_id)
    if not activity:
        return jsonify({"error": "Activité non trouvée"}), 404

    # Tâches => simple liste de noms
    tasks_list = [t.name for t in activity.tasks]

    # Outils => cumulés
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
        "name": activity.name,
        "description": activity.description or "",
        "tasks": tasks_list,
        "tools": tools_list,
        "constraints": constraints_list,
        "competencies": competencies_list,
        "outgoing": outgoing_data,
        "input_data": "Aucune donnée d'entrée (placeholder)",
        "output_data": "Aucune donnée de sortie (placeholder)"
    }
    return jsonify(activity_data), 200
