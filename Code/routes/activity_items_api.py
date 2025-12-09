# Code/routes/activity_items_api.py
from flask import Blueprint, jsonify
from sqlalchemy import text
from Code.extensions import db

# URL de base conservée pour ne pas toucher au JS
activity_items_api_bp = Blueprint("activity_items_api", __name__, url_prefix="/your_api")

@activity_items_api_bp.route("/activity_items/<int:activity_id>")
def activity_items(activity_id: int):
    """
    Retourne les items liés à l’activité via activity_id (pas de tables d’association).
    Schéma BDD observé :
      - savoirs(id, description, activity_id)
      - savoir_faires(id, description, activity_id)
      - softskills(id, habilete, niveau, activity_id)
    """

    # Savoirs
    savoirs = db.session.execute(text("""
        SELECT id, description AS name
        FROM savoirs
        WHERE activity_id = :aid
        ORDER BY id
    """), {"aid": activity_id}).mappings().all()

    # Savoir-faire
    sfs = db.session.execute(text("""
        SELECT id, description AS name
        FROM savoir_faires
        WHERE activity_id = :aid
        ORDER BY id
    """), {"aid": activity_id}).mappings().all()

    # HSC (softskills) — on compose un libellé lisible "Habilete (Niveau)"
    hsc = db.session.execute(text("""
        SELECT id,
               CASE
                 WHEN niveau IS NOT NULL AND TRIM(niveau) <> '' THEN habilete || ' (' || niveau || ')'
                 ELSE habilete
               END AS name
        FROM softskills
        WHERE activity_id = :aid
        ORDER BY id
    """), {"aid": activity_id}).mappings().all()

    return jsonify({
        "savoirs":       [dict(r) for r in savoirs],
        "savoir_faire":  [dict(r) for r in sfs],
        "hsc":           [dict(r) for r in hsc],
    })
