from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Activities(db.Model):
    """Table des activités principales."""
    __tablename__ = 'activities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

class Connections(db.Model):
    """Table des connexions entre activités et données."""
    __tablename__ = 'connections'
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, nullable=False)  # Référence à une donnée source
    target_id = db.Column(db.Integer, nullable=False)  # Référence à une activité cible
    type = db.Column(db.String(50), nullable=False)  # input ou output
    description = db.Column(db.Text, nullable=True)

class Data(db.Model):
    """Table des données (déclenchantes, nourrissantes, etc.)."""
    __tablename__ = 'data'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # déclenchante, nourrissante, résultat, retour
    description = db.Column(db.Text, nullable=True)
    layer = db.Column(db.String(50), nullable=True)  # Ajout pour stocker les layers si nécessaire
