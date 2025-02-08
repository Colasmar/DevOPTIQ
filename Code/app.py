import os
import sys

# Ajouter dynamiquement le répertoire parent et 'Code' dans sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from flask import Flask, jsonify
from sqlalchemy import text, inspect

from Code.extensions import db
from Code.models.models import Activities, Connections, Data

def create_app():
    """Initialisation de l'application Flask avec configuration et extensions."""
    app = Flask(__name__)

    # Configuration de la base de données
    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    db_path = os.path.join(instance_path, 'optiq.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Création du dossier 'instance' si nécessaire
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)

    # Initialisation de l'extension SQLAlchemy
    db.init_app(app)

    # Route pour déboguer la création de la base de données
    @app.route('/debug-create-db', methods=['GET'])
    def debug_create_db():
        try:
            with app.app_context():
                # Liste des tables avant la création
                inspector = inspect(db.engine)
                before_tables = inspector.get_table_names()
                print(f"Tables avant la création : {before_tables}")

                # Création des tables
                db.create_all()

                # Liste des tables après la création
                after_tables = inspector.get_table_names()
                print(f"Tables après la création : {after_tables}")

                return jsonify({
                    "message": "Base de données créée avec succès.",
                    "tables_before": before_tables,
                    "tables_after": after_tables,
                })
        except Exception as e:
            return jsonify({
                "message": "Erreur lors de la création de la base de données.",
                "error": str(e)
            })

    return app


# Déclarer explicitement 'app' pour l'import
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
