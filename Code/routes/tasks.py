from flask import Blueprint, request, jsonify
from Code.extensions import db
from Code.models.models import Task, Activities

tasks_bp = Blueprint('tasks', __name__, url_prefix='/tasks')

@tasks_bp.route('/add', methods=['POST'])
def add_task():
    """
    Ajoute une tâche associée à une activité.
    Expects JSON with keys: activity_id, name, (optionnellement description et order).
    """
    data = request.get_json()
    if not data or 'activity_id' not in data or 'name' not in data:
        return jsonify({'error': 'Données invalides. "activity_id" et "name" sont requis.'}), 400

    activity = Activities.query.get(data['activity_id'])
    if not activity:
        return jsonify({'error': 'Activité non trouvée.'}), 404

    new_task = Task(
        name=data['name'],
        description=data.get('description', ''),
        order=data.get('order', None),
        activity_id=data['activity_id']
    )
    db.session.add(new_task)
    db.session.commit()

    return jsonify({
        'id': new_task.id,
        'name': new_task.name,
        'description': new_task.description,
        'order': new_task.order,
        'activity_id': new_task.activity_id
    }), 201
