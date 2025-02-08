import os
import sys

from Code.extensions import db
from Code.models.models import Activity, Data, Connection
from vsdx import VisioFile


def process_visio_file(vsdx_path):
    """
    Process and extract data from a Visio file and store them in the database.
    """
    try:
        with VisioFile(vsdx_path) as visio:
            for page in visio.pages:
                print(f"INFO : Analyse de la page : {page.name}")
                shapes = page.all_shapes
                process_shapes(shapes)

    except Exception as e:
        print(f"ERROR: Une erreur s'est produite lors du traitement du fichier Visio : {e}")
    finally:
        try:
            visio.close_vsdx()
        except Exception as e:
            print(f"WARNING: Impossible de fermer le fichier Visio proprement : {e}")


def process_shapes(shapes):
    """
    Process each shape in the Visio page.
    """
    activity_shapes = {}
    special_shapes = {}
    data_shapes = {}

    for shape in shapes:
        text = shape.text.strip() if shape.text else "Forme sans texte"
        layer = get_layer(shape)

        # Identify the type of shape
        if layer == "Activity":
            activity_shapes[shape.ID] = process_activity(shape)
        elif layer in ["Result", "Return"]:
            special_shapes[shape.ID] = process_special_shape(shape, layer)
        elif layer in ["Trigger", "Nourishing"]:
            data_shapes[shape.ID] = process_data(shape, layer)

    process_connections(shapes, activity_shapes, special_shapes, data_shapes)


def process_activity(shape):
    """
    Process an activity shape and save it to the database.
    """
    activity = Activity(name=shape.text.strip())
    db.session.add(activity)
    db.session.commit()
    print(f"INFO : Activité ajoutée : {activity.name}")
    return activity


def process_special_shape(shape, layer):
    """
    Process a special shape (Result, Return) and save it to the database.
    """
    special_shape = Data(name=shape.text.strip(), type=layer)
    db.session.add(special_shape)
    db.session.commit()
    print(f"INFO : Forme spéciale ajoutée : {special_shape.name} ({layer})")
    return special_shape


def process_data(shape, layer):
    """
    Process a data shape and save it to the database.
    """
    data_type = "déclenchante" if layer == "Trigger" else "nourrissante"
    data = Data(name=shape.text.strip(), type=data_type)
    db.session.add(data)
    db.session.commit()
    print(f"INFO : Donnée ajoutée : {data.name} ({data_type})")
    return data


def process_connections(shapes, activity_shapes, special_shapes, data_shapes):
    """
    Process connections between shapes and save them to the database.
    """
    for shape in shapes:
        if not shape.connectors:
            continue

        for connector in shape.connectors:
            from_shape = connector.from_shape
            to_shape = connector.to_shape

            if from_shape.ID in data_shapes and to_shape.ID in activity_shapes:
                connection = Connection(
                    source_id=data_shapes[from_shape.ID].id,
                    target_id=activity_shapes[to_shape.ID].id,
                    type="input"
                )
                db.session.add(connection)
                db.session.commit()
                print(f"INFO : Connexion ajoutée : {connection}")
            elif from_shape.ID in activity_shapes and to_shape.ID in data_shapes:
                connection = Connection(
                    source_id=activity_shapes[from_shape.ID].id,
                    target_id=data_shapes[to_shape.ID].id,
                    type="output"
                )
                db.session.add(connection)
                db.session.commit()
                print(f"INFO : Connexion ajoutée : {connection}")


def get_layer(shape):
    """
    Retrieve the layer of a shape.
    """
    cell = shape.xml.find(".//{*}Cell[@N='LayerMember']")
    return cell.get("V") if cell is not None else None


if __name__ == "__main__":
    vsdx_path = os.path.join("Code", "example.vsdx")
    process_visio_file(vsdx_path)
