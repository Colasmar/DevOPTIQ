# Code/models/time_extra.py
from datetime import datetime
from Code.extensions import db

class TimeProject(db.Model):
    __tablename__ = 'time_project'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    lines = db.relationship('TimeProjectLine', backref='project', cascade="all, delete-orphan")

class TimeProjectLine(db.Model):
    __tablename__ = 'time_project_line'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('time_project.id', ondelete="CASCADE"), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    duration_minutes = db.Column(db.Float, nullable=False, default=0)
    delay_minutes = db.Column(db.Float, nullable=False, default=0)
    nb_people = db.Column(db.Integer, nullable=False, default=1)

class TimeRoleAnalysis(db.Model):
    __tablename__ = 'time_role_analysis'
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    js = db.Column(db.Integer)   # optionnel (override)
    sa = db.Column(db.Integer)   # optionnel (override)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    lines = db.relationship('TimeRoleLine', backref='role_analysis', cascade="all, delete-orphan")

class TimeRoleLine(db.Model):
    __tablename__ = 'time_role_line'
    id = db.Column(db.Integer, primary_key=True)
    role_analysis_id = db.Column(db.Integer, db.ForeignKey('time_role_analysis.id', ondelete="CASCADE"), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    recurrence = db.Column(db.String(32), nullable=False)  # journalier/hebdomadaire/mensuel/annuel
    frequency = db.Column(db.Integer, nullable=False, default=1)

class TimeWeakness(db.Model):
    __tablename__ = 'time_weakness'
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    duration_std_minutes = db.Column(db.Float, nullable=False, default=0)  # B
    delay_std_minutes = db.Column(db.Float, nullable=False, default=0)     # C
    recurrence = db.Column(db.String(32), nullable=False)  # J/H/M/A
    frequency = db.Column(db.Integer, nullable=False, default=1)
    weakness = db.Column(db.Text)  # K
    work_added_qty = db.Column(db.Float, nullable=False, default=0)  # L
    work_added_unit = db.Column(db.String(16), nullable=False, default='minutes')
    wait_added_qty = db.Column(db.Float, nullable=False, default=0)  # M
    wait_added_unit = db.Column(db.String(16), nullable=False, default='minutes')
    prob_denom = db.Column(db.Integer, nullable=False, default=1)    # N
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
