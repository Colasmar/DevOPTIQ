from scripts.extract_visio import create_app
from Code.extensions import db

# Créer l'application
app = create_app()

# Créer les tables
with app.app_context():
    db.create_all()
    print("Les tables ont été créées avec succès.")
