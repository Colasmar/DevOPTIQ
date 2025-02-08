import os
import sys

# Définir les chemins attendus
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
code_dir = os.path.join(project_root, "Code")
extensions_path = os.path.join(code_dir, "extensions.py")
models_path = os.path.join(code_dir, "models", "models.py")

# Vérifier si les chemins sont dans sys.path
print("DEBUG: Chemins dans sys.path :")
for path in sys.path:
    print(f"  - {path}")

# Ajouter le chemin du projet si nécessaire
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print("DEBUG: Chemin du projet ajouté à sys.path")

# Vérification des fichiers critiques
print("\nDEBUG: Vérification des fichiers critiques...")
print(f"  - extensions.py : {'Présent' if os.path.exists(extensions_path) else 'Manquant'} (Path : {extensions_path})")
print(f"  - models.py : {'Présent' if os.path.exists(models_path) else 'Manquant'} (Path : {models_path})")

# Tentative d'importation des modules
try:
    from Code.extensions import db
    from Code.models.models import Activity, Data, Connection
    print("\nDEBUG: Importation des modules réussie.")
except ImportError as e:
    print(f"ERREUR : Problème d'importation des modules. Détails : {e}")
