from sqlalchemy import text
import csv
import os
from Code.extensions import db
from Code.models.models import (
    Activities, Role, Task, Data, Tool, Competency, Softskill,
    Link, Performance, Constraint, Savoir, SavoirFaire, Aptitude
)
from flask import Flask

# Créer le chemin absolu vers optiq.db
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'Code', 'instance', 'optiq.db')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def import_from_csv(model, filename, converters=None):
    filepath = os.path.join('backup', filename)
    with open(filepath, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if converters:
                for key, func in converters.items():
                    if key in row:
                        row[key] = func(row[key])
            obj = model(**row)
            db.session.add(obj)
        print(f"✅ Imported {filename}")

with app.app_context():
    db.session.execute(text('PRAGMA foreign_keys = OFF;'))
    db.session.commit()

    import_from_csv(Activities, 'activities.csv', converters={'is_result': lambda x: x.lower() == 'true'})
    import_from_csv(Role, 'roles.csv')
    import_from_csv(Task, 'tasks.csv')
    import_from_csv(Data, 'data.csv')
    import_from_csv(Tool, 'tools.csv')
    import_from_csv(Competency, 'competencies.csv')
    import_from_csv(Softskill, 'softskills.csv')
    import_from_csv(Constraint, 'constraints.csv')
    import_from_csv(Savoir, 'savoirs.csv')
    import_from_csv(SavoirFaire, 'savoir_faires.csv')
    import_from_csv(Aptitude, 'aptitudes.csv')
    import_from_csv(Link, 'links.csv')
    import_from_csv(Performance, 'performances.csv')

    db.session.commit()
    print("🎉 Tous les fichiers ont été importés avec succès.")
