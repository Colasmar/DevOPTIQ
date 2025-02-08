import os
import sys

# Ajuster le chemin
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

try:
    from Code.models.models import Activities, Connections, Data
    print("Importation réussie.")
except Exception as e:
    print(f"Erreur lors de l'importation des modèles : {e}")
