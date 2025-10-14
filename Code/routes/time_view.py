# Code/routes/time_view.py
from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
from sqlalchemy import text
from Code.extensions import db
from Code.models.models import (
    Activities, Task, Role, TimeAnalysis,
    TimeProject, TimeProjectLine, TimeWeakness,
    TimeRoleAnalysis, TimeRoleLine,
    activity_roles
)

time_bp = Blueprint('time_view', __name__, url_prefix='/temps')

# ---------- Helpers ----------
UNIT_TO_MIN = {'minutes': 1, 'heures': 60, 'jours': 1440}
def to_minutes(qty, unit):
    return float(qty or 0) * UNIT_TO_MIN.get((unit or 'minutes').lower(), 1)

def get_company_params():
    defaults = {'Js': 5, 'Sa': 47, 'Ja': 220}
    try:
        row = db.session.execute(text("SELECT Js, Sa, Ja FROM company_params LIMIT 1")).fetchone()
        if row:
            return {'Js': int(row[0] or 5), 'Sa': int(row[1] or 47), 'Ja': int(row[2] or 220)}
    except Exception:
        pass
    try:
        row = db.session.execute(text("""
            SELECT days_per_week, weeks_per_year, days_per_year
            FROM gestion_rh_params LIMIT 1
        """)).fetchone()
        if row:
            return {'Js': int(row[0] or 5), 'Sa': int(row[1] or 47), 'Ja': int(row[2] or 220)}
    except Exception:
        pass
    return defaults

def get_calendar_params():
    try:
        row = db.session.execute(text("""
            SELECT hours_per_day, days_per_week, weeks_per_year
            FROM enterprise_settings
            LIMIT 1
        """)).fetchone()
        if row:
            return {'hours_per_day': float(row[0] or 7),
                    'days_per_week': int(row[1] or 5),
                    'weeks_per_year': int(row[2] or 47)}
    except Exception:
        pass
    cp = get_company_params()
    return {'hours_per_day': 7.0, 'days_per_week': cp['Js'], 'weeks_per_year': cp['Sa']}

def activity_duration_minutes(activity_id):
    a = Activities.query.get(activity_id)
    return float(getattr(a, 'duration_minutes', 0) or 0)

def ensure_time_role_schema():
    """Auto-patch : ajoute les colonnes manquantes dans les tables rôle si nécessaire (SQLite)."""
    try:
        # time_role_analysis
        cols_ra = db.session.execute(text("PRAGMA table_info(time_role_analysis)")).fetchall()
        if cols_ra:
            names_ra = {c[1] for c in cols_ra}
            if 'name' not in names_ra:
                db.session.execute(text("ALTER TABLE time_role_analysis ADD COLUMN name TEXT DEFAULT 'Analyse rôle'"))
            if 'created_at' not in names_ra:
                db.session.execute(text("ALTER TABLE time_role_analysis ADD COLUMN created_at TEXT DEFAULT (datetime('now'))"))
        # time_role_line
        cols_rl = db.session.execute(text("PRAGMA table_info(time_role_line)")).fetchall()
        if cols_rl:
            names_rl = {c[1] for c in cols_rl}
            if 'duration_minutes' not in names_rl:
                db.session.execute(text("ALTER TABLE time_role_line ADD COLUMN duration_minutes REAL"))
        db.session.commit()
    except Exception:
        db.session.rollback()

# ---------- Page ----------
@time_bp.route('/', methods=['GET'])
def page():
    activities = Activities.query.order_by(Activities.name.asc()).all()
    roles = Role.query.order_by(Role.name.asc()).all()
    return render_template('time_dashboard.html', activities=activities, roles=roles)

@time_bp.route('/api/calendar_params', methods=['GET'])
def api_calendar_params():
    return jsonify({"ok": True, **get_calendar_params()})

# ---------- API: Defaults activité ----------
@time_bp.route('/api/activity_defaults/<int:activity_id>', methods=['GET'])
def api_activity_defaults(activity_id):
    a = Activities.query.get_or_404(activity_id)
    duration_min = getattr(a, 'duration_minutes', 0) or 0
    delay_min    = getattr(a, 'delay_minutes', 0) or 0
    tasks = Task.query.filter_by(activity_id=activity_id).order_by(Task.order.asc(), Task.id.asc()).all()
    return jsonify({
        "duration_minutes": float(duration_min),
        "delay_minutes": float(delay_min),
        "tasks": [{
            "id": t.id,
            "name": t.name,
            "duration_minutes": float(getattr(t, 'duration_minutes', 0) or 0),
            "delay_minutes":    float(getattr(t, 'delay_minutes', 0) or 0)
        } for t in tasks]
    })

# ---------- API: Saisie durée/délai directe ----------
@time_bp.route('/api/activity_time/<int:activity_id>', methods=['GET', 'POST', 'DELETE'])
def api_activity_time(activity_id):
    a = Activities.query.get_or_404(activity_id)

    if request.method == 'GET':
        tasks = Task.query.filter_by(activity_id=activity_id).order_by(Task.order.asc(), Task.id.asc()).all()
        sum_tasks = sum(float(t.duration_minutes or 0) for t in tasks)
        suggested_mode = 'tasks' if sum_tasks > 0 and abs(sum_tasks - (a.duration_minutes or 0)) < 0.001 else 'activity'
        return jsonify({
            "ok": True,
            "activity": {
                "id": a.id, "name": a.name,
                "duration_minutes": float(a.duration_minutes or 0),
                "delay_minutes": float(a.delay_minutes or 0)
            },
            "tasks": [{
                "id": t.id, "name": t.name,
                "duration_minutes": float(t.duration_minutes or 0),
                "delay_minutes": float(t.delay_minutes or 0)
            } for t in tasks],
            "mode": suggested_mode
        })

    if request.method == 'DELETE':
        a.duration_minutes = 0
        a.delay_minutes = 0
        Task.query.filter_by(activity_id=activity_id).update({
            Task.duration_minutes: 0,
            Task.delay_minutes: 0
        })
        db.session.commit()
        return jsonify({"ok": True, "reset": True})

    data = request.get_json(force=True) or {}
    mode = (data.get('mode') or 'activity').strip().lower()

    a.delay_minutes = to_minutes(data.get('delay', 0), data.get('delay_unit') or 'minutes')

    if mode == 'tasks':
        rows = data.get('tasks') or []
        total = 0.0
        for row in rows:
            tid = int(row['task_id'])
            dur_mn = to_minutes(row.get('duration', 0), row.get('duration_unit') or 'minutes')
            t = Task.query.get(tid)
            if t and t.activity_id == activity_id:
                t.duration_minutes = dur_mn
                if row.get('delay') is not None and row.get('delay_unit'):
                    t.delay_minutes = to_minutes(row.get('delay', 0), row.get('delay_unit') or 'minutes')
                total += dur_mn
        a.duration_minutes = total
    else:
        a.duration_minutes = to_minutes(data.get('duration', 0), data.get('duration_unit') or 'minutes')

    db.session.commit()
    return jsonify({"ok": True, "activity_id": a.id, "duration_minutes": float(a.duration_minutes or 0), "delay_minutes": float(a.delay_minutes or 0)})

# ========================= CHARGES : PROJET =========================
@time_bp.route('/api/project', methods=['POST'])
def api_project_create():
    data = request.get_json(force=True) or {}
    name = (data.get('name') or 'Projet sans titre').strip()
    lines = data.get('lines') or []

    proj = TimeProject(name=name, created_at=datetime.utcnow())
    db.session.add(proj)
    db.session.flush()

    for ln in lines:
        db.session.add(TimeProjectLine(
            project_id=proj.id,
            activity_id=int(ln['activity_id']),
            duration_minutes=to_minutes(ln.get('duration', 0), ln.get('duration_unit')),
            delay_minutes=to_minutes(ln.get('delay', 0), ln.get('delay_unit')),
            nb_people=int(ln.get('nb_people') or 1)
        ))
    db.session.commit()
    return jsonify({"ok": True, "project_id": proj.id})

@time_bp.route('/api/project/<int:project_id>', methods=['GET'])
def api_project_read(project_id):
    proj = TimeProject.query.get_or_404(project_id)
    rows, tot_nb, tot_dur, tot_charge, sum_delay = [], 0, 0.0, 0.0, 0.0
    for ln in proj.lines:
        charge = float(ln.duration_minutes) * max(1, ln.nb_people)
        rows.append({
            "id": ln.id,
            "activity_id": ln.activity_id,
            "activity": Activities.query.get(ln.activity_id).name if ln.activity_id else "",
            "duration_minutes": float(ln.duration_minutes),
            "delay_minutes": float(ln.delay_minutes),
            "nb_people": ln.nb_people,
            "charge": charge
        })
        tot_nb += 1
        tot_dur += float(ln.duration_minutes)
        sum_delay += float(ln.delay_minutes)
        tot_charge += charge
    avg_delay = (sum_delay / tot_nb) if tot_nb else 0.0
    return jsonify({
        "ok": True,
        "project": {"id": proj.id, "name": proj.name, "created_at": proj.created_at.isoformat() },
        "lines": rows,
        "summary": {
            "nb_activites": tot_nb,
            "tot_duree_minutes": tot_dur,
            "delais_optimum_minutes": avg_delay,
            "charge_globale_minutes": tot_charge
        }
    })

@time_bp.route('/api/projects', methods=['GET'])
def api_projects_list():
    projs = TimeProject.query.order_by(TimeProject.created_at.desc(), TimeProject.id.desc()).all()
    out = []
    for p in projs:
        nb = len(p.lines)
        tot_dur = sum(float(x.duration_minutes) for x in p.lines)
        sum_delay = sum(float(x.delay_minutes) for x in p.lines)
        tot_charge = sum(float(x.duration_minutes) * max(1, x.nb_people) for x in p.lines)
        avg_delay = (sum_delay / nb) if nb else 0.0
        out.append({
            "id": p.id, "name": p.name, "created_at": p.created_at.isoformat(),
            "nb_activites": nb, "tot_duree_minutes": tot_dur,
            "delais_optimum_minutes": avg_delay, "charge_globale_minutes": tot_charge
        })
    return jsonify({"ok": True, "projects": out})

@time_bp.route('/api/project/<int:project_id>', methods=['PATCH', 'DELETE'])
def api_project_update_delete(project_id):
    proj = TimeProject.query.get_or_404(project_id)
    if request.method == 'PATCH':
        data = request.get_json(force=True) or {}
        new_name = (data.get('name') or '').strip()
        if new_name:
            proj.name = new_name
            db.session.commit()
        return jsonify({"ok": True, "id": proj.id, "name": proj.name})
    else:
        db.session.delete(proj)
        db.session.commit()
        return jsonify({"ok": True, "deleted": True})

@time_bp.route('/api/project_line/<int:line_id>', methods=['DELETE'])
def api_project_line_delete(line_id):
    ln = TimeProjectLine.query.get_or_404(line_id)
    proj_id = ln.project_id
    db.session.delete(ln)
    db.session.flush()
    remaining = TimeProjectLine.query.filter_by(project_id=proj_id).count()
    project_deleted = False
    if remaining == 0:
        proj = TimeProject.query.get(proj_id)
        if proj:
            db.session.delete(proj)
            project_deleted = True
    db.session.commit()
    return jsonify({"ok": True, "project_deleted": project_deleted, "project_id": proj_id})

# ========================= CHARGES : ACTIVITE =========================
@time_bp.route('/api/activity_workload', methods=['POST'])
def api_activity_workload():
    d = request.get_json(force=True) or {}
    ta = TimeAnalysis(
        type='activity',
        activity_id=int(d['activity_id']),
        duration=int(round(to_minutes(d.get('duration', 0), d.get('duration_unit')))),
        recurrence=(d.get('recurrence') or 'journalier').strip().lower(),
        frequency=int(d.get('frequency') or 1),
        nb_people=int(d.get('nb_people') or 1),
        delay=None,
        delay_increase=None,
        impact_unit='minutes'
    )
    db.session.add(ta)
    db.session.commit()
    total = float(ta.duration) * max(1, ta.frequency) * max(1, ta.nb_people)
    return jsonify({"ok": True, "id": ta.id, "total_minutes": total})

@time_bp.route('/api/activity_workload/<int:wk_id>', methods=['PATCH'])
def api_activity_workload_update(wk_id):
    x = TimeAnalysis.query.get_or_404(wk_id)
    if x.type != 'activity':
        return jsonify({"ok": False, "error": "bad_type"}), 400
    d = request.get_json(force=True) or {}
    if d.get('activity_id') is not None: x.activity_id = int(d['activity_id'])
    if d.get('duration') is not None and d.get('duration_unit'):
        x.duration = int(round(to_minutes(d['duration'], d['duration_unit'])))
    if d.get('recurrence') is not None: x.recurrence = (d['recurrence'] or '').strip().lower()
    if d.get('frequency') is not None: x.frequency = int(d['frequency'])
    if d.get('nb_people') is not None: x.nb_people = int(d['nb_people'])
    db.session.commit()
    total = float(x.duration or 0) * max(1, x.frequency or 1) * max(1, x.nb_people or 1)
    return jsonify({"ok": True, "id": x.id, "total_minutes": total})

@time_bp.route('/api/activity_workload/<int:wk_id>', methods=['DELETE'])
def api_activity_workload_delete(wk_id):
    x = TimeAnalysis.query.get_or_404(wk_id)
    if x.type != 'activity':
        return jsonify({"ok": False, "error": "bad_type"}), 400
    db.session.delete(x)
    db.session.commit()
    return jsonify({"ok": True, "deleted": True})

@time_bp.route('/api/activity_workloads', methods=['GET'])
def api_activity_workloads_list():
    items = (TimeAnalysis.query
             .filter_by(type='activity')
             .order_by(TimeAnalysis.id.desc())
             .all())
    out = []
    for x in items:
        act = Activities.query.get(x.activity_id)
        total = float(x.duration or 0) * max(1, x.frequency or 1) * max(1, x.nb_people or 1)
        out.append({
            "id": x.id,
            "activity_id": x.activity_id,
            "activity": act.name if act else "",
            "duration_minutes": float(x.duration or 0),
            "recurrence": x.recurrence,
            "frequency": int(x.frequency or 1),
            "nb_people": int(x.nb_people or 1),
            "total_minutes": total
        })
    return jsonify({"ok": True, "items": out})

@time_bp.route('/api/activity_workload/<int:wk_id>', methods=['GET'])
def api_activity_workload_read(wk_id):
    x = TimeAnalysis.query.get_or_404(wk_id)
    act = Activities.query.get(x.activity_id)
    total = float(x.duration or 0) * max(1, x.frequency or 1) * max(1, x.nb_people or 1)
    return jsonify({
        "ok": True,
        "item": {
            "id": x.id,
            "activity_id": x.activity_id,
            "activity": act.name if act else "",
            "duration_minutes": float(x.duration or 0),
            "recurrence": x.recurrence,
            "frequency": int(x.frequency or 1),
            "nb_people": int(x.nb_people or 1),
            "total_minutes": total
        }
    })

# ========================= CHARGES : PAR RÔLE =========================
@time_bp.route('/api/role_activities/<int:role_id>', methods=['GET'])
def api_role_activities(role_id):
    qs = (Activities.query
          .join(activity_roles, Activities.id == activity_roles.c.activity_id)
          .filter(activity_roles.c.role_id == role_id)
          .order_by(Activities.name.asc()))
    items = [{"id": a.id, "name": a.name} for a in qs.all()]
    return jsonify({"ok": True, "activities": items})

@time_bp.route('/api/role_analysis', methods=['POST'])
def api_role_analysis_create():
    ensure_time_role_schema()
    d = request.get_json(force=True) or {}
    R = TimeRoleAnalysis(
        role_id=int(d['role_id']),
        name=(d.get('name') or 'Analyse rôle').strip(),
        created_at=datetime.utcnow()
    )
    db.session.add(R)
    db.session.flush()
    for ln in (d.get('lines') or []):
        db.session.add(TimeRoleLine(
            role_analysis_id=R.id,
            activity_id=int(ln['activity_id']),
            recurrence=(ln.get('recurrence') or 'journalier').strip().lower(),
            frequency=int(ln.get('frequency') or 1),
            duration_minutes=float(ln.get('duration') or 0)
        ))
    db.session.commit()
    return jsonify({"ok": True, "id": R.id})

def _line_duration(l):
    if getattr(l, 'duration_minutes', None):
        return float(l.duration_minutes or 0)
    return activity_duration_minutes(l.activity_id)

def _role_summary(R):
    sum_day = sum(_line_duration(l) * max(1, l.frequency) for l in R.lines if l.recurrence.startswith('jour'))
    sum_week = sum(_line_duration(l) * max(1, l.frequency) for l in R.lines if l.recurrence.startswith('hebdo'))
    sum_month = sum(_line_duration(l) * max(1, l.frequency) for l in R.lines if l.recurrence.startswith('mens'))
    sum_year = sum(_line_duration(l) * max(1, l.frequency) for l in R.lines if l.recurrence.startswith('ann'))

    p = get_calendar_params()
    dpw, wpy = p['days_per_week'], p['weeks_per_year']
    annual = sum_day * (dpw * wpy) + sum_week * wpy + sum_month * 12 + sum_year
    monthly = sum_day * (dpw * wpy / 12.0) + sum_week * (wpy / 12.0) + sum_month + sum_year / 12.0

    return {
        "sum_daily_minutes": float(sum_day),
        "sum_weekly_minutes": float(sum_week),
        "sum_monthly_minutes": float(sum_month),
        "sum_yearly_minutes": float(sum_year),
        "annual_minutes": float(annual),
        "monthly_minutes": float(monthly),
        "calendar": p
    }

@time_bp.route('/api/role_analysis/<int:rid>', methods=['GET', 'PATCH', 'DELETE'])
def api_role_analysis_read_patch_delete(rid):
    ensure_time_role_schema()
    R = TimeRoleAnalysis.query.get_or_404(rid)
    if request.method == 'PATCH':
        data = request.get_json(force=True) or {}
        new_name = (data.get('name') or '').strip()
        if new_name:
            R.name = new_name
            db.session.commit()
        return jsonify({"ok": True, "id": R.id, "name": R.name})
    if request.method == 'DELETE':
        db.session.delete(R)
        db.session.commit()
        return jsonify({"ok": True, "deleted": True})

    rows = []
    for ln in R.lines:
        dur = _line_duration(ln)
        rows.append({
            "id": ln.id,
            "activity_id": ln.activity_id,
            "activity": Activities.query.get(ln.activity_id).name if ln.activity_id else "",
            "duration_minutes": float(dur),
            "recurrence": ln.recurrence,
            "frequency": ln.frequency,
            "weight_minutes": float(dur) * max(1, ln.frequency)
        })
    return jsonify({
        "ok": True,
        "role": {"id": R.id, "role_id": R.role_id, "name": R.name, "created_at": R.created_at.isoformat() if hasattr(R, "created_at") and R.created_at else None},
        "lines": rows,
        "summary": _role_summary(R)
    })

@time_bp.route('/api/role_analyses', methods=['GET'])
def api_role_analyses_list():
    ensure_time_role_schema()
    Rs = TimeRoleAnalysis.query.order_by(TimeRoleAnalysis.created_at.desc(), TimeRoleAnalysis.id.desc()).all()
    out = []
    for R in Rs:
        s = _role_summary(R)
        out.append({
            "id": R.id,
            "role_id": R.role_id,
            "role": Role.query.get(R.role_id).name if R.role_id else "",
            "name": getattr(R, "name", "Analyse rôle"),
            "created_at": R.created_at.isoformat() if hasattr(R, "created_at") and R.created_at else None,
            **s
        })
    return jsonify({"ok": True, "items": out})

@time_bp.route('/api/role_line/<int:line_id>', methods=['DELETE'])
def api_role_line_delete(line_id):
    ensure_time_role_schema()
    ln = TimeRoleLine.query.get_or_404(line_id)
    rid = ln.role_analysis_id
    db.session.delete(ln)
    db.session.flush()
    remaining = TimeRoleLine.query.filter_by(role_analysis_id=rid).count()
    deleted = False
    if remaining == 0:
        R = TimeRoleAnalysis.query.get(rid)
        if R:
            db.session.delete(R)
            deleted = True
    db.session.commit()
    return jsonify({"ok": True, "analysis_deleted": deleted, "analysis_id": rid})

# ========================= FAIBLESSE =========================
@time_bp.route('/api/weakness', methods=['POST'])
def api_weakness():
    d = request.get_json(force=True) or {}
    mode = (d.get('mode') or 'activity').strip().lower()
    activity_id = int(d.get('activity_id'))
    rec = (d.get('recurrence') or 'journalier').strip().lower()
    freq = int(d.get('frequency') or 1)
    weakness_txt = (d.get('weakness') or '').strip()
    save = bool(d.get('save'))

    L_qty = to_minutes(d.get('L_work_added', 0), d.get('L_unit') or 'minutes')
    M_qty = to_minutes(d.get('M_wait_added', 0), d.get('M_unit') or 'minutes')
    N_denom = max(1, int(d.get('N_prob_denom') or 1))

    C = to_minutes(d.get('delay_std', 0), d.get('delay_unit') or 'minutes')

    tasks_payload = d.get('tasks') or []
    if mode == 'tasks':
        B = sum(to_minutes(t.get('duration_std', 0), t.get('duration_unit') or 'minutes') for t in tasks_payload)
    else:
        B = to_minutes(d.get('duration_std', 0), d.get('duration_unit') or 'minutes')

    params = get_calendar_params()
    Js, Sa = params['days_per_week'], params['weeks_per_year']
    WPM = 4.34524
    WPA = 52.1429

    if rec.startswith('jour'):
        H = Js * Sa
    elif rec.startswith('hebdo'):
        H = Sa
    elif rec.startswith('mens'):
        H = Sa / WPM
    else:
        H = Sa / WPA

    O = 1.0 / N_denom
    P = H * O
    Q = L_qty * O
    Rv = (L_qty + M_qty) * O
    S = B + Q
    T = C + Rv
    U = L_qty * P
    V = (L_qty + M_qty) * P
    W = U / (Sa / WPM) if (Sa / WPM) else 0
    X = V / (Sa / WPM) if (Sa / WPM) else 0
    Y = C + M_qty
    Z = M_qty
    AA = P

    if save:
        if mode == 'tasks' and tasks_payload:
            for t in tasks_payload:
                dur_task = to_minutes(t.get('duration_std', 0), t.get('duration_unit') or 'minutes')
                del_task = to_minutes(t.get('delay_std', 0), t.get('delay_unit') or 'minutes') if t.get('delay_std') is not None else 0
                db.session.add(TimeWeakness(
                    activity_id=activity_id, task_id=int(t.get('task_id')),
                    duration_std_minutes=dur_task, delay_std_minutes=del_task or 0,
                    recurrence=rec, frequency=freq, weakness=weakness_txt,
                    work_added_qty=L_qty, work_added_unit='minutes',
                    wait_added_qty=M_qty, wait_added_unit='minutes',
                    prob_denom=N_denom, created_at=datetime.utcnow()
                ))
            db.session.add(TimeWeakness(
                activity_id=activity_id, task_id=None,
                duration_std_minutes=B, delay_std_minutes=C,
                recurrence=rec, frequency=freq, weakness=weakness_txt,
                work_added_qty=L_qty, work_added_unit='minutes',
                wait_added_qty=M_qty, wait_added_unit='minutes',
                prob_denom=N_denom, created_at=datetime.utcnow()
            ))
        else:
            db.session.add(TimeWeakness(
                activity_id=activity_id, task_id=None,
                duration_std_minutes=B, delay_std_minutes=C,
                recurrence=rec, frequency=freq, weakness=weakness_txt,
                work_added_qty=L_qty, work_added_unit='minutes',
                wait_added_qty=M_qty, wait_added_unit='minutes',
                prob_denom=N_denom, created_at=datetime.utcnow()
            ))
        db.session.commit()

    return jsonify({
        "ok": True,
        "mode": mode,
        "activity_id": activity_id,
        "calc": {"O": O, "P": P, "Q": Q, "R": Rv, "S": S, "T": T, "U": U, "V": V, "W": W, "X": X, "Y": Y, "Z": Z, "AA": AA},
        "B_minutes": B, "C_minutes": C,
        "params": get_calendar_params()
    })
