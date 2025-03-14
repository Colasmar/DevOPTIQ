from Code.extensions import db

# ---------------------------------------------------------
#  Table d'association entre Task et Tool
# ---------------------------------------------------------
task_tools = db.Table(
    'task_tools',
    db.Column('task_id', db.Integer, db.ForeignKey('tasks.id'), primary_key=True),
    db.Column('tool_id', db.Integer, db.ForeignKey('tools.id'), primary_key=True)
)

# ---------------------------------------------------------
#  Modèles existants
# ---------------------------------------------------------
class Activities(db.Model):
    __tablename__ = 'activities'
    id = db.Column(db.Integer, primary_key=True)
    shape_id = db.Column(db.String(50), unique=True, index=True, nullable=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_result = db.Column(db.Boolean, nullable=False, default=False)

    tasks = db.relationship('Task', backref='activity', lazy=True,
                            order_by='Task.order', cascade="all, delete-orphan")
    competencies = db.relationship('Competency', backref='activity', lazy=True,
                                   cascade="all, delete-orphan")
    softskills = db.relationship('Softskill', backref='activity', lazy=True,
                                 cascade="all, delete-orphan")

    # NOUVEAU : Contrôles (contraintes et exigences)
    constraints = db.relationship(
        'Constraint',
        backref='activity',
        lazy=True,
        cascade="all, delete-orphan"
    )

class Data(db.Model):
    __tablename__ = 'data'
    id = db.Column(db.Integer, primary_key=True)
    shape_id = db.Column(db.String(50), unique=True, index=True, nullable=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # "output", "input", etc.
    description = db.Column(db.Text, nullable=True)
    layer = db.Column(db.String(50), nullable=True)
    performance = db.relationship('Performance', backref='data', uselist=False)


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    order = db.Column(db.Integer, nullable=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)

    tools = db.relationship(
        'Tool',
        secondary=task_tools,
        lazy='subquery',
        backref=db.backref('tasks', lazy=True)
    )

class Tool(db.Model):
    __tablename__ = 'tools'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)

class Competency(db.Model):
    __tablename__ = 'competencies'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)

class Softskill(db.Model):
    __tablename__ = 'softskills'
    id = db.Column(db.Integer, primary_key=True)
    habilete = db.Column(db.String(255), nullable=False)
    niveau = db.Column(db.String(10), nullable=False)
    justification = db.Column(db.Text, nullable=True)  # champ supplémentaire
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    onboarding_plan = db.Column(db.Text, nullable=True)  # plan d'onboarding

    def __repr__(self):
        return f"<Role {self.name}>"

# ---------------------------------------------------------
#  Tables d'association existantes
# ---------------------------------------------------------
activity_roles = db.Table('activity_roles',
    db.Column('activity_id', db.Integer, db.ForeignKey('activities.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('status', db.String(50), nullable=False)
)

task_roles = db.Table('task_roles',
    db.Column('task_id', db.Integer, db.ForeignKey('tasks.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('status', db.String(50), nullable=False)
)

class Link(db.Model):
    __tablename__ = 'links'
    id = db.Column(db.Integer, primary_key=True)
    source_activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=True)
    source_data_id = db.Column(db.Integer, db.ForeignKey('data.id'), nullable=True)
    target_activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=True)
    target_data_id = db.Column(db.Integer, db.ForeignKey('data.id'), nullable=True)
    type = db.Column(db.String(50), nullable=False)  # ex: 'déclenchante', 'nourrissante'
    description = db.Column(db.Text, nullable=True)

    @property
    def source_id(self):
        if self.source_activity_id is not None:
            return self.source_activity_id
        return self.source_data_id

    @property
    def target_id(self):
        if self.target_activity_id is not None:
            return self.target_activity_id
        return self.target_data_id

# ---------------------------------------------------------
#  NOUVELLES CLASSES : Performances, Constraints, Savoirs,
#  SavoirFaire, Aptitudes
# ---------------------------------------------------------

class Performance(db.Model):
    """
    Représente une performance attendue sur une donnée de sortie.
    data_id -> rattache la performance à la table 'data'.
    """
    __tablename__ = 'performances'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    data_id = db.Column(db.Integer, db.ForeignKey('data.id'), nullable=False)

class Constraint(db.Model):
    """
    Contrainte (ou exigence) associée à une activité.
    """
    __tablename__ = 'constraints'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)

class Savoir(db.Model):
    """
    Savoir attaché à l'activité (connaissance "théorique").
    """
    __tablename__ = 'savoirs'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)

class SavoirFaire(db.Model):
    """
    Savoir-faire attaché à l'activité (compétence pratique).
    """
    __tablename__ = 'savoir_faires'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)

class Aptitude(db.Model):
    """
    Aptitude spécifique attachée à l'activité.
    """
    __tablename__ = 'aptitudes'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
