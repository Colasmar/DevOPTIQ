# FICHIER: Code/routes/competences.py

from flask import Blueprint, jsonify, render_template, request
from Code.extensions import db
from datetime import datetime
from Code.models.models import (
    Competency, Role, Activities, User, UserRole,
    CompetencyEvaluation, Savoir, SavoirFaire, Aptitude, Softskill, activity_roles, PerformancePersonnalisee
)

competences_bp = Blueprint('competences_bp', __name__, url_prefix='/competences')

@competences_bp.route('/view', methods=['GET'])
def competences_view():
    return render_template('competences_view.html')


@competences_bp.route('/managers', methods=['GET'])
def get_managers():
    role_manager = Role.query.filter_by(name='manager').first()
    if not role_manager:
        return jsonify([])
    managers = User.query.join(UserRole).filter(UserRole.role_id == role_manager.id).all()
    return jsonify([{'id': m.id, 'name': f"{m.first_name} {m.last_name}"} for m in managers])

@competences_bp.route('/collaborators/<int:manager_id>', methods=['GET'])
def get_collaborators(manager_id):
    collaborateurs = User.query.filter_by(manager_id=manager_id).all()
    return jsonify([{'id': u.id, 'first_name': u.first_name, 'last_name': u.last_name} for u in collaborateurs])

@competences_bp.route('/get_user_roles/<int:user_id>', methods=['GET'])
def get_user_roles(user_id):
    user_roles = UserRole.query.filter_by(user_id=user_id).all()
    roles = [Role.query.get(ur.role_id) for ur in user_roles if Role.query.get(ur.role_id)]
    return jsonify({'roles': [{'id': r.id, 'name': r.name} for r in roles]})

@competences_bp.route('/save_user_evaluations', methods=['POST'])
def save_user_evaluations():
    data = request.get_json()
    user_id = data.get('userId')
    evaluations = data.get('evaluations', [])

    if not user_id or not evaluations:
        return jsonify({'success': False, 'message': 'Données incomplètes.'}), 400

    try:
        for eval in evaluations:
            activity_id = eval.get('activity_id')
            item_id = eval.get('item_id')
            item_type = eval.get('item_type')
            eval_number = str(eval.get('eval_number'))
            note = eval.get('note')

            if not activity_id:
                print(f"❌ Ignoré (pas d'activité): {eval}")
                continue

            existing = db.session.query(CompetencyEvaluation).filter_by(
                user_id=user_id,
                activity_id=activity_id,
                item_id=item_id,
                item_type=item_type,
                eval_number=eval_number
            ).first()

            if existing:
                if note == 'empty':
                    db.session.delete(existing)
                else:
                    existing.note = note
                    existing.created_at = datetime.utcnow()
            else:
                if note != 'empty':
                    db.session.add(CompetencyEvaluation(
                        user_id=user_id,
                        activity_id=activity_id,
                        item_id=item_id,
                        item_type=item_type,
                        eval_number=eval_number,
                        note=note,
                        created_at=datetime.utcnow()
                    ))


        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500



@competences_bp.route('/get_user_evaluations_by_user/<int:user_id>', methods=['GET'])
def get_user_evaluations_by_user(user_id):
    from datetime import datetime

    def to_iso(dt):
        if not dt:
            return ''
        # la colonne est Text : dt peut être str ou datetime
        if isinstance(dt, datetime):
            return dt.isoformat()  # ex: 2025-08-15T12:34:56.789123
        if isinstance(dt, str):
            # essaie iso → sinon quelques formats courants → sinon renvoie tel quel
            for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S.%f",
                        "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
                        "%d/%m/%Y %H:%M", "%d/%m/%Y"):
                try:
                    return datetime.strptime(dt, fmt).isoformat()
                except ValueError:
                    continue
            return dt  # on garde la valeur, le front fera un fallback
        return ''

    evaluations = CompetencyEvaluation.query.filter_by(user_id=user_id).all()
    return jsonify([{
        'activity_id': e.activity_id,
        'item_id': e.item_id,
        'item_type': e.item_type,
        'eval_number': e.eval_number,
        'note': e.note,
        'created_at': to_iso(e.created_at)
    } for e in evaluations])


@competences_bp.route('/role_structure/<int:user_id>/<int:role_id>', methods=['GET'])
def get_role_structure(user_id, role_id):
    from Code.models.models import activity_roles

    role = Role.query.get(role_id)
    user = User.query.get(user_id)
    if not role or not user:
        return jsonify({'error': 'Utilisateur ou rôle non trouvé'}), 404

    activities = db.session.query(Activities).join(activity_roles)\
        .filter(activity_roles.c.role_id == role_id).all()

    all_evaluations = CompetencyEvaluation.query.filter_by(user_id=user_id).all()
    eval_dict = {}
    for e in all_evaluations:
        key = (e.item_id, e.item_type, str(e.eval_number))
        eval_dict[key] = {
            'note': e.note,
            'created_at': e.created_at
        }

    activities_data = []
    for activity in activities:
        activity_obj = {
            'id': activity.id,
            'name': activity.name,
            'savoirs': [],
            'savoir_faires': [],
            'hsc': []
        }

        for savoir in activity.savoirs:
            activity_obj['savoirs'].append({
                'id': savoir.id,
                'description': savoir.description,
                'evals': {
                    k: eval_dict.get((savoir.id, 'savoirs', k), {}) for k in ['1', '2', '3']
                }
            })

        for sf in activity.savoir_faires:
            activity_obj['savoir_faires'].append({
                'id': sf.id,
                'description': sf.description,
                'evals': {
                    k: eval_dict.get((sf.id, 'savoir_faires', k), {}) for k in ['1', '2', '3']
                }
            })

        for hsc in activity.softskills:
            activity_obj['hsc'].append({
                'id': hsc.id,
                'description': hsc.habilete,
                'niveau': hsc.niveau,
                'evals': {
                    k: eval_dict.get((hsc.id, 'softskills', k), {}) for k in ['1', '2', '3']
                }
            })

        activities_data.append(activity_obj)

    # Synthèse (notations garant, manager, RH) + compétences
    synthese = []
    for activity in activities:
        synthese.append({
            'activity_id': activity.id,
            'activity_name': activity.name,
            'competencies': [c.description for c in activity.competencies],
            'evals': {
                role_name: eval_dict.get((activity.id, 'activities', role_name), {})
                for role_name in ['garant', 'manager', 'rh']
            }
        })

    return jsonify({
        'role_id': role.id,
        'role_name': role.name,
        'activities': activities_data,
        'synthese': synthese
    })


@competences_bp.route('/global_summary/<int:user_id>')
def global_summary(user_id):
    from flask import render_template
    from Code.models.models import activity_roles

    user = User.query.get(user_id)
    if not user:
        return "Utilisateur introuvable", 404

    user_roles = UserRole.query.filter_by(user_id=user_id).all()
    role_ids = [ur.role_id for ur in user_roles]
    roles = Role.query.filter(Role.id.in_(role_ids)).all()

    evals = CompetencyEvaluation.query.filter_by(user_id=user_id).all()
    eval_map = {}
    for e in evals:
        if e.item_type is None and e.item_id is None:  # Synthèse par activité
            key = f"{e.activity_id}_{e.eval_number}"
            eval_map[key] = e.note

    role_data = []
    for role in roles:
        activities = db.session.query(Activities).join(activity_roles).filter(activity_roles.c.role_id == role.id).all()
        activity_data = []
        for activity in activities:
            competencies = [c.description for c in activity.competencies]
            key_g = f"{activity.id}_garant"
            key_m = f"{activity.id}_manager"
            key_r = f"{activity.id}_rh"
            activity_data.append({
                'name': activity.name,
                'competencies': competencies,
                'evals': {
                    'garant': eval_map.get(key_g),
                    'manager': eval_map.get(key_m),
                    'rh': eval_map.get(key_r)
                }
            })
        role_data.append({
            'name': role.name,
            'activities': activity_data
        })

    return render_template('global_summary_table.html', user=user, roles=role_data)


@competences_bp.route('/global_flat_summary/<int:user_id>')
def global_flat_summary(user_id):
    from flask import render_template
    from Code.models.models import activity_roles

    user = User.query.get(user_id)
    if not user:
        return "Utilisateur introuvable", 404

    user_roles = UserRole.query.filter_by(user_id=user_id).all()
    role_ids = [ur.role_id for ur in user_roles]
    roles = Role.query.filter(Role.id.in_(role_ids)).all()

    evaluations = CompetencyEvaluation.query.filter_by(user_id=user_id).all()
    eval_map = {}
    eval_date_map = {}
    for e in evaluations:
        if e.item_type is None and e.item_id is None:
            key = f"{e.activity_id}_activity_{e.eval_number}"
            eval_map[key] = e.note
            if e.created_at:
                if isinstance(e.created_at, str):
                    try:
                        parsed_date = datetime.fromisoformat(e.created_at)
                    except ValueError:
                        parsed_date = datetime.strptime(e.created_at, "%d/%m/%Y")
                else:
                    parsed_date = e.created_at

                eval_date_map[key] = parsed_date.strftime('%d/%m/%Y')
            else:
                eval_date_map[key] = ''

    header_roles = []
    header_activities = []
    row_manager = []

    for role in roles:
        activities = db.session.query(Activities).join(activity_roles)\
            .filter(activity_roles.c.role_id == role.id).all()
        if not activities:
            continue

        all_green = all(
            eval_map.get(f"{act.id}_activity_manager", '') == 'green'
            for act in activities
        )
        role_status = 'green' if all_green else ''

        header_roles.append({
            'name': role.name,
            'span': len(activities),
            'status': role_status
        })

        for act in activities:
            header_activities.append(act.name)
            key = f"{act.id}_activity_manager"
            row_manager.append({
                'activity_id': act.id,
                'note': eval_map.get(key, ''),
                'date': eval_date_map.get(key, '')
            })

    return render_template(
        'global_flat_summary.html',
        user=user,
        header_roles=header_roles,
        header_activities=header_activities,
        row_manager=row_manager,
        current_date=datetime.now().strftime('%d/%m/%Y') 
    )



@competences_bp.route('/users/global_summary', methods=['GET'])
def users_global_summary():
    from Code.models.models import User, Role, Activities, CompetencyEvaluation, activity_roles

    users = User.query.all()
    roles = Role.query.order_by(Role.name).all()

    # Préparer l'ensemble des activités par rôle
    role_activities_map = {}
    for role in roles:
        acts = db.session.query(Activities).join(activity_roles)\
            .filter(activity_roles.c.role_id == role.id).all()
        role_activities_map[role.id] = acts

    user_rows = []
    for user in users:
        evals = CompetencyEvaluation.query.filter_by(user_id=user.id, eval_number='manager').all()
        notes = []

        for role in roles:
            role_activities = role_activities_map.get(role.id, [])
            related_notes = [
                e.note for e in evals
                if e.activity_id in [a.id for a in role_activities]
            ]
            note = related_notes[0] if related_notes else None
            notes.append(note)

        user_rows.append({
            'user': f"{user.first_name} {user.last_name}",
            'user_id': user.id,
            'manager_id': user.manager_id,  
            'notes': notes
        })

    role_names = [r.name for r in roles]
    roles_loop = [r.name for r in roles]

    return render_template(
        'global_users_summary.html',
        roles=roles,
        user_rows=user_rows,
        all_role_names=role_names,
        roles_loop=roles_loop
    )



@competences_bp.route('/general_performance/<int:activity_id>', methods=['GET'])
def get_general_performance(activity_id):
    from Code.models.models import Link, Performance
    # On récupère une performance attachée à un lien dont source est activity_id
    link = Link.query.filter_by(source_activity_id=activity_id).first()
    if not link or not link.performance:
        return jsonify({'content': ''})
    return jsonify({'content': link.performance.name or ''})


@competences_bp.route('/performance_perso_list/<int:user_id>/<int:activity_id>', methods=['GET'])
def get_personalized_performance_list(user_id, activity_id):
    performances = PerformancePersonnalisee.query.filter_by(
        user_id=user_id, activity_id=activity_id, deleted=False
    ).order_by(PerformancePersonnalisee.updated_at.desc()).all()

    return jsonify([
        {
            'id': p.id,
            'content': p.content,
            'updated_at': (
                p.updated_at.strftime('%d/%m/%Y %H:%M') if p.updated_at and not isinstance(p.updated_at, str)
                else p.updated_at
            )
        }
        for p in performances
    ])



@competences_bp.route('/performance_perso', methods=['POST'])
def save_new_personalized_performance():
    data = request.get_json()
    user_id = data.get('user_id')
    activity_id = data.get('activity_id')
    content = data.get('content')

    if not user_id or not activity_id:
        return jsonify({'success': False, 'message': 'ID manquant'}), 400

    try:
        perf = PerformancePersonnalisee(
            user_id=user_id,
            activity_id=activity_id,
            content=content,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            deleted=False
        )
        db.session.add(perf)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500



@competences_bp.route('/performance_history/<int:user_id>/<int:activity_id>')
def get_performance_history(user_id, activity_id):
    from sqlalchemy import or_
    performances = PerformancePersonnalisee.query.filter(
        PerformancePersonnalisee.user_id == user_id,
        PerformancePersonnalisee.activity_id == activity_id,
        or_(PerformancePersonnalisee.content != '', PerformancePersonnalisee.content.isnot(None))
    ).order_by(PerformancePersonnalisee.updated_at.desc()).all()

    history = [{
        "content": p.content,
        "updated_at": (
            p.updated_at.strftime("%d/%m/%Y %H:%M") if p.updated_at and not isinstance(p.updated_at, str)
            else p.updated_at if p.updated_at else ''
        ),
        "deleted": p.deleted
    } for p in performances]


    return jsonify(history)


@competences_bp.route('/performance_perso/<int:perf_id>', methods=['DELETE'])
def delete_personalized_performance(perf_id):
    perf = PerformancePersonnalisee.query.get(perf_id)
    if not perf:
        return jsonify({'success': False, 'message': 'Introuvable'}), 404
    try:
        perf.deleted = True
        perf.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

