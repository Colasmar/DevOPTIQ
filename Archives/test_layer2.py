import os
from vsdx import VisioFile

def analyze_activity_connections(shapes, shape_by_id):
    """
    Analyse les connexions pour chaque activité.
    """
    activity_data = {}

    for shape in shapes:
        layer = shape.xml.find(".//{*}Cell[@N='LayerMember']")
        layer_value = layer.get("V") if layer is not None else "None"

        # Filtrage des formes inutiles
        if layer_value in ["2", "None"]:
            continue

        # Identifier les activités
        if layer_value == "1":  # Activités principales
            activity_data[shape.ID] = {
                "name": shape.text.strip(),
                "declenchante_in": [],
                "nourrissante_in": [],
                "declenchante_out": [],
                "nourrissante_out": [],
            }

        # Identifier les connexions pour les données
        elif layer_value in ["9", "10", "8"]:  # Données
            connections = analyze_connections(shape, shape_by_id)
            if connections["from_id"] in activity_data:  # Sortante
                source_name = activity_data[connections["from_id"]]["name"]
                if layer_value == "10":
                    activity_data[connections["from_id"]]["declenchante_out"].append(
                        f"{shape.text.strip()} (vers {activity_data[connections['to_id']]['name'] if connections['to_id'] in activity_data else 'inconnu'})"
                    )
                elif layer_value == "9":
                    activity_data[connections["from_id"]]["nourrissante_out"].append(
                        f"{shape.text.strip()} (vers {activity_data[connections['to_id']]['name'] if connections['to_id'] in activity_data else 'inconnu'})"
                    )
            if connections["to_id"] in activity_data:  # Entrante
                target_name = activity_data[connections["to_id"]]["name"]
                if layer_value == "10":
                    activity_data[connections["to_id"]]["declenchante_in"].append(
                        f"{shape.text.strip()} (depuis {activity_data[connections['from_id']]['name'] if connections['from_id'] in activity_data else 'inconnu'})"
                    )
                elif layer_value == "9":
                    activity_data[connections["to_id"]]["nourrissante_in"].append(
                        f"{shape.text.strip()} (depuis {activity_data[connections['from_id']]['name'] if connections['from_id'] in activity_data else 'inconnu'})"
                    )

    return activity_data

def analyze_connections(shape, shape_by_id):
    """
    Analyse les connexions d'une forme.
    """
    connections = {"from_id": None, "to_id": None}
    for cell in shape.xml.findall(".//{*}Cell"):
        n_val = cell.get("N")
        f_val = cell.get("F")
        if n_val == "BeginX":
            connections["from_id"] = f_val.split("Sheet.")[1].split("!")[0] if "Sheet." in f_val else None
        elif n_val == "EndX":
            connections["to_id"] = f_val.split("Sheet.")[1].split("!")[0] if "Sheet." in f_val else None
    return connections

def test_activities_with_enriched_data():
    """
    Test pour analyser les connexions entre activités et données avec enrichissement.
    """
    current_dir = os.path.dirname(__file__)
    vsdx_path = os.path.join(current_dir, "example.vsdx")

    if not os.path.exists(vsdx_path):
        print(f"ERROR: Fichier example.vsdx introuvable dans '{vsdx_path}'")
        return

    print(f"DEBUG: Ouverture du fichier Visio '{vsdx_path}'")
    doc = VisioFile(vsdx_path)
    pages = doc.pages
    print(f"DEBUG: Nombre de pages dans ce doc = {len(pages)}")
    if not pages:
        print("No pages in doc.")
        return

    page = pages[0]
    print(f"DEBUG: On analyse la page 0 nommée '{page.name}'")

    shapes = page.all_shapes
    print(f"DEBUG: Nombre de shapes = {len(shapes)}")

    # Dictionnaire des shapes par ID
    shape_by_id = {str(shape.ID): shape for shape in shapes}

    # Analyse des connexions et données
    activity_data = analyze_activity_connections(shapes, shape_by_id)

    # Affichage des résultats
    for activity_id, data in activity_data.items():
        print(f"Activité : {data['name']} (ID={activity_id})")
        print(f"  Données déclenchantes entrantes : {', '.join(data['declenchante_in']) if data['declenchante_in'] else 'None'}")
        print(f"  Données nourrissantes entrantes : {', '.join(data['nourrissante_in']) if data['nourrissante_in'] else 'None'}")
        print(f"  Données déclenchantes sortantes : {', '.join(data['declenchante_out']) if data['declenchante_out'] else 'None'}")
        print(f"  Données nourrissantes sortantes : {', '.join(data['nourrissante_out']) if data['nourrissante_out'] else 'None'}")

    # Fermeture du fichier (pour éviter le PermissionError).
    try:
        doc.close_vsdx()
    except PermissionError as e:
        print(f"PermissionError ignored: {e}")

if __name__ == "__main__":
    test_activities_with_enriched_data()
    print("DEBUG: Fin du script test_activities_with_enriched_data.py")
