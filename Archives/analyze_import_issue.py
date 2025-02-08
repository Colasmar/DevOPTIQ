import os
import sys

# Ajouter dynamiquement le répertoire racine du projet
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Afficher les chemins de sys.path
print("DEBUG: Chemins dans sys.path :")
for path in sys.path:
    print(f"  - {path}")

# Vérification des fichiers critiques
extensions_path = os.path.join(project_root, 'Code', 'extensions.py')
models_path = os.path.join(project_root, 'Code', 'models', 'models.py')

print("\nDEBUG: Vérification des fichiers critiques...")
print(f"  - extensions.py : {'Présent' if os.path.exists(extensions_path) else 'Manquant'} (Path : {extensions_path})")
print(f"  - models.py : {'Présent' if os.path.exists(models_path) else 'Manquant'} (Path : {models_path})")

# Test d'importation des modules
try:
    from Code.extensions import db
    from Code.models.models import Activity, Data, Connection
    print("\nDEBUG: Importation des modules réussie.")
except ImportError as e:
    print(f"\nERREUR : Problème d'importation des modules. Détails : {e}")
