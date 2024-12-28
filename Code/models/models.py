from Code.extensions import db


class Activity(db.Model):
    __tablename__ = 'activities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    incoming_relations = db.relationship('Relation', foreign_keys='Relation.target_id', backref='target_activity', lazy=True)
    outgoing_relations = db.relationship('Relation', foreign_keys='Relation.source_id', backref='source_activity', lazy=True)

class Relation(db.Model):
    __tablename__ = 'relations'
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
