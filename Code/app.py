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
from flask_migrate import Migrate
from Code.extensions import db

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

    # Enregistrement des blueprints
    from Code.routes.activities import activities_bp
    app.register_blueprint(activities_bp)
    # Si vous avez un blueprint pour les tâches, l'enregistrer également (si applicable)
    # from Code.routes.tasks import tasks_bp
    # app.register_blueprint(tasks_bp)
    from Code.routes.tools import tools_bp
    app.register_blueprint(tools_bp)

    @app.route('/')
    def home():
        return "Bienvenue sur mon application Flask !"
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
