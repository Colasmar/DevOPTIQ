# Code/routes/plan_storage.py
from flask import Blueprint, request, jsonify
from sqlalchemy import text
from datetime import datetime
import json

from Code.extensions import db

plan_storage_bp = Blueprint("plan_storage_bp", __name__, url_prefix="/competences_plan")

def _now_iso():
    return datetime.utcnow().isoformat(timespec="seconds")

@plan_storage_bp.route("/save_plan", methods=["POST"])
def save_plan():
    """
    JSON attendu:
    {
      "user_id": int,
      "activity_id": int,
      "role_id": int | null,
      "plan": {...},           # objet JSON
      "force": true|false      # optionnel; si False et plan déjà existant => 409
    }
    """
    data = request.get_json(silent=True) or {}
    user_id     = data.get("user_id")
    activity_id = data.get("activity_id")
    role_id     = data.get("role_id")
    plan        = data.get("plan")
    force       = bool(data.get("force", False))

    if not user_id or not activity_id or plan is None:
        return jsonify({"ok": False, "error": "Paramètres manquants."}), 400

    # Vérifier existence
    sql_exist = text("""
        SELECT id FROM user_activity_plans
        WHERE user_id = :uid AND activity_id = :aid
        LIMIT 1
    """)
    row = db.session.execute(sql_exist, {"uid": user_id, "aid": activity_id}).fetchone()

    now = _now_iso()
    plan_json = json.dumps(plan, ensure_ascii=False)

    try:
        if row:
            if not force:
                # Prévenir côté front qu'un plan existe déjà
                return jsonify({"ok": False, "exists": True, "message": "Plan déjà enregistré pour cette activité."}), 409
            # Remplacement
            sql_upd = text("""
                UPDATE user_activity_plans
                SET content = :content, role_id = :rid, updated_at = :now
                WHERE id = :pid
            """)
            db.session.execute(sql_upd, {"content": plan_json, "rid": role_id, "now": now, "pid": row[0]})
            db.session.commit()
            return jsonify({"ok": True, "replaced": True, "plan_id": row[0]})
        else:
            # Insertion
            sql_ins = text("""
                INSERT INTO user_activity_plans (user_id, activity_id, role_id, content, created_at, updated_at)
                VALUES (:uid, :aid, :rid, :content, :now, :now)
            """)
            cur = db.session.execute(sql_ins, {"uid": user_id, "aid": activity_id, "rid": role_id, "content": plan_json, "now": now})
            db.session.commit()
            new_id = cur.lastrowid
            return jsonify({"ok": True, "created": True, "plan_id": new_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@plan_storage_bp.route("/get_plan/<int:user_id>/<int:activity_id>", methods=["GET"])
def get_plan(user_id, activity_id):
    """
    Récupère le plan enregistré pour (user_id, activity_id)
    """
    sql = text("""
        SELECT content, role_id, updated_at, created_at
        FROM user_activity_plans
        WHERE user_id = :uid AND activity_id = :aid
        LIMIT 1
    """)
    row = db.session.execute(sql, {"uid": user_id, "aid": activity_id}).fetchone()
    if not row:
        return jsonify({"ok": False, "error": "Aucun plan enregistré."}), 404

    try:
        content = json.loads(row[0])
    except Exception:
        content = None

    return jsonify({
        "ok": True,
        "plan": content,
        "meta": {
            "role_id": row[1],
            "updated_at": row[2],
            "created_at": row[3],
        }
    })
