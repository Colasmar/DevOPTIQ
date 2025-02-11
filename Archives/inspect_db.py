from sqlalchemy import create_engine, inspect

# Utilisation du chemin absolu pour s'assurer que la base est accessible
engine = create_engine('sqlite:///instance/optiq.db')
inspector = inspect(engine)

print("Tables existantes dans la base de données :")
tables = inspector.get_table_names()
if tables:
    print(tables)
else:
    print("Aucune table trouvée.")
