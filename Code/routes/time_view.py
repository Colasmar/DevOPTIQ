from flask import Blueprint, render_template, request, redirect, url_for
from Code.extensions import db
from Code.models.models import TimeAnalysis, Activities, Task, Role, User
from datetime import datetime

time_bp = Blueprint('time_view', __name__, url_prefix='/temps')

@time_bp.route('/')
def time_list():
    all_times = TimeAnalysis.query.all()
    activities = Activities.query.all()
    tasks = Task.query.all()
    roles = Role.query.all()    # doit être importé
    users = User.query.all()    # idem

    return render_template(
        'time_list.html',
        analyses=all_times,
        activities=activities,
        tasks=tasks,
        roles=roles,
        users=users
    )



@time_bp.route('/new', methods=['GET', 'POST'])
def time_new():
    from Code.models.models import Role, User  # à importer si pas déjà fait

    if request.method == 'POST':
        analysis_type = request.form['analysis_type']
        duration = int(request.form['duration'])
        recurrence = request.form['recurrence']
        frequency = int(request.form['frequency'])
        activity_id = request.form.get('activity_id') or None
        task_id = request.form.get('task_id') or None
        role_id = request.form.get('role_id') or None
        user_id = request.form.get('user_id') or None
        nb_people = int(request.form.get('nb_people', 1))
        delay_unit = request.form.get('delay_unit') or 'minutes'
        impact_unit = request.form.get('impact_unit') or 'minutes'

        standard_delay = float(request.form.get('standard_delay'))
        delay_increase = float(request.form.get('delay_increase') or 0)

        # Conversion des unités en minutes
        unit_factor = {'minutes': 1, 'heures': 60, 'jours': 1440}
        delay_min = standard_delay * unit_factor[delay_unit]
        impact_min = delay_increase * unit_factor[impact_unit]

        retard_total = delay_min + impact_min
        retard_percent = (impact_min / delay_min * 100) if delay_min > 0 else 0

        annual_time = duration * frequency * nb_people

        time_obj = TimeAnalysis(
            duration=duration,
            recurrence=recurrence,
            frequency=frequency,
            delay=standard_delay,
            type=analysis_type,
            activity_id=activity_id,
            task_id=task_id,
            role_id=request.form.get('role_id') or None,
            user_id=request.form.get('user_id') or None,
            nb_people=nb_people,
            delay_increase=delay_increase,
            impact_unit=request.form.get('impact_unit') or None
        )


        db.session.add(time_obj)
        db.session.commit()
        return redirect(url_for('time_view.time_list'))

    activities = Activities.query.all()
    tasks = Task.query.all()
    roles = Role.query.all()
    users = User.query.all()
    return render_template('time_form.html', activities=activities, tasks=tasks, roles=roles, users=users)



