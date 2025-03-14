# Code/routes/activities.py

import os
import io
import contextlib
from flask import Blueprint, jsonify, request, render_template
from sqlalchemy import text  # <-- pour la requête brute du Garant
from Code.extensions import db
from Code.models.models import Activities, Data, Link, Task, Tool, Competency, Softskill, Constraint
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

# AJOUT MINIMAL : récupérer le Garant
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
        activities = Activities.query.all()
        data = []
        for a in activities:
            data.append({
                "id": a.id,
                "name": a.name,
                "description": a.description or ""
            })
        return jsonify(data), 200
    except Exception as e:
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
        return jsonify({"error": str(e)}), 500

@activities_bp.route('/<int:activity_id>/tasks/reorder', methods=['POST'])
def reorder_tasks(activity_id):
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
        return jsonify({"error": str(e)}), 500

@activities_bp.route('/<int:activity_id>/details', methods=['GET'])
def get_activity_details(activity_id):
    activity = Activities.query.get(activity_id)
    if not activity:
        return jsonify({"error": "Activité non trouvée"}), 404

    tasks_list = []
    tools_list = []
    for t in activity.tasks:
        tasks_list.append(t.name or "")
        for tool in t.tools:
            if tool.name not in tools_list:
                tools_list.append(tool.name)

    input_data_value = getattr(activity, "input_data", "Aucune donnée d'entrée")
    output_data_value = getattr(activity, "output_data", "Aucune donnée de sortie")
    competencies = [{"id": comp.id, "description": comp.description} for comp in activity.competencies]
    softskills = [{"id": ss.id, "habilete": ss.habilete, "niveau": ss.niveau} for ss in activity.softskills]

    activity_data = {
        "id": activity.id,
        "name": activity.name,
        "description": activity.description or "",
        "input_data": input_data_value,
        "output_data": output_data_value,
        "tasks": tasks_list,
        "tools": tools_list,
        "competencies": competencies,
        "softskills": softskills
    }
    return jsonify(activity_data), 200

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
        return jsonify({"error": str(e)}), 500

@activities_bp.route('/view', methods=['GET'])
def view_activities():
    try:
        # Récupère uniquement les activités non marquées comme résultat
        activities = Activities.query.filter_by(is_result=False).all()

        activity_data = []
        for activity in activities:
            # Connexions entrantes
            incoming_links = Link.query.filter(
                (Link.target_activity_id == activity.id) | (Link.target_data_id == activity.id)
            ).all()
            incoming_list = []
            for link in incoming_links:
                data_name = resolve_data_name_for_incoming(link)
                source_name = resolve_activity_name(link.source_id)
                incoming_list.append({
                    'type': link.type,
                    'data_name': data_name,
                    'source_name': source_name
                })

            # Connexions sortantes
            outgoing_links = Link.query.filter(
                (Link.source_activity_id == activity.id) | (Link.source_data_id == activity.id)
            ).all()

            outgoing_list = []
            for link in outgoing_links:
                data_name = resolve_data_name_for_outgoing(link)
                target_name = resolve_activity_name(link.target_id)

                # Vérifier si link.target_id correspond à une Data
                data_obj = Data.query.get(link.target_id)
                perf_obj = None
                data_id = None
                if data_obj:
                    data_id = data_obj.id
                    if data_obj.performance:
                        perf_obj = {
                            'id': data_obj.performance.id,
                            'name': data_obj.performance.name,
                            'description': data_obj.performance.description
                        }

                outgoing_list.append({
                    'type': link.type,
                    'data_name': data_name,
                    'target_name': target_name,
                    'data_id': data_id,     # <-- L'ID de la Data (ou None)
                    'performance': perf_obj # <-- La performance associée, ou None
                })

            # Tâches
            tasks = sorted(activity.tasks, key=lambda x: x.order if x.order is not None else 0)
            tasks_list = []
            for t in tasks:
                tasks_list.append({
                    'id': t.id,
                    'name': t.name,
                    'description': t.description,
                    'order': t.order,
                    'tools': [
                        {'id': tool.id, 'name': tool.name, 'description': tool.description}
                        for tool in t.tools
                    ]
                })

            # Garant
            garant = get_garant_role(activity.id)

            # Contraintes (nouveau)
            constraints_list = []
            for c in activity.constraints:
                constraints_list.append({
                    "id": c.id,
                    "description": c.description
                })

            # Ajouter la structure à activity_data
            activity_data.append({
                'activity': activity,
                'incoming': incoming_list,
                'outgoing': outgoing_list,
                'tasks': tasks_list,
                'garant': garant,
                'constraints': constraints_list  # <-- AJOUT
            })

        return render_template('display_list.html', activity_data=activity_data)
    except Exception as e:
        return f"Erreur lors de l'affichage des activités: {e}", 500

def print_summary():
    print("\n--- RÉSUMÉ DES LIENS ---")
    if link_summaries:
        for (data_name, data_type, s_name, t_name) in link_summaries:
            print(f"  - '{data_name}' ({data_type}) : {s_name} -> {t_name}")
    else:
        print("  Aucun lien créé")
    print("--- Fin du résumé ---\n")
    if rename_summaries:
        print("--- Renommages détectés ---")
        for (old, new) in rename_summaries:
            print(f"  * '{old}' => '{new}'")
        print("--- Fin des renommages ---\n")
    print("CONFIRMATION : toutes les opérations ont été effectuées avec succès.")
