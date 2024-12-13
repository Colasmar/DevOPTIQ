from extensions import db

class Activity(db.Model):
    __tablename__ = 'activities'  # Optionnel, mais c'est plus explicite
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
