import os
import sys
from flask import Flask
from vsdx import VisioFile
from sqlalchemy.exc import IntegrityError

# Ajouter dynamiquement le chemin du projet
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from Code.extensions import db
from Code.models.models import Activities, Data, Connections

def create_app():
    """Initialise l'application Flask."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.abspath('Code/instance/optiq.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def reset_database():
    """Réinitialise les bases de données."""
    db.session.query(Connections).delete()
    db.session.query(Data).delete()
    db.session.query(Activities).delete()
    db.session.commit()
    print("INFO : Les bases de données ont été réinitialisées avec succès.")

def process_visio_file(vsdx_path):
    """Analyse et importe les données depuis un fichier Visio."""
    if not os.path.exists(vsdx_path):
        print(f"ERREUR : Le fichier Visio '{vsdx_path}' est introuvable.")
        return

    with VisioFile(vsdx_path) as visio:
        shape_by_id = {}
        for page in visio.pages:
            print(f"INFO : Analyse de la page : {page.name}")
            shapes = page.all_shapes
            shape_by_id.update({str(shape.ID): shape for shape in shapes})
            for shape in shapes:
                process_shape(shape, shape_by_id)

def process_shape(shape, shape_by_id):
    """Traite chaque forme en fonction de son type."""
    layer = shape.xml.find(".//{*}Cell[@N='LayerMember']")
    layer_value = layer.get("V") if layer is not None else "None"

    if layer_value == "1":  # Activités
        add_activity(shape)
    elif layer_value in ["9", "10"]:  # Données nourrissantes ou déclenchantes
        add_data_and_connections(shape, shape_by_id, layer_value)
    elif layer_value in ["6", "8"]:  # Formes spéciales
        add_special_shape(shape, layer_value)

def add_activity(shape):
    """Ajoute une activité dans la base."""
    name = shape.text.strip()
    try:
        activity = Activities(name=name)
        db.session.add(activity)
        db.session.flush()
        print(f"INFO : Activité ajoutée : {name}")
    except IntegrityError:
        db.session.rollback()
        print(f"INFO : Activité existante : {name}")

def add_data_and_connections(shape, shape_by_id, layer_value):
    """Ajoute des données et crée les connexions entrantes/sortantes."""
    data_name = shape.text.strip()
    data_type = "déclenchante" if layer_value == "10" else "nourrissante"
    connections = analyze_connections(shape)

    try:
        data = Data(name=data_name, type=data_type)
        db.session.add(data)
        db.session.flush()
        print(f"INFO : Donnée ajoutée : {data_name} ({data_type})")

        if connections["from_id"]:
            connection = Connections(
                source_id=connections["from_id"],
                target_id=data.id,
                type="output"
            )
            db.session.add(connection)
        if connections["to_id"]:
            connection = Connections(
                source_id=data.id,
                target_id=connections["to_id"],
                type="input"
            )
            db.session.add(connection)
        db.session.commit()

    except IntegrityError:
        db.session.rollback()
        print(f"INFO : Donnée existante : {data_name}")

def add_special_shape(shape, layer_value):
    """Ajoute une forme spéciale dans la base."""
    name = shape.text.strip()
    special_type = "Résultat" if layer_value == "6" else "Retour"

    try:
        data = Data(name=name, type=special_type)
        db.session.add(data)
        db.session.flush()
        print(f"INFO : Forme spéciale ajoutée : {name} ({special_type})")
    except IntegrityError:
        db.session.rollback()
        print(f"INFO : Forme spéciale existante : {name}")

def analyze_connections(shape):
    """Analyse les connexions d'une forme."""
    connections = {"from_id": None, "to_id": None}
    for cell in shape.xml.findall(".//{*}Cell"):
        n_val = cell.get("N")
        f_val = cell.get("F")
        if n_val == "BeginX":
            connections["from_id"] = extract_shape_id(f_val)
        elif n_val == "EndX":
            connections["to_id"] = extract_shape_id(f_val)
    return connections

def extract_shape_id(f_val):
    """Extrait l'ID d'une forme connectée."""
    if "Sheet." in f_val:
        return f_val.split("Sheet.")[1].split("!")[0]
    return None

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        reset_database()
        process_visio_file("Code/example.vsdx")
