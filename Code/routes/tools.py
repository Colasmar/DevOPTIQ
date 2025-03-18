# Code/routes/tools.py

from flask import Blueprint, request, jsonify
from Code.extensions import db
from Code.models.models import Task, Tool
from sqlalchemy import func

tools_bp = Blueprint('tools', __name__, url_prefix='/tools')

@tools_bp.route('/add', methods=['POST'])
def add_tools_to_task():
    data = request.get_json()
    if not data or 'task_id' not in data:
        return jsonify({"error": "task_id is required"}), 400

    task = Task.query.get(data['task_id'])
    if not task:
        return jsonify({"error": "Task not found"}), 404

    added_tools = []
    try:
        # (1) Associer des outils existants via leurs IDs
        if 'existing_tool_ids' in data and isinstance(data['existing_tool_ids'], list):
            for tool_id in data['existing_tool_ids']:
                tool = Tool.query.get(tool_id)
                if tool and tool not in task.tools:
                    task.tools.append(tool)
                    added_tools.append({"id": tool.id, "name": tool.name})

        # (2) Créer ou associer de nouveaux outils par leur nom
        if 'new_tools' in data and isinstance(data['new_tools'], list):
            for tool_name in data['new_tools']:
                if tool_name:
                    # Vérifier si un outil du même nom existe déjà (insensible à la casse)
                    tool = Tool.query.filter(func.lower(Tool.name) == tool_name.lower()).first()
                    if not tool:
                        tool = Tool(name=tool_name)
                        db.session.add(tool)
                        db.session.flush()  # obtenir l'id du nouvel outil
                    if tool not in task.tools:
                        task.tools.append(tool)
                        added_tools.append({"id": tool.id, "name": tool.name})

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify({"task_id": task.id, "added_tools": added_tools}), 200

@tools_bp.route('/all', methods=['GET'])
def get_all_tools():
    """
    Renvoie la liste de tous les outils en ordre alphabétique.
    """
    tools = Tool.query.order_by(Tool.name).all()
    return jsonify([{'id': tool.id, 'name': tool.name} for tool in tools])
