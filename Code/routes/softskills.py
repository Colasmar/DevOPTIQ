import re
from flask import Blueprint, request, jsonify, render_template
from sqlalchemy import func
from Code.extensions import db
from Code.models.models import Softskill, Activities

softskills_crud_bp = Blueprint('softskills_crud_bp', __name__, url_prefix='/softskills')


@softskills_crud_bp.route('/add', methods=['POST'])
def add_softskill():
    """
    Ajoute ou met à jour une softskill (HSC).
    JSON attendu : {
      "activity_id": <int>,
      "habilete": <str>,
      "niveau": <str> ex: "2 (acquisition)",
      "justification": <str> (optionnel)
    }
    Compare les niveaux pour éviter d'enregistrer un niveau plus bas (ceci a été simplifié).
    """
    data = request.get_json() or {}
    activity_id = data.get("activity_id")
    habilete = data.get("habilete", "").strip()
    niveau_str = data.get("niveau", "").strip()
    justification = data.get("justification", "").strip()

    if not activity_id or not habilete or not niveau_str:
        return jsonify({"error": "activity_id, habilete and niveau are required"}), 400

    # Chercher s'il existe déjà une HSC de même nom (insensible à la casse) sur la même activité
    existing = Softskill.query.filter(
        func.lower(Softskill.habilete) == habilete.lower(),
        Softskill.activity_id == activity_id
    ).first()

    try:
        if existing:
            # On écrase le niveau et la justification
            existing.habilete = habilete
            existing.niveau = niveau_str
            if justification:
                existing.justification = justification
            db.session.commit()
            return jsonify({
                "id": existing.id,
                "activity_id": existing.activity_id,
                "habilete": existing.habilete,
                "niveau": existing.niveau,
                "justification": existing.justification or ""
            }), 200
        else:
            # Nouvelle HSC
            new_softskill = Softskill(
                activity_id=activity_id,
                habilete=habilete,
                niveau=niveau_str,
                justification=justification
            )
            db.session.add(new_softskill)
            db.session.commit()
            return jsonify({
                "id": new_softskill.id,
                "activity_id": new_softskill.activity_id,
                "habilete": new_softskill.habilete,
                "niveau": new_softskill.niveau,
                "justification": new_softskill.justification or ""
            }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@softskills_crud_bp.route('/<int:softskill_id>', methods=['PUT'])
def update_softskill(softskill_id):
    """
    Met à jour une softskill existante.
    JSON attendu : {
      "habilete": <str>,
      "niveau": <str> ex: "2 (acquisition)",
      "justification": <str> (optionnel)
    }
    """
    data = request.get_json() or {}
    new_habilete = data.get("habilete", "").strip()
    new_niveau_str = data.get("niveau", "").strip()
    new_justification = data.get("justification", "").strip()

    if not new_habilete or not new_niveau_str:
        return jsonify({"error": "habilete and niveau are required"}), 400

    ss = Softskill.query.get(softskill_id)
    if not ss:
        return jsonify({"error": "Softskill not found"}), 404

    try:
        ss.habilete = new_habilete
        ss.niveau = new_niveau_str
        if new_justification:
            ss.justification = new_justification
        db.session.commit()
        return jsonify({
            "id": ss.id,
            "habilete": ss.habilete,
            "niveau": ss.niveau,
            "justification": ss.justification or ""
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@softskills_crud_bp.route('/<int:softskill_id>', methods=['DELETE'])
def delete_softskill(softskill_id):
    """
    Supprime une softskill existante.
    """
    ss = Softskill.query.get(softskill_id)
    if not ss:
        return jsonify({"error": "Softskill not found"}), 404
    try:
        db.session.delete(ss)
        db.session.commit()
        return jsonify({"message": "Softskill deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ============== NOUVELLE ROUTE DE RENDU PARTIEL ==============
@softskills_crud_bp.route('/<int:activity_id>/render', methods=['GET'])
def render_softskills_partial(activity_id):
    """
    Retourne le bloc HTML (partial) listant les HSC de l'activité,
    pour un rafraîchissement dynamique (même principe que Savoirs/Savoir-Faire).
    """
    activity = Activities.query.get(activity_id)
    if not activity:
        return jsonify({"error": "Activité non trouvée"}), 404
    return render_template("softskills_partial.html", activity=activity)
