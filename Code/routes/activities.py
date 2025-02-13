from flask import Blueprint, jsonify, request, render_template
from Code.extensions import db
from Code.models.models import Activities, Connections, Data

# Le blueprint est défini avec le dossier de templates situé dans Code/routes/templates/
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
    try:
        activities = Activities.query.all()
        return jsonify([
            {"id": activity.id, "name": activity.name, "description": activity.description or ""}
            for activity in activities
        ]), 200
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

@activities_bp.route('/view', methods=['GET'])
def view_activities():
    try:
        activities = Activities.query.filter_by(is_result=False).all()
        activity_data = []
        for activity in activities:
            # Traitement des connexions entrantes
            incoming_conns = Connections.query.filter(Connections.target_id == activity.id).all()
            incoming_list = []
            for conn in incoming_conns:
                conn_type = conn.type or ""
                if conn_type.lower() == 'input':
                    display_type = 'Nourrissante'
                elif conn_type.lower() == 'output':
                    display_type = 'Déclenchante'
                else:
                    display_type = conn_type
                data_name = resolve_data_name_for_incoming(conn)
                source_name = resolve_activity_name(conn.source_id)
                incoming_list.append({
                    'type': conn.type,
                    'data_name': data_name,
                    'source_name': source_name
                })
            # Traitement des connexions sortantes
            outgoing_conns = Connections.query.filter(Connections.source_id == activity.id).all()
            outgoing_list = []
            for conn in outgoing_conns:
                conn_type = conn.type or ""
                if conn_type.lower() == 'output':
                    display_type = 'Déclenchante'
                elif conn_type.lower() == 'input':
                    display_type = 'Nourrissante'
                else:
                    display_type = conn_type
                data_name = resolve_data_name_for_outgoing(conn)
                target_name = resolve_activity_name(conn.target_id)
                outgoing_list.append({
                    'type': conn.type,
                    'data_name': data_name,
                    'target_name': target_name
                })
            # Récupération des tâches associées à l'activité
            tasks = [{'id': t.id, 'name': t.name, 'description': t.description, 'order': t.order} for t in activity.tasks]
            activity_data.append({
                'activity': activity,
                'incoming': incoming_list,
                'outgoing': outgoing_list,
                'tasks': tasks
            })
        return render_template('activities_list.html', activity_data=activity_data)
    except Exception as e:
        return f"Erreur lors de l'affichage des activités: {e}", 500
