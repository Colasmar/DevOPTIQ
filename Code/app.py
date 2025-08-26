# Code/app.py

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

from flask import Flask, redirect, url_for
from flask_migrate import Migrate
from Code.extensions import db, mail

# Import pour Flask-Mail
from flask_mail import Mail

# Import pour modifier la connexion SMTP
import smtplib

# Classe personnalisée pour forcer l'encodage UTF-8
class CustomMail(Mail):
    def connect(self):
        connection = super().connect()
        # Si c'est une instance de smtplib.SMTP, on définit local_hostname
        if isinstance(connection, smtplib.SMTP):
            # Forcer le local_hostname en ASCII
            connection.local_hostname = 'localhost'
        return connection

def create_app():
    static_folder = os.path.join(parent_dir, 'static')
    app = Flask(__name__, static_folder=static_folder)

    # Active le mode debug et la propagation des exceptions
    app.config['DEBUG'] = True
    app.config['PROPAGATE_EXCEPTIONS'] = True

    # Configuration de la base de données SQLite
    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    db_path = os.path.join(instance_path, 'optiq.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # -------------- Configuration SMTP pour Flask-Mail --------------
    # Adapte ces valeurs avec ton fournisseur SMTP
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'afdec.enterprise.services@gmail.com'
    app.config['MAIL_PASSWORD'] = 'awdkerghqvuwjhel'

    # Initialisation de Flask-Mail avec la classe personnalisée
    mail.init_app(app)
    db.init_app(app)


    # Init extensions
    from flask_migrate import Migrate
    migrate = Migrate(app, db)

    # ----------------------------------------------------------------------
    # 1) Filtre Jinja pour n'afficher que la partie numérique (1..4)
    # ----------------------------------------------------------------------
    import re  # pour le filtre extract_numeric_level
    def extract_numeric_level(value):
        match = re.search(r"\d", value or "")
        return match.group(0) if match else "1"

    app.jinja_env.filters['extract_numeric_level'] = extract_numeric_level

    # ----------------------------------------------------------------------
    # 2) Filtre Jinja 'escapejs' pour échapper apostrophes & backslashes en JS
    # ----------------------------------------------------------------------
    def escapejs_filter(value):
        if not value:
            return ""
        out = value.replace("\\", "\\\\")
        out = out.replace("'", "\\'")
        out = out.replace('"', '\\"')
        return out

    app.jinja_env.filters['escapejs'] = escapejs_filter

    # ----------------------------------------------------------------------
    # Blueprints
    # ----------------------------------------------------------------------
    from Code.routes.activities import activities_bp
    app.register_blueprint(activities_bp)

    from Code.routes.tools import tools_bp
    app.register_blueprint(tools_bp)

    from Code.routes.skills import skills_bp
    app.register_blueprint(skills_bp)

    from Code.routes.roles import roles_bp
    app.register_blueprint(roles_bp)

    from Code.routes.roles_view import roles_view_bp
    app.register_blueprint(roles_view_bp)

    from Code.routes.onboarding import onboarding_bp
    app.register_blueprint(onboarding_bp)

    from Code.routes.tasks import tasks_bp
    app.register_blueprint(tasks_bp)

    from Code.routes.performance import performance_bp
    app.register_blueprint(performance_bp)

    from Code.routes.constraints import constraints_bp
    app.register_blueprint(constraints_bp)

    from Code.routes.propose_softskills import propose_softskills_bp
    app.register_blueprint(propose_softskills_bp)

    from Code.routes.translate_softskills import translate_softskills_bp
    app.register_blueprint(translate_softskills_bp)

    from Code.routes.softskills import softskills_crud_bp
    app.register_blueprint(softskills_crud_bp)

    from Code.routes.savoirs import savoirs_bp
    app.register_blueprint(savoirs_bp)

    from Code.routes.savoir_faires import savoir_faires_bp
    app.register_blueprint(savoir_faires_bp)

    from Code.routes.aptitudes import aptitudes_bp
    app.register_blueprint(aptitudes_bp)

    from Code.routes.connexion_routes import auth_bp
    app.register_blueprint(auth_bp)

    from Code.routes.competences import competences_bp
    app.register_blueprint(competences_bp)

    # ---------------------
    #  Nouveaux blueprints
    # ---------------------
    from Code.routes.propose_savoirs import propose_savoirs_bp
    app.register_blueprint(propose_savoirs_bp)

    from Code.routes.propose_savoir_faires import propose_savoir_faires_bp
    app.register_blueprint(propose_savoir_faires_bp)

    from Code.routes.propose_aptitudes import propose_aptitudes_bp
    app.register_blueprint(propose_aptitudes_bp)

    from Code.routes.time_view import time_bp
    app.register_blueprint(time_bp)

    from Code.routes.gestion_compte import gestion_compte_bp
    app.register_blueprint(gestion_compte_bp)

    from Code.routes.routes_password  import auth_password_bp
    app.register_blueprint(auth_password_bp)

    from Code.routes.gestion_rh import gestion_rh_bp
    app.register_blueprint(gestion_rh_bp)

    from Code.routes.projection_metier import projection_metier_bp
    app.register_blueprint(projection_metier_bp)

    from Code.routes.gestion_outils import bp_tools
    app.register_blueprint(bp_tools)




    # Clé secrète pour session et sécurité
    app.secret_key = 'votre_clé_secrète_unique'

    @app.route('/')
    def home():
        return redirect(url_for('auth.login'))

    @app.route('/test_skills')
    def test_skills():
        return app.send_static_file('test_skills.html')

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)