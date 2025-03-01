import os
import sys
from dotenv import load_dotenv

load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from flask import Flask
from flask_migrate import Migrate
from Code.extensions import db

def create_app():
    static_folder = os.path.join(parent_dir, 'static')
    app = Flask(__name__, static_folder=static_folder)

    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    db_path = os.path.join(instance_path, 'optiq.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate = Migrate(app, db)

    # Enregistrement des blueprints existants
    from Code.routes.activities import activities_bp
    app.register_blueprint(activities_bp)

    from Code.routes.tools import tools_bp
    app.register_blueprint(tools_bp)

    from Code.routes.skills import skills_bp
    app.register_blueprint(skills_bp)

    from Code.routes.softskills import softskills_bp
    app.register_blueprint(softskills_bp)

    from Code.routes.roles import roles_bp
    app.register_blueprint(roles_bp)

    # Enregistrement du blueprint pour la vue des rôles
    from Code.routes.roles_view import roles_view_bp
    app.register_blueprint(roles_view_bp)

    # Enregistrement du blueprint pour l'onboarding
    from Code.routes.onboarding import onboarding_bp
    app.register_blueprint(onboarding_bp)

    @app.route('/')
    def home():
        return "Bienvenue sur mon application Flask !"

    @app.route('/test_skills')
    def test_skills():
        return app.send_static_file('test_skills.html')

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
