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

# Chemin absolu vers la base de données
db_directory = os.path.join("C:", "Temp", "instance")
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
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path.replace('\\', '/')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

print(f"SQLAlchemy URI utilisé : {app.config['SQLALCHEMY_DATABASE_URI']}")

# Initialiser la base de données
try:
    with app.app_context():
        print(f"Tentative de connexion avec SQLAlchemy URI : {app.config['SQLALCHEMY_DATABASE_URI']}")
        db.create_all()
        print("Tables créées avec succès dans la base de données.")
except Exception as e:
    print(f"Erreur critique lors de la création des tables : {e}")
    import traceback
    traceback.print_exc()
