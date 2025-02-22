# Code/models/models.py

from Code.extensions import db

# Table d'association entre Task et Tool
task_tools = db.Table(
    'task_tools',
    db.Column('task_id', db.Integer, db.ForeignKey('tasks.id'), primary_key=True),
    db.Column('tool_id', db.Integer, db.ForeignKey('tools.id'), primary_key=True)
)

class Activities(db.Model):
    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True)
    # Identifiant stable provenant de Visio (pour éviter de recréer/supprimer l'activité à chaque fois)
    shape_id = db.Column(db.String(50), unique=True, index=True, nullable=True)

    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_result = db.Column(db.Boolean, nullable=False, default=False)

    # Relation avec les tâches (ordonnées par 'order')
    tasks = db.relationship('Task', backref='activity', lazy=True, order_by='Task.order', cascade="all, delete-orphan")

    # Relation avec les compétences validées
    competencies = db.relationship('Competency', backref='activity', lazy=True, cascade="all, delete-orphan")

    # Relation avec les habiletés socio-cognitives (softskills)
    softskills = db.relationship('Softskill', backref='activity', lazy=True, cascade="all, delete-orphan")

class Connections(db.Model):
    __tablename__ = 'connections'

    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('activities.id', name='fk_connections_source_id'), nullable=True)
    target_id = db.Column(db.Integer, db.ForeignKey('activities.id', name='fk_connections_target_id'), nullable=True)
    type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)

class Data(db.Model):
    __tablename__ = 'data'

    id = db.Column(db.Integer, primary_key=True)
    # Si vous souhaitez aussi faire des mises à jour partielles sur les Data, on peut leur attribuer un shape_id
    shape_id = db.Column(db.String(50), unique=True, index=True, nullable=True)

    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    layer = db.Column(db.String(50), nullable=True)

class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    order = db.Column(db.Integer, nullable=True)

    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)

    # Relation Many-to-Many avec Tool
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
    # Stocke le niveau sous forme de chaîne ("1", "2", "3" ou "4")
    niveau = db.Column(db.String(10), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
