from flask import Blueprint, jsonify, request
from extensions import db
from models.models import Activity

activities_bp = Blueprint('activities', __name__)

@activities_bp.route('/activities', methods=['GET'])
def get_activities():
    activities = Activity.query.all()
    return jsonify([{"id": activity.id, "name": activity.name} for activity in activities])

@activities_bp.route('/activities', methods=['POST'])
def create_activity():
    data = request.get_json()
    new_activity = Activity(name=data['name'])
    db.session.add(new_activity)
    db.session.commit()
    return jsonify({"id": new_activity.id, "name": new_activity.name}), 201
