from flask import Blueprint, request, jsonify, render_template
from Code.extensions import db
from Code.models.models import Performance, Link
import traceback

performance_bp = Blueprint('performance', __name__, url_prefix='/performance')

@performance_bp.route('/add', methods=['POST'])
def add_performance():
    """
    Crée ou met à jour une Performance pour un link_id donné.
    JSON attendu :
      { "link_id": <int>, "name": "<str>", "description": "<str facultatif>" }
    """
    data = request.get_json() or {}
    link_id = data.get("link_id")
    name = data.get("name", "").strip()
    description = data.get("description", "").strip()

    if not link_id or not name:
        return jsonify({"error": "link_id and name are required"}), 400

    try:
        link = Link.query.get(link_id)
        if not link:
            return jsonify({"error": f"Link ID {link_id} not found"}), 404

        # S’il existe déjà une performance pour ce link => on met à jour
        existing_perf = Performance.query.filter_by(link_id=link_id).first()
        if existing_perf:
            existing_perf.name = name
            existing_perf.description = description
            db.session.commit()
            return jsonify({
                "id": existing_perf.id,
                "name": existing_perf.name,
                "description": existing_perf.description,
                "link_id": link_id
            }), 200

        # Sinon, on crée une nouvelle Performance
        new_perf = Performance(link_id=link_id, name=name, description=description)
        db.session.add(new_perf)
        db.session.commit()
        return jsonify({
            "id": new_perf.id,
            "name": new_perf.name,
            "description": new_perf.description,
            "link_id": link_id
        }), 201

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@performance_bp.route('/<int:perf_id>', methods=['PUT', 'DELETE'])
def manage_performance(perf_id):
    """
    - PUT => modifie (JSON: { "name":"...", "description":"..." })
    - DELETE => supprime
    """
    perf = Performance.query.get(perf_id)
    if not perf:
        return jsonify({"error": "Performance not found"}), 404

    if request.method == 'PUT':
        data = request.get_json() or {}
        new_name = data.get("name", "").strip()
        new_desc = data.get("description", "").strip()

        if not new_name:
            return jsonify({"error": "name is required"}), 400

        try:
            perf.name = new_name
            perf.description = new_desc
            db.session.commit()
            return jsonify({"message": "Performance updated"}), 200
        except Exception as e:
            db.session.rollback()
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    elif request.method == 'DELETE':
        try:
            db.session.delete(perf)
            db.session.commit()
            return jsonify({"message": "Performance deleted"}), 200
        except Exception as e:
            db.session.rollback()
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

@performance_bp.route('/render/<int:link_id>', methods=['GET'])
def render_performance_partial(link_id):
    """
    Retourne un fragment HTML : 
      - si Performance existe => on affiche (nom, description, boutons)
      - sinon => bouton "Performance"
    """
    try:
        perf_obj = Performance.query.filter_by(link_id=link_id).first()
        return render_template("performance_partial.html", link_id=link_id, performance=perf_obj)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
