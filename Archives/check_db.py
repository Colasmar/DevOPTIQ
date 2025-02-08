import os

# Chemin attendu pour la base de données
db_path = os.path.abspath("Code/instance/optiq.db")
print(f"DEBUG: Chemin complet vers la base de données : {db_path}")

# Vérification de l'existence du fichier
if not os.path.exists(db_path):
    print("ERREUR : Le fichier de base de données est introuvable à l'emplacement spécifié.")
else:
    print("DEBUG : Le fichier de base de données existe.")
