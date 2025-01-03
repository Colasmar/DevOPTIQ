import os
from vsdx import VisioFile

def analyze_activity_connections(shapes, shape_by_id):
    """
    Analyse les connexions pour chaque activité.
    """
    activity_data = {}
    special_shapes = {}

    for shape in shapes:
        layer = shape.xml.find(".//{*}Cell[@N='LayerMember']")
        layer_value = layer.get("V") if layer is not None else "None"

        # Identifier les activités principales
        if layer_value == "1":
            activity_data[shape.ID] = {
                "name": shape.text.strip(),
                "declenchante_in": [],
                "nourrissante_in": [],
                "declenchante_out": [],
                "nourrissante_out": [],
            }

        # Identifier les formes spéciales (Retour, Résultat)
        elif layer_value in ["8", "6"]:  # Ajouter les layers correspondants
            special_shapes[shape.ID] = {
                "name": shape.text.strip(),
                "declenchante_in": [],
                "nourrissante_in": [],
                "declenchante_out": [],
                "nourrissante_out": [],
            }

        # Identifier les connexions pour les données
        elif layer_value in ["9", "10"]:  # Données nourrissantes et déclenchantes
            connections = analyze_connections(shape, shape_by_id)
            from_id = connections["from_id"]
            to_id = connections["to_id"]

            # Traiter les données sortantes
            if from_id in activity_data:
                target_name = (
                    special_shapes[to_id]["name"] if to_id in special_shapes else
                    activity_data[to_id]["name"] if to_id in activity_data else "inconnu"
                )
                if layer_value == "10":
                    activity_data[from_id]["declenchante_out"].append(f"{shape.text.strip()} (vers {target_name})")
                elif layer_value == "9":
                    activity_data[from_id]["nourrissante_out"].append(f"{shape.text.strip()} (vers {target_name})")

            # Traiter les données entrantes
            if to_id in activity_data:
                source_name = (
                    special_shapes[from_id]["name"] if from_id in special_shapes else
                    activity_data[from_id]["name"] if from_id in activity_data else "inconnu"
                )
                if layer_value == "10":
                    activity_data[to_id]["declenchante_in"].append(f"{shape.text.strip()} (depuis {source_name})")
                elif layer_value == "9":
                    activity_data[to_id]["nourrissante_in"].append(f"{shape.text.strip()} (depuis {source_name})")

            # Gérer les formes spéciales
            if from_id in special_shapes:
                target_name = (
                    activity_data[to_id]["name"] if to_id in activity_data else "inconnu"
                )
                if layer_value == "10":
                    special_shapes[from_id]["declenchante_out"].append(f"{shape.text.strip()} (vers {target_name})")
                elif layer_value == "9":
                    special_shapes[from_id]["nourrissante_out"].append(f"{shape.text.strip()} (vers {target_name})")

            if to_id in special_shapes:
                source_name = (
                    activity_data[from_id]["name"] if from_id in activity_data else "inconnu"
                )
                if layer_value == "10":
                    special_shapes[to_id]["declenchante_in"].append(f"{shape.text.strip()} (depuis {source_name})")
                elif layer_value == "9":
                    special_shapes[to_id]["nourrissante_in"].append(f"{shape.text.strip()} (depuis {source_name})")

    return activity_data, special_shapes

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

def test_activities_with_special_shapes():
    """
    Test pour analyser les connexions entre activités et formes spéciales.
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
    activity_data, special_shapes = analyze_activity_connections(shapes, shape_by_id)

    # Affichage des résultats
    print("\n=== Activités ===")
    for activity_id, data in activity_data.items():
        print(f"Activité : {data['name']} (ID={activity_id})")
        print(f"  Données déclenchantes entrantes : {', '.join(data['declenchante_in']) if data['declenchante_in'] else 'None'}")
        print(f"  Données nourrissantes entrantes : {', '.join(data['nourrissante_in']) if data['nourrissante_in'] else 'None'}")
        print(f"  Données déclenchantes sortantes : {', '.join(data['declenchante_out']) if data['declenchante_out'] else 'None'}")
        print(f"  Données nourrissantes sortantes : {', '.join(data['nourrissante_out']) if data['nourrissante_out'] else 'None'}")

    print("\n=== Formes spéciales (Résultat, Retour) ===")
    for shape_id, data in special_shapes.items():
        print(f"Forme spéciale : {data['name']} (ID={shape_id})")
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
    test_activities_with_special_shapes()
    print("DEBUG: Fin du script test_activities_with_special_shapes.py")
