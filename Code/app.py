import os
import sys

# Ajouter dynamiquement le répertoire parent et 'Code' dans sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from Code.extensions import db
from Code.models.models import Activity
from Code.routes.ui_routes import ui_bp
from Code.routes.activities import activities_bp
from flask import Flask, render_template
from sqlalchemy import text


def create_app():
    app = Flask(__name__)

    # Configuration de la base de données
    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    db_path = os.path.join(instance_path, 'optiq.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Création du dossier 'instance' si nécessaire
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)

    # Initialisation des extensions
    db.init_app(app)

    # Enregistrement des blueprints
    app.register_blueprint(activities_bp)
    app.register_blueprint(ui_bp)

    return app


# Déclarer explicitement 'app' pour l'import
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        try:
            # Vérification de la connexion à la base de données
            db.session.execute(text('SELECT 1'))
            print("Connexion à la base de données réussie.")
        except Exception as e:
            print(f"Erreur lors de la connexion à la base de données : {e}")

        # Création ou mise à jour des tables
        db.create_all()
        print("Tables créées ou mises à jour avec succès !")

    app.run(debug=True)
