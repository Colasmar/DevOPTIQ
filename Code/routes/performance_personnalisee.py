# Code/routes/performance_personnalisee.py
from flask import Blueprint, request, jsonify
from datetime import datetime
from sqlalchemy import text
from Code.extensions import db
from Code.models.models import PerformancePersonnalisee

performance_perso_bp = Blueprint('performance_perso', __name__, url_prefix='/performance_perso')

def iso_today():
    return datetime.utcnow().strftime('%Y-%m-%d')

def to_dict(p: PerformancePersonnalisee):
    def _ts(x):
        try:
            return x.isoformat()
        except Exception:
            return x
    return {
        "id": p.id,
        "user_id": p.user_id,
        "activity_id": p.activity_id,
        "content": p.content or "",
        "validation_status": p.validation_status,
        "validation_date": p.validation_date,
        "created_at": _ts(p.created_at),
        "updated_at": _ts(p.updated_at),
        "deleted": bool(getattr(p, "deleted", False)),
    }

# ---------- Utils SQL robustes ----------
def insert_history_row(perf: PerformancePersonnalisee):
    """
    Insère une ligne d'historique en s'adaptant au schéma existant :
    - essaie avec (performance_id, user_id, activity_id, contenu, validation_status, validation_date, changed_at)
    - sinon retente avec content au lieu de contenu
    - sinon insère a minima (performance_id, contenu/content, changed_at)
    """
    base_params = {
        "performance_id": perf.id,
        "user_id": perf.user_id,
        "activity_id": perf.activity_id,
        "contenu": perf.content or "",
        "validation_status": perf.validation_status,
        "validation_date": perf.validation_date,
    }

    try:
        db.session.execute(
            text("""
                INSERT INTO performance_personnalisee_historique
                    (performance_id, user_id, activity_id, contenu, validation_status, validation_date, changed_at)
                VALUES
                    (:performance_id, :user_id, :activity_id, :contenu, :validation_status, :validation_date, datetime('now'))
            """),
            base_params
        )
        return
    except Exception:
        db.session.rollback()

    try:
        db.session.execute(
            text("""
                INSERT INTO performance_personnalisee_historique
                    (performance_id, user_id, activity_id, content, validation_status, validation_date, changed_at)
                VALUES
                    (:performance_id, :user_id, :activity_id, :contenu, :validation_status, :validation_date, datetime('now'))
            """),
            base_params
        )
        return
    except Exception:
        db.session.rollback()

    # Fallback minimal : pas de user_id/activity_id/validation_* dans la table
    try:
        db.session.execute(
            text("""
                INSERT INTO performance_personnalisee_historique
                    (performance_id, contenu, changed_at)
                VALUES
                    (:performance_id, :contenu, datetime('now'))
            """),
            base_params
        )
    except Exception:
        db.session.rollback()
        # Dernier essai avec 'content'
        db.session.execute(
            text("""
                INSERT INTO performance_personnalisee_historique
                    (performance_id, content, changed_at)
                VALUES
                    (:performance_id, :contenu, datetime('now'))
            """),
            base_params
        )

# ---------- Endpoints ----------
@performance_perso_bp.route('/list', methods=['GET'])
def list_perf():
    user_id = request.args.get('user_id', type=int)
    activity_id = request.args.get('activity_id', type=int)
    q = PerformancePersonnalisee.query
    if user_id:
        q = q.filter(PerformancePersonnalisee.user_id == user_id)
    if activity_id:
        q = q.filter(PerformancePersonnalisee.activity_id == activity_id)
    try:
        q = q.filter((PerformancePersonnalisee.deleted == False) | (PerformancePersonnalisee.deleted.is_(None)))
    except Exception:
        pass
    items = q.order_by(PerformancePersonnalisee.id.asc()).all()
    return jsonify([to_dict(p) for p in items])

@performance_perso_bp.route('/create', methods=['POST'])
def create_perf():
    data = request.get_json(force=True) or {}
    user_id = int(data.get('user_id'))
    activity_id = int(data.get('activity_id'))
    # compat "contenu" / "content"
    content = (data.get('content') or data.get('contenu') or '').strip()
    validation_status = (data.get('validation_status') or 'non-validee').strip()
    validation_date = (data.get('validation_date') or iso_today()).strip()

    if not user_id or not activity_id:
        return jsonify({"ok": False, "error": "user_id et activity_id requis"}), 400
    if not content:
        return jsonify({"ok": False, "error": "content requis"}), 400
    if validation_status not in ('validee', 'non-validee'):
        return jsonify({"ok": False, "error": "validation_status invalide"}), 400

    p = PerformancePersonnalisee(
        user_id=user_id,
        activity_id=activity_id,
        content=content,
        validation_status=validation_status,
        validation_date=validation_date,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )
    db.session.add(p)
    db.session.flush()  # p.id

    # Historiser état initial
    insert_history_row(p)

    db.session.commit()
    return jsonify({"ok": True, "item": to_dict(p)})

@performance_perso_bp.route('/update/<int:perf_id>', methods=['PUT'])
def update_perf(perf_id):
    p = PerformancePersonnalisee.query.get_or_404(perf_id)
    data = request.get_json(force=True) or {}

    old_content = p.content
    old_status = p.validation_status
    old_date = p.validation_date

    # compat
    if 'contenu' in data and 'content' not in data:
        data['content'] = data['contenu']

    if 'content' in data:
        p.content = (data['content'] or '').strip()

    status_changed = False
    if 'validation_status' in data:
        val = data['validation_status']
        if val not in ('validee', 'non-validee'):
            return jsonify({"ok": False, "error": "validation_status invalide"}), 400
        if val != p.validation_status:
            p.validation_status = val
            status_changed = True

    if 'validation_date' in data:
        p.validation_date = data['validation_date'] or None
    elif status_changed:
        p.validation_date = iso_today()

    p.updated_at = datetime.utcnow().isoformat()
    db.session.flush()

    # Historiser si nécessaire
    if (p.content != old_content) or status_changed or (p.validation_date != old_date):
        insert_history_row(p)

    db.session.commit()
    return jsonify({"ok": True, "item": to_dict(p)})

@performance_perso_bp.route('/history', methods=['GET'])
def history():
    """
    Récupère l'historique pour un couple (user_id, activity_id) en JOIN-ant
    la table principale (pas besoin de colonnes user_id/activity_id dans l'historique).
    Gère 'contenu' OU 'content' et la présence/absence de validation_*.
    """
    user_id = request.args.get('user_id', type=int)
    activity_id = request.args.get('activity_id', type=int)
    if not user_id or not activity_id:
        return jsonify({"ok": False, "error": "user_id et activity_id requis"}), 400

    queries = [
        # 1) 'contenu' + validation_*
        """
        SELECT h.performance_id, p.user_id, p.activity_id,
               h.contenu AS contenu, h.validation_status, h.validation_date, h.changed_at
        FROM performance_personnalisee_historique h
        JOIN performance_personnalisee p ON p.id = h.performance_id
        WHERE p.user_id = :user_id AND p.activity_id = :activity_id
        ORDER BY h.changed_at DESC
        """,
        # 2) 'content' + validation_*
        """
        SELECT h.performance_id, p.user_id, p.activity_id,
               h.content AS contenu, h.validation_status, h.validation_date, h.changed_at
        FROM performance_personnalisee_historique h
        JOIN performance_personnalisee p ON p.id = h.performance_id
        WHERE p.user_id = :user_id AND p.activity_id = :activity_id
        ORDER BY h.changed_at DESC
        """,
        # 3) 'content' sans validation_*
        """
        SELECT h.performance_id, p.user_id, p.activity_id,
               h.content AS contenu, NULL AS validation_status, NULL AS validation_date, h.changed_at
        FROM performance_personnalisee_historique h
        JOIN performance_personnalisee p ON p.id = h.performance_id
        WHERE p.user_id = :user_id AND p.activity_id = :activity_id
        ORDER BY h.changed_at DESC
        """,
        # 4) 'contenu' sans validation_*
        """
        SELECT h.performance_id, p.user_id, p.activity_id,
               h.contenu AS contenu, NULL AS validation_status, NULL AS validation_date, h.changed_at
        FROM performance_personnalisee_historique h
        JOIN performance_personnalisee p ON p.id = h.performance_id
        WHERE p.user_id = :user_id AND p.activity_id = :activity_id
        ORDER BY h.changed_at DESC
        """
    ]

    rows = None
    last_err = None
    for sql in queries:
        try:
            rows = db.session.execute(text(sql), {"user_id": user_id, "activity_id": activity_id}).mappings().all()
            break
        except Exception as e:
            last_err = e
            db.session.rollback()

    if rows is None:
        return jsonify({"ok": False, "error": str(last_err)}), 500

    return jsonify({"ok": True, "history": [dict(r) for r in rows]})
