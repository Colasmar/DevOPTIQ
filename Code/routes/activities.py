import os
import io
import contextlib
from flask import Blueprint, jsonify, request, render_template
from Code.extensions import db
from Code.models.models import Activities, Connections, Data, Task, Tool
from Code.scripts.extract_visio import reset_database, process_visio_file, print_summary

activities_bp = Blueprint('activities', __name__, url_prefix='/activities', template_folder='templates')

def resolve_return_activity_name(data_record):
    if data_record and data_record.type and data_record.type.lower() == 'retour':
        activity = Activities.query.filter_by(name=data_record.name).first()
        if activity:
            return activity.name
    return data_record.name if data_record and data_record.name else "[Nom non renseigné]"

def resolve_data_name_for_incoming(conn):
    if conn.type and conn.type.lower() == 'input':
        data_record = Data.query.get(conn.source_id)
        if data_record and data_record.name:
            return resolve_return_activity_name(data_record)
    if conn.description:
        return conn.description
    return "[Nom non renseigné]"

def resolve_data_name_for_outgoing(conn):
    if conn.type and conn.type.lower() == 'output':
        data_record = Data.query.get(conn.target_id)
        if data_record and data_record.name:
            return resolve_return_activity_name(data_record)
    if conn.description:
        return conn.description
    return "[Nom non renseigné]"

def resolve_activity_name(record_id):
    """Renvoie le nom d'une activité ou d'une donnée (si c'est un noeud Data)."""
    activity = Activities.query.get(record_id)
    if activity:
        return activity.name
    data_record = Data.query.get(record_id)
    if data_record:
        if data_record.type and data_record.type.lower() == 'retour':
            act = Activities.query.filter_by(name=data_record.name).first()
            if act:
                return act.name
        return data_record.name
    return "[Activité inconnue]"

@activities_bp.route('/', methods=['GET'])
def get_activities():
    """Renvoie la liste de toutes les activités au format JSON (non utilisé directement ici)."""
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
    """Crée une nouvelle activité (non essentiel ici, mais gardé pour cohérence)."""
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
    """Ajoute une tâche à une activité."""
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
    """Supprime une tâche."""
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
    """Met à jour une tâche existante."""
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
    """Supprime un outil associé à la tâche."""
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
    """Réordonne les tâches selon la liste transmise."""
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
    """
    Retourne les infos d'une activité au format JSON,
    pour le bouton "Proposer Compétences".
    """
    activity = Activities.query.get(activity_id)
    if not activity:
        return jsonify({"error": "Activité non trouvée"}), 404

    # Construire la liste des tâches (juste les noms)
    tasks_list = []
    # Construire la liste des outils (tous ceux utilisés par les tâches)
    tools_list = []
    for t in activity.tasks:
        tasks_list.append(t.name or "")
        for tool in t.tools:
            if tool.name not in tools_list:
                tools_list.append(tool.name)

    # Gérer input_data / output_data si votre modèle le permet
    input_data_value = getattr(activity, "input_data", "Aucune donnée d'entrée")
    output_data_value = getattr(activity, "output_data", "Aucune donnée de sortie")

    activity_data = {
        "id": activity.id,
        "name": activity.name,
        "description": activity.description or "",
        "input_data": input_data_value,
        "output_data": output_data_value,
        "tasks": tasks_list,
        "tools": tools_list
    }
    return jsonify(activity_data), 200

@activities_bp.route('/update-cartography', methods=['GET'])
def update_cartography():
    """Réinitialise la base et relance le parsing du vsdx (exemple)."""
    try:
        vsdx_path = os.path.join("Code", "example.vsdx")
        reset_database()
        process_visio_file(vsdx_path)
        summary_output = io.StringIO()
        with contextlib.redirect_stdout(summary_output):
            print_summary()
        summary_text = summary_output.getvalue()
        return jsonify({"message": "Cartographie mise à jour", "summary": summary_text}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@activities_bp.route('/view', methods=['GET'])
def view_activities():
    """
    Affiche la liste des activités via display_list.html
    On y inclut toutes les infos : connexions, tâches, ...
    """
    try:
        activities = Activities.query.filter_by(is_result=False).all()
        activity_data = []
        for activity in activities:
            # Connexions entrantes
            incoming_conns = Connections.query.filter(Connections.target_id == activity.id).all()
            incoming_list = []
            for conn in incoming_conns:
                conn_type = conn.type or ""
                data_name = resolve_data_name_for_incoming(conn)
                source_name = resolve_activity_name(conn.source_id)
                incoming_list.append({
                    'type': conn.type,
                    'data_name': data_name,
                    'source_name': source_name
                })
            # Connexions sortantes
            outgoing_conns = Connections.query.filter(Connections.source_id == activity.id).all()
            outgoing_list = []
            for conn in outgoing_conns:
                conn_type = conn.type or ""
                data_name = resolve_data_name_for_outgoing(conn)
                target_name = resolve_activity_name(conn.target_id)
                outgoing_list.append({
                    'type': conn.type,
                    'data_name': data_name,
                    'target_name': target_name
                })
            # Tâches triées par 'order'
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

            activity_data.append({
                'activity': activity,
                'incoming': incoming_list,
                'outgoing': outgoing_list,
                'tasks': tasks_list
            })

        return render_template('display_list.html', activity_data=activity_data)
    except Exception as e:
        return f"Erreur lors de l'affichage des activités: {e}", 500
