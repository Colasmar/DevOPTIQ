from Code.extensions import db

class Activities(db.Model):
    __tablename__ = 'activities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_result = db.Column(db.Boolean, nullable=False, default=False)  # Champ ajouté pour distinguer les activités résultat

class Connections(db.Model):
    __tablename__ = 'connections'
    id = db.Column(db.Integer, primary_key=True)
    # Attribution d'un nom explicite aux clés étrangères
    source_id = db.Column(
        db.Integer, 
        db.ForeignKey('activities.id', name='fk_connections_source_id'),
        nullable=False
    )
    target_id = db.Column(
        db.Integer, 
        db.ForeignKey('activities.id', name='fk_connections_target_id'),
        nullable=False
    )
    type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)

class Data(db.Model):
    __tablename__ = 'data'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    layer = db.Column(db.String(50), nullable=True)
