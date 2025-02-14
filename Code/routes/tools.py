from flask import Blueprint, request, jsonify
from Code.extensions import db
from Code.models.models import Task, Tool

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
        if 'existing_tool_ids' in data and isinstance(data['existing_tool_ids'], list):
            for tool_id in data['existing_tool_ids']:
                tool = Tool.query.get(tool_id)
                if tool and tool not in task.tools:
                    task.tools.append(tool)
                    added_tools.append({"id": tool.id, "name": tool.name})
        if 'new_tools' in data and isinstance(data['new_tools'], list):
            for tool_name in data['new_tools']:
                if tool_name:
                    tool = Tool.query.filter(db.func.lower(Tool.name) == tool_name.lower()).first()
                    if not tool:
                        tool = Tool(name=tool_name)
                        db.session.add(tool)
                        db.session.flush()  # obtenir l'id
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
    tools = Tool.query.all()
    return jsonify([{'id': tool.id, 'name': tool.name} for tool in tools])
