# Code/models/models.py
from datetime import datetime
from Code.extensions import db

# -------------------------------------------------------------------
# Tables d'association (déclarées UNE seule fois + extend_existing)
# -------------------------------------------------------------------
task_tools = db.Table(
    'task_tools',
    db.Column('task_id', db.Integer, db.ForeignKey('tasks.id'), primary_key=True),
    db.Column('tool_id', db.Integer, db.ForeignKey('tools.id'), primary_key=True),
    extend_existing=True
)

activity_roles = db.Table(
    'activity_roles',
    db.Column('activity_id', db.Integer, db.ForeignKey('activities.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('status', db.String(50), nullable=False),
    extend_existing=True
)

task_roles = db.Table(
    'task_roles',
    db.Column('task_id', db.Integer, db.ForeignKey('tasks.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('status', db.String(50), nullable=False),
    extend_existing=True
)

# -------------------------------------------------------------------
# Modèles - CORRIGÉ avec autoincrement=True pour PostgreSQL
# -------------------------------------------------------------------
class Activities(db.Model):
    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    shape_id = db.Column(db.String(50), unique=True, index=True, nullable=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_result = db.Column(db.Boolean, nullable=False, default=False)

    # 🔹 Nouvelles colonnes (défaut / préremplissage des autres pages)
    duration_minutes = db.Column(db.Float, default=0)  # durée moyenne (en minutes)
    delay_minutes    = db.Column(db.Float, default=0)  # délai de production (en minutes)

    tasks = db.relationship(
        'Task',
        backref='activity',
        lazy=True,
        order_by='Task.order',
        cascade="all, delete-orphan"
    )
    competencies = db.relationship('Competency', backref='activity', lazy=True, cascade="all, delete-orphan")
    softskills = db.relationship('Softskill', backref='activity', lazy=True, cascade="all, delete-orphan")
    constraints = db.relationship('Constraint', backref='activity', lazy=True, cascade="all, delete-orphan")
    savoirs = db.relationship('Savoir', backref='activity', lazy=True, cascade="all, delete-orphan")
    savoir_faires = db.relationship('SavoirFaire', backref='activity', lazy=True, cascade="all, delete-orphan")
    aptitudes = db.relationship('Aptitude', backref='activity', lazy=True, cascade="all, delete-orphan")


class Data(db.Model):
    __tablename__ = 'data'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    shape_id = db.Column(db.String(50), unique=True, index=True, nullable=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    layer = db.Column(db.String(50), nullable=True)


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    order = db.Column(db.Integer, nullable=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)

    # 🔹 Nouvelles colonnes (durée/délai par tâche — utile si saisie « par tâches »)
    duration_minutes = db.Column(db.Float, default=0)
    delay_minutes    = db.Column(db.Float, default=0)

    tools = db.relationship(
        'Tool',
        secondary=task_tools,
        lazy='subquery',
        backref=db.backref('tasks', lazy=True)
    )


class Tool(db.Model):
    __tablename__ = 'tools'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)


class Competency(db.Model):
    __tablename__ = 'competencies'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description = db.Column(db.Text, nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)


class Softskill(db.Model):
    __tablename__ = 'softskills'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    habilete = db.Column(db.String(255), nullable=False)
    niveau = db.Column(db.String(10), nullable=False)
    justification = db.Column(db.Text, nullable=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    onboarding_plan = db.Column(db.Text, nullable=True)


class Link(db.Model):
    __tablename__ = 'links'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    source_activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=True)
    source_data_id = db.Column(db.Integer, db.ForeignKey('data.id'), nullable=True)
    target_activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=True)
    target_data_id = db.Column(db.Integer, db.ForeignKey('data.id'), nullable=True)
    type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)

    @property
    def source_id(self):
        return self.source_activity_id if self.source_activity_id is not None else self.source_data_id

    @property
    def target_id(self):
        return self.target_activity_id if self.target_activity_id is not None else self.target_data_id


class Performance(db.Model):
    __tablename__ = 'performances'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    link_id = db.Column(db.Integer, db.ForeignKey('links.id', ondelete='CASCADE'), unique=True)
    link = db.relationship('Link', backref=db.backref('performance', uselist=False))


class PerformancePersonnalisee(db.Model):
    __tablename__ = 'performance_personnalisee'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    activity_id = db.Column(db.Integer, nullable=False)

    content = db.Column('content', db.Text, nullable=True)
    validation_status = db.Column(db.String(20), default='non-validee')
    validation_date = db.Column(db.String(10), nullable=True)
    created_at = db.Column(db.Text, default=lambda: datetime.utcnow().isoformat())
    updated_at = db.Column(db.Text, default=lambda: datetime.utcnow().isoformat())
    deleted = db.Column(db.Boolean, default=False)


class Constraint(db.Model):
    __tablename__ = 'constraints'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description = db.Column(db.Text, nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)


class Savoir(db.Model):
    __tablename__ = 'savoirs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description = db.Column(db.Text, nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)


class SavoirFaire(db.Model):
    __tablename__ = 'savoir_faires'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description = db.Column(db.Text, nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)


class Aptitude(db.Model):
    __tablename__ = 'aptitudes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description = db.Column(db.Text, nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    email = db.Column(db.String(200), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='user')
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    subordinates = db.relationship('User', backref=db.backref('manager', remote_side=[id]))
    evaluations = db.relationship('CompetencyEvaluation', back_populates='user', cascade='all, delete-orphan')


class UserRole(db.Model):
    __tablename__ = 'user_roles'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), primary_key=True)

    user = db.relationship('User', backref='user_roles')
    role = db.relationship('Role', backref='user_roles')


class CompetencyEvaluation(db.Model):
    __tablename__ = 'competency_evaluation'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)

    item_id = db.Column(db.Integer, nullable=True)
    item_type = db.Column(db.String(50), nullable=True)
    eval_number = db.Column(db.String(50), nullable=False)
    note = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.Text, default=datetime.utcnow)

    user = db.relationship('User', back_populates='evaluations')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'activity_id', 'item_id', 'item_type', 'eval_number'),
    )


class TimeAnalysis(db.Model):
    __tablename__ = 'time_analysis'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    duration = db.Column(db.Integer, nullable=False)
    recurrence = db.Column(db.String(20), nullable=False)
    frequency = db.Column(db.Integer, nullable=False)
    delay = db.Column(db.Integer, nullable=True)

    type = db.Column(db.String(20), nullable=False)

    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    nb_people = db.Column(db.Integer, nullable=False, default=1)
    impact_unit = db.Column(db.String(20), nullable=True)
    delay_increase = db.Column(db.Float, nullable=True)
    delay_percentage = db.Column(db.Float, nullable=True)

    activity = db.relationship('Activities', backref='time_analyses')
    task = db.relationship('Task', backref='time_analyses')
    role = db.relationship('Role', backref='time_analyses')
    user = db.relationship('User', backref='time_analyses')

    @property
    def recurrence_factor(self):
        return {
            "journalier": 220,
            "hebdo": 42,
            "mensuel": 10.5,
            "annuel": 1
        }.get(self.recurrence, 0)

    @property
    def annual_time(self):
        return self.duration * self.recurrence_factor * self.frequency * self.nb_people

    @property
    def delay_gap(self):
        if self.delay and self.delay_increase:
            return self.delay + self.delay_increase
        elif self.delay:
            return self.delay
        else:
            return self.delay_increase or 0

    @property
    def delay_ratio(self):
        if self.delay and self.delay_increase:
            try:
                return round((self.delay_increase / self.delay) * 100, 1)
            except ZeroDivisionError:
                return 0
        return 0

# -------------------------------------------------------------------
# 🔽 Nouveaux modèles "Temps"
# -------------------------------------------------------------------
class TimeProject(db.Model):
    __tablename__ = 'time_project'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    lines = db.relationship('TimeProjectLine', backref='project', cascade="all, delete-orphan")


class TimeProjectLine(db.Model):
    __tablename__ = 'time_project_line'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('time_project.id', ondelete="CASCADE"), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    duration_minutes = db.Column(db.Float, nullable=False, default=0)
    delay_minutes = db.Column(db.Float, nullable=False, default=0)
    nb_people = db.Column(db.Integer, nullable=False, default=1)


class TimeRoleAnalysis(db.Model):
    __tablename__ = 'time_role_analysis'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    name = db.Column(db.String(120), default='Analyse rôle')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    lines = db.relationship('TimeRoleLine', backref='role_analysis', cascade="all, delete-orphan")


class TimeRoleLine(db.Model):
    __tablename__ = 'time_role_line'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    role_analysis_id = db.Column(db.Integer, db.ForeignKey('time_role_analysis.id', ondelete="CASCADE"), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    recurrence = db.Column(db.String(32), nullable=False)  # journalier/hebdomadaire/mensuel/annuel
    frequency = db.Column(db.Integer, nullable=False, default=1)
    # 🔹 Ajouts pour stocker la durée/délai/personnes à la ligne (corrige les agrégats à 0)
    duration_minutes = db.Column(db.Float, nullable=False, default=0)
    delay_minutes = db.Column(db.Float, nullable=False, default=0)
    nb_people = db.Column(db.Integer, nullable=False, default=1)


class TimeWeakness(db.Model):
    __tablename__ = 'time_weakness'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    duration_std_minutes = db.Column(db.Float, nullable=False, default=0)  # B
    delay_std_minutes = db.Column(db.Float, nullable=False, default=0)     # C
    recurrence = db.Column(db.String(32), nullable=False)  # J/H/M/A
    frequency = db.Column(db.Integer, nullable=False, default=1)
    weakness = db.Column(db.Text)
    work_added_qty = db.Column(db.Float, nullable=False, default=0)  # L
    work_added_unit = db.Column(db.String(16), nullable=False, default='minutes')
    wait_added_qty = db.Column(db.Float, nullable=False, default=0)  # M
    wait_added_unit = db.Column(db.String(16), nullable=False, default='minutes')
    prob_denom = db.Column(db.Integer, nullable=False, default=1)    # N
    created_at = db.Column(db.DateTime, default=datetime.utcnow)