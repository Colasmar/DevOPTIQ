import os
import sys

# Ajouter dynamiquement le chemin du projet (pour que les imports internes fonctionnent)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from flask import Flask, jsonify
from sqlalchemy import inspect
from flask_migrate import Migrate

from Code.extensions import db
# Import explicite des modèles pour les enregistrer dans l'instance db
from Code.models.models import Activities, Connections, Data

def create_app():
    app = Flask(__name__)
    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    db_path = os.path.join(instance_path, 'optiq.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate = Migrate(app, db)

    # Optionnel : route de débogage pour vérifier la création des tables
    @app.route('/debug-create-db', methods=['GET'])
    def debug_create_db():
        with app.app_context():
            inspector = inspect(db.engine)
            before = inspector.get_table_names()
            db.create_all()
            after = inspector.get_table_names()
            return jsonify({"before": before, "after": after})
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
