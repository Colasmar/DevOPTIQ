import os
import io
import contextlib
import traceback
from flask import Blueprint, jsonify, request, render_template
from sqlalchemy import text
from Code.extensions import db
from Code.models.models import Activities, Data, Link, Task, Tool, Competency, Softskill, Constraint, Savoir, SavoirFaire, Aptitude
from Code.scripts.extract_visio import process_visio_file, print_summary

activities_bp = Blueprint('activities', __name__, url_prefix='/activities', template_folder='templates')

def resolve_return_activity_name(data_record):
    if data_record and data_record.type and data_record.type.lower() == 'retour':
        act = Activities.query.filter_by(name=data_record.name).first()
        if act:
            return act.name
    if data_record and data_record.name:
        return data_record.name
    return "[Nom non renseigné]"

def resolve_data_name_for_incoming(link):
    if link.type and link.type.lower() == 'input':
        data_record = Data.query.get(link.source_id)
        if data_record:
            return resolve_return_activity_name(data_record)
    if link.description:
        return link.description
    return "[Nom non renseigné]"

def resolve_data_name_for_outgoing(link):
    if link.type and link.type.lower() == 'output':
        data_record = Data.query.get(link.target_id)
        if data_record:
            return resolve_return_activity_name(data_record)
    if link.description:
        return link.description
    return "[Nom non renseigné]"

def resolve_activity_name(record_id):
    act = Activities.query.get(record_id)
    if act:
        return act.name
    data_record = Data.query.get(record_id)
    if data_record:
        if data_record.type and data_record.type.lower() == 'retour':
            linked_act = Activities.query.filter_by(name=data_record.name).first()
            if linked_act:
                return linked_act.name
        if data_record.name:
            return data_record.name
    return "[Activité inconnue]"

def get_garant_role(activity_id):
    """
    Retourne le rôle Garant associé à l'activité (status='Garant'), ou None.
    """
    result = db.session.execute(
        text("SELECT r.id, r.name FROM activity_roles ar JOIN roles r ON ar.role_id = r.id "
             "WHERE ar.activity_id = :aid AND ar.status = 'Garant'"),
        {"aid": activity_id}
    ).fetchone()
    if result:
        return {"id": result[0], "name": result[1]}
    return None

@activities_bp.route('/', methods=['GET'])
def get_activities():
    try:
        all_acts = Activities.query.all()
        data = []
        for a in all_acts:
            data.append({
                "id": a.id,
                "name": a.name,
                "description": a.description or ""
            })
        return jsonify(data), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@activities_bp.route('/', methods=['POST'])
def create_activity():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Invalid input. 'name' is required."}), 400
    try:
        new_activity = Activities(name=data['name'], description=data.get('description'))
        db.session.add(new_activity)
        db.session.commit()
        return jsonify({
            "id": new_activity.id,
            "name": new_activity.name,
            "description": new_activity.description or ""
        }), 201
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@activities_bp.route('/<int:activity_id>/tasks/add', methods=['POST'])
def add_task_to_activity(activity_id):
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Invalid input. 'name' is required."}), 400
    try:
        new_task = Task(
            name=data['name'],
            description=data.get('description', ""),
            activity_id=activity_id
        )
        db.session.add(new_task)
        db.session.commit()
        return jsonify({
            "id": new_task.id,
            "name": new_task.name,
            "description": new_task.description or ""
        }), 201
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@activities_bp.route('/<int:activity_id>/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(activity_id, task_id):
    task = Task.query.filter_by(id=task_id, activity_id=activity_id).first()
    if not task:
        return jsonify({"error": "Task not found for this activity"}), 404
    try:
        db.session.delete(task)
        db.session.commit()
        return jsonify({"message": "Task deleted"}), 200
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@activities_bp.route('/<int:activity_id>/tasks/<int:task_id>', methods=['PUT'])
def update_task(activity_id, task_id):
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Invalid input. 'name' is required."}), 400
    task = Task.query.filter_by(id=task_id, activity_id=activity_id).first()
    if not task:
        return jsonify({"error": "Task not found for this activity"}), 404
    try:
        task.name = data['name']
        task.description = data.get('description', "")
        db.session.commit()
        return jsonify({
            "id": task.id,
            "name": task.name,
            "description": task.description or ""
        }), 200
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@activities_bp.route('/tasks/<int:task_id>/tools/<int:tool_id>', methods=['DELETE'])
def delete_tool_from_task(task_id, tool_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    tool = None
    for t in task.tools:
        if t.id == tool_id:
            tool = t
            break
    if not tool:
        return jsonify({"error": "Tool not associated with task"}), 404
    try:
        task.tools.remove(tool)
        db.session.commit()
        return jsonify({"message": "Tool removed from task"}), 200
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@activities_bp.route('/<int:activity_id>/tasks/reorder', methods=['POST'])
def reorder_tasks(activity_id):
    """
    Réordonne les tâches via Drag&Drop.
    JSON: { "order": [12, 13, 15] }
    """
    data = request.get_json()
    new_order = data.get('order')
    if not new_order:
        return jsonify({"error": "order list is required"}), 400
    try:
        for idx, t_id in enumerate(new_order):
            task = Task.query.filter_by(id=t_id, activity_id=activity_id).first()
            if task:
                task.order = idx
        db.session.commit()
        return jsonify({"message": "Order updated"}), 200
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@activities_bp.route('/update-cartography', methods=['GET'])
def update_cartography():
    try:
        vsdx_path = os.path.join("Code", "example.vsdx")
        process_visio_file(vsdx_path)
        summary_output = io.StringIO()
        with contextlib.redirect_stdout(summary_output):
            print_summary()
        summary_text = summary_output.getvalue()
        return jsonify({
            "message": "Cartographie mise à jour (partielle)",
            "summary": summary_text
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@activities_bp.route('/view', methods=['GET'])
def view_activities():
    try:
        activities = Activities.query.filter_by(is_result=False).all()
        activity_data = []

        for activity in activities:
            incoming_links = Link.query.filter(
                (Link.target_activity_id == activity.id) | (Link.target_data_id == activity.id)
            ).all()
            incoming_list = [{
                'type': link.type,
                'data_name': resolve_data_name_for_incoming(link),
                'source_name': resolve_activity_name(link.source_id)
            } for link in incoming_links]

            outgoing_links = Link.query.filter(
                (Link.source_activity_id == activity.id) | (Link.source_data_id == activity.id)
            ).all()
            outgoing_list = []
            for link in outgoing_links:
                data_obj = Data.query.get(link.target_id) if link.target_id else None
                perf_obj = {
                    'id': link.performance.id,
                    'name': link.performance.name,
                    'description': link.performance.description
                } if link.performance else None

                outgoing_list.append({
                    'type': link.type,
                    'data_name': resolve_data_name_for_outgoing(link),
                    'target_name': resolve_activity_name(link.target_activity_id),
                    'data_id': data_obj.id if data_obj else None,
                    'performance': perf_obj,
                    'link_id': link.id
                })

            tasks_sorted = sorted(
                activity.tasks,
                key=lambda x: int(x.order) if (x.order is not None and str(x.order).strip() != "") else 0
            )
            tasks_list = [{
                'id': t.id,
                'name': t.name,
                'description': t.description,
                'order': t.order,
                'tools': [
                    {'id': tool.id, 'name': tool.name, 'description': tool.description}
                    for tool in t.tools
                ]
            } for t in tasks_sorted]

            garant = get_garant_role(activity.id)
            constraints_list = [{"id": c.id, "description": c.description} for c in activity.constraints]

            # On récupère la liste des savoirs, savoir-faires, aptitudes
            savoirs_list = [{"id": sv.id, "description": sv.description} for sv in activity.savoirs]
            sf_list = [{"id": sf.id, "description": sf.description} for sf in activity.savoir_faires]
            apt_list = [{"id": ap.id, "description": ap.description} for ap in activity.aptitudes]

            activity_data.append({
                'activity': activity,
                'incoming': incoming_list,
                'outgoing': outgoing_list,
                'tasks': tasks_list,
                'garant': garant,
                'constraints': constraints_list,
                'savoirs': savoirs_list,
                'savoir_faires': sf_list,
                'aptitudes': apt_list
            })

        return render_template('display_list.html', activity_data=activity_data)
    except Exception as e:
        traceback.print_exc()
        return f"Erreur lors de l'affichage des activités: {e}", 500

@activities_bp.route('/<int:activity_id>/details', methods=['GET'])
def get_activity_details(activity_id):
    """
    Retourne un JSON avec toutes les infos (tasks, constraints, etc.)
    pour l'IA "Proposer Compétences" ou "Proposer Softskills".
    """
    activity = Activities.query.get(activity_id)
    if not activity:
        return jsonify({"error": "Activité non trouvée"}), 404

    # Tâches => simple liste de noms
    tasks_list = [t.name or "" for t in activity.tasks]

    # Outils => cumulés
    tools_list = []
    for t in activity.tasks:
        for tool in t.tools:
            if tool.name not in tools_list:
                tools_list.append(tool.name)

    # Contraintes
    constraints_list = [{"description": c.description} for c in activity.constraints]

    # Compétences existantes
    competencies_list = [{"description": comp.description} for comp in activity.competencies]

    # Performances "outgoing"
    outgoing_data = []
    all_links = Link.query.filter_by(source_activity_id=activity.id).all()
    for link in all_links:
        perf = None
        if link.performance:
            perf = {
                "name": link.performance.name,
                "description": link.performance.description
            }
        outgoing_data.append({"performance": perf})

    # On peut rajouter "input_data"/"output_data" si besoin
    input_data_value = "Aucune donnée d'entrée"
    output_data_value = "Aucune donnée de sortie"

    # Regrouper
    activity_data = {
        "id": activity.id,
        "name": activity.name,
        "input_data": input_data_value,
        "output_data": output_data_value,
        "tasks": tasks_list,
        "tools": tools_list,
        "constraints": constraints_list,
        "competencies": competencies_list,
        "outgoing": outgoing_data
    }
    return jsonify(activity_data), 200
