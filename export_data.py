import os
import csv
from flask import Flask
from Code.extensions import db
from Code.models.models import (
    Activities, Role, Task, Data, Tool, Competency, Softskill,
    Link, Performance, Constraint, Savoir, SavoirFaire, Aptitude
)

# ➤ Création de l'application Flask
app = Flask(__name__)

# ➤ Chemin absolu vers optiq.db pour éviter toute confusion
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'Code', 'instance', 'optiq.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ➤ Initialisation de SQLAlchemy
db.init_app(app)

# ➤ Création du dossier de sauvegarde
backup_folder = os.path.join(BASE_DIR, 'backup')
os.makedirs(backup_folder, exist_ok=True)

# ➤ Fonction d'export CSV
def export_to_csv(model, filename):
    filepath = os.path.join(backup_folder, filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        columns = [column.name for column in model.__table__.columns]
        writer.writerow(columns)
        for obj in model.query.all():
            writer.writerow([getattr(obj, col) for col in columns])
    print(f"✅ Exported {filename}")

# ➤ Contexte Flask requis pour accéder à la base
with app.app_context():
    export_to_csv(Role, 'roles.csv')
    export_to_csv(Activities, 'activities.csv')
    export_to_csv(Task, 'tasks.csv')
    export_to_csv(Data, 'data.csv')
    export_to_csv(Tool, 'tools.csv')
    export_to_csv(Competency, 'competencies.csv')
    export_to_csv(Softskill, 'softskills.csv')
    export_to_csv(Link, 'links.csv')
    export_to_csv(Performance, 'performances.csv')
    export_to_csv(Constraint, 'constraints.csv')
    export_to_csv(Savoir, 'savoirs.csv')
    export_to_csv(SavoirFaire, 'savoir_faires.csv')
    export_to_csv(Aptitude, 'aptitudes.csv')
