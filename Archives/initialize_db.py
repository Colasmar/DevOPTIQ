import os
import sys

# Ajouter dynamiquement le répertoire racine du projet dans sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Afficher les chemins actuels pour vérifier
print("Chemins actuels dans sys.path :")
for path in sys.path:
    print(path)

# Import des modules nécessaires
from Code.extensions import db
from Code.scripts.extract_visio import create_app
from Code.models.models import Activity  # Pour tester l'insertion

# Chemin absolu vers la base de données
db_directory = os.path.join(current_dir, "instance")
db_path = os.path.join(db_directory, "optiq.db")


# Créer le répertoire 'instance' s'il n'existe pas
if not os.path.exists(db_directory):
    os.makedirs(db_directory)
    print(f"Répertoire créé : {db_directory}")

# Vérifier si le fichier de base de données existe déjà
if not os.path.exists(db_path):
    print(f"Base de données non trouvée. Elle sera créée à l'emplacement : {db_path}")
else:
    print(f"Base de données existante détectée : {db_path}")

# Initialisation de l'application Flask et configuration
app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.abspath(db_path).replace('\\', '/')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
print(f"SQLAlchemy URI utilisé : {app.config['SQLALCHEMY_DATABASE_URI']}")

# Test de persistance explicite avec SQLAlchemy (ajouté ici)
from sqlalchemy import create_engine, text

print("Test de persistance avec SQLAlchemy...")
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
try:
    with engine.connect() as connection:
        # Création de la table de test
        connection.execute(text("CREATE TABLE IF NOT EXISTS persistence_test (id INTEGER PRIMARY KEY, name TEXT)"))
        # Insertion dans la table de test
        connection.execute(text("INSERT INTO persistence_test (name) VALUES (:name)"), {"name": "Persist Test"})
        # Lecture des données insérées
        result = connection.execute(text("SELECT id, name FROM persistence_test"))
        rows = [{"id": row[0], "name": row[1]} for row in result]  # Accès par indices
        print(f"Résultats de la table 'persistence_test': {rows}")
except Exception as e:
    print(f"Erreur lors du test de persistance : {e}")
finally:
    engine.dispose()


# Initialiser la base de données
try:
    with app.app_context():
        print("Tentative de création des tables...")
        db.create_all()
        print("Tables créées avec succès.")
except Exception as e:
    print(f"Erreur critique lors de la création des tables : {e}")
    import traceback
    traceback.print_exc()

# Vérification du fichier SQLite
db_physical_path = os.path.abspath(db_path)
print(f"Vérification physique du fichier SQLite : {db_physical_path}")
if os.path.exists(db_physical_path):
    print(f"Fichier de base de données trouvé à : {db_physical_path}")
else:
    print(f"Erreur : Le fichier de base de données n'existe pas à : {db_physical_path}")

# Test d'insertion pour vérifier la fonctionnalité de la base de données
try:
    with app.app_context():
        print("Insertion de test dans la table 'activities'...")
        test_activity = Activity(name="Test Activity", description="Validation de la base de données")
        db.session.add(test_activity)
        db.session.commit()
        print("Insertion de test réussie.")
except Exception as e:
    print(f"Erreur lors de l'insertion de test : {e}")
    import traceback
    traceback.print_exc()

# Vérification des données insérées
try:
    with app.app_context():
        print("Récupération des données insérées dans la table 'activities'...")
        activities = Activity.query.all()
        if activities:
            print(f"Données récupérées : {[{'id': a.id, 'name': a.name, 'description': a.description} for a in activities]}")
        else:
            print("Aucune donnée trouvée dans la table 'activities'.")
except Exception as e:
    print(f"Erreur lors de la récupération des données : {e}")
    import traceback
    traceback.print_exc()
