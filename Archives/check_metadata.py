import os
import sys

# Ajout dynamique des chemins pour éviter les erreurs d'importation
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from Code.extensions import db
from Code.models.models import Activities, Connections, Data

print("Tables dans db.metadata :")
for table_name in db.metadata.tables.keys():
    print(f"- {table_name}")

print("Modèles déclarés :")
print(f"Activities: {Activities.__tablename__}")
print(f"Connections: {Connections.__tablename__}")
print(f"Data: {Data.__tablename__}")
