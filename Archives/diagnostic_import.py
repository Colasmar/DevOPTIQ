import os
import sys

# Étape 1 : Ajouter explicitement le répertoire racine au début de sys.path
project_root = os.path.dirname(os.path.abspath(__file__))  # Dossier 'Code'
sys.path.insert(0, os.path.dirname(project_root))  # Ajouter le dossier parent de 'Code'

print("DEBUG: Chemins dans sys.path après modification :")
for path in sys.path:
    print(f"  - {path}")

# Étape 2 : Vérification des fichiers critiques
extensions_path = os.path.join(project_root, 'extensions.py')
models_path = os.path.join(project_root, 'models', 'models.py')

print(f"DEBUG: Vérification des fichiers critiques :")
print(f"  - extensions.py : {'Présent' if os.path.exists(extensions_path) else 'Manquant'}")
print(f"  - models.py : {'Présent' if os.path.exists(models_path) else 'Manquant'}")

# Étape 3 : Import des modules
try:
    from Code.extensions import db
    from Code.models.models import Activity, Data, Connection
    print("DEBUG: Import des modules réussi.")
except Exception as e:
    print(f"ERREUR : Problème lors de l'import. Détails : {e}")
