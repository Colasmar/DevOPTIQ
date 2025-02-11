import os
from sqlalchemy import create_engine, inspect

# Chemin vers la base de données
db_path = os.path.abspath("Code/instance/optiq.db")
if not os.path.exists(db_path):
    print(f"ERREUR : Le fichier de base de données est introuvable : {db_path}")
    exit(1)

# Création de l'engin SQLAlchemy
engine = create_engine(f"sqlite:///{db_path}")

# Inspection des tables
inspector = inspect(engine)

def check_table_structure():
    """Vérifie la structure des tables dans la base de données."""
    expected_tables = {
        "activities": ["id", "name", "description"],
        "connections": ["id", "source_id", "target_id", "type", "description"],
        "data": ["id", "name", "type", "description", "layer"]
    }

    print(f"DEBUG : Tables attendues : {list(expected_tables.keys())}")
    tables = inspector.get_table_names()
    print(f"DEBUG : Tables présentes dans la base : {tables}")

    for table_name, expected_columns in expected_tables.items():
        if table_name not in tables:
            print(f"ERREUR : La table '{table_name}' est absente.")
            continue

        columns = [col["name"] for col in inspector.get_columns(table_name)]
        print(f"DEBUG : Colonnes de '{table_name}' : {columns}")

        for expected_col in expected_columns:
            if expected_col not in columns:
                print(f"ERREUR : Colonne manquante dans '{table_name}' : {expected_col}")
        
        extra_columns = [col for col in columns if col not in expected_columns]
        if extra_columns:
            print(f"ATTENTION : Colonnes supplémentaires dans '{table_name}' : {extra_columns}")

if __name__ == "__main__":
    check_table_structure()
