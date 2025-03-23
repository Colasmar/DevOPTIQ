import re
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from Code.extensions import db
from Code.models.models import Softskill

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
    Compare les niveaux pour éviter d'enregistrer un niveau plus bas que l'existant.
    Ex: si "2 (acquisition)" est déjà stocké et on reçoit "1 (aptitude)", on ne remplace pas.
    """
    data = request.get_json() or {}
    activity_id = data.get("activity_id")
    habilete = data.get("habilete", "").strip()
    niveau_str = data.get("niveau", "").strip()       # ex: "2 (acquisition)"
    justification = data.get("justification", "").strip()

    if not activity_id or not habilete or not niveau_str:
        return jsonify({"error": "activity_id, habilete and niveau are required"}), 400

    # On extrait la première occurrence de chiffre (1..4) dans niveau_str
    new_level_int = 0
    match_new = re.search(r"(\d)", niveau_str)
    if match_new:
        new_level_int = int(match_new.group(1))  # ex: "2 (acquisition)" => 2

    # Chercher s'il existe déjà une HSC de même nom (insensible à la casse)
    existing = Softskill.query.filter(
        func.lower(Softskill.habilete) == habilete.lower(),
        Softskill.activity_id == activity_id
    ).first()

    try:
        if existing:
            # On récupère l'ancien niveau (chiffre) de la HSC
            old_level_int = 0
            match_old = re.search(r"(\d)", existing.niveau or "")
            if match_old:
                old_level_int = int(match_old.group(1))

            # On met à jour la HSC :
            # Le nom et le niveau sont mis à jour systématiquement
            existing.habilete = habilete
            existing.niveau = niveau_str  # On stocke toujours la chaîne entière
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
                niveau=niveau_str,          # on stocke la chaîne entière
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
    
    Logique :
    - Le nom (habilete) et la justification sont toujours mis à jour si fournis.
    - Le niveau est mis à jour quelle que soit la modification.
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
        # Mise à jour du nom (habilete) systématique
        ss.habilete = new_habilete

        # Mise à jour de la justification si fournie
        if new_justification:
            ss.justification = new_justification

        # Mise à jour du niveau : on le met à jour quelle que soit la modification
        ss.niveau = new_niveau_str

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

