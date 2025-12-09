from flask import jsonify
from Code.extensions import db
from Code.models.models import Performance, Link

def add_performance(link_id, name, description):
    """
    Crée ou met à jour la Performance pour link_id.
    Si link_id a déjà une performance => on la met à jour,
    sinon on en crée une nouvelle.
    """
    existing = Performance.query.filter_by(link_id=link_id).first()
    if existing:
        existing.name = name
        existing.description = description
        db.session.commit()
        return jsonify({"message": "Performance mise à jour", "id": existing.id}), 200

    new_p = Performance(link_id=link_id, name=name, description=description)
    db.session.add(new_p)
    db.session.commit()
    return jsonify({"message": "Performance créée", "id": new_p.id}), 201

def update_performance(perf_id, name, description):
    perf = Performance.query.get(perf_id)
    if not perf:
        return jsonify({"error": "Performance introuvable"}), 404
    perf.name = name
    perf.description = description
    db.session.commit()
    return jsonify({"message": "Performance mise à jour"}), 200

def delete_performance(perf_id):
    perf = Performance.query.get(perf_id)
    if not perf:
        return jsonify({"error": "Performance introuvable"}), 404
    db.session.delete(perf)
    db.session.commit()
    return jsonify({"message": "Performance supprimée"}), 200
