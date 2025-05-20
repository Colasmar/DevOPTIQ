from flask import Blueprint, render_template, request, redirect, url_for
from Code.extensions import db
from Code.models.models import TimeAnalysis, Activities, Task
from datetime import datetime

time_bp = Blueprint('time_view', __name__, url_prefix='/temps')

@time_bp.route('/')
def time_list():
    all_times = TimeAnalysis.query.all()
    activities = Activities.query.all()
    
    tasks_by_activity = {}
    for activity in activities:
        tasks_by_activity[activity.id] = {
            'name': activity.name,
            'tasks': activity.tasks  
        }
    return render_template('time_list.html', analyses=all_times, activities=activities, tasks_by_activity=tasks_by_activity)

@time_bp.route('/new', methods=['GET', 'POST'])
def time_new():
    if request.method == 'POST':
        duration = int(request.form['duration'])
        recurrence = request.form['recurrence']
        frequency = int(request.form['frequency'])
        activity_id = request.form.get('activity_id') or None
        task_id = request.form.get('task_id') or None
        nb_people = int(request.form.get('nb_people', 1))
        delay_unit = request.form.get('delay_unit') or None
        delay_increase = request.form.get('delay_increase')
        delay_increase = float(delay_increase) if delay_increase else None
        analysis_type = request.form['analysis_type']

        # Création de l'objet sans date
        time_obj = TimeAnalysis(
            duration=duration,
            recurrence=recurrence,
            frequency=frequency,
            type=analysis_type,
            activity_id=activity_id,
            task_id=task_id,
            nb_people=nb_people,
            delay_unit=delay_unit if analysis_type == 'défaillance' else None,
            delay_increase=delay_increase if analysis_type == 'défaillance' else None,
            start_datetime=None,
            end_datetime=None
        )

        db.session.add(time_obj)
        db.session.commit()
        return redirect(url_for('time_view.time_list'))

    activities = Activities.query.all()
    tasks = Task.query.all()
    return render_template('time_form.html', activities=activities, tasks=tasks)