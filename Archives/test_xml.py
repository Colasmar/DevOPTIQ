import os
from vsdx import VisioFile

def analyze_connections_with_layers(shape, shape_by_id):
    """
    Analyse les connexions et récupère l'information de LayerMembership.
    """
    connections = {"from_id": None, "to_id": None, "layer_member": None}

    for cell in shape.xml.findall(".//{*}Cell"):
        n_val = cell.get("N")  # Nom de la cellule
        f_val = cell.get("F")  # Formule de la cellule
        v_val = cell.get("V")  # Valeur de la cellule

        if n_val == "BeginX":
            connections["from_id"] = f_val.split("Sheet.")[1].split("!")[0] if "Sheet." in f_val else None
        elif n_val == "EndX":
            connections["to_id"] = f_val.split("Sheet.")[1].split("!")[0] if "Sheet." in f_val else None
        elif n_val == "LayerMember":
            connections["layer_member"] = v_val

    return connections

def test_layer_membership():
    """
    Test pour analyser les connexions avec gestion des Layer Memberships.
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

    # Analyse des connexions
    for shape in shapes:
        if shape.master_page and shape.text.strip():
            print(f"\nDEBUG: Shape ID={shape.ID}, text='{shape.text.strip()}', master='{shape.master_page.name}'")
            connections = analyze_connections_with_layers(shape, shape_by_id)
            from_id = connections["from_id"]
            to_id = connections["to_id"]
            layer_member = connections["layer_member"]
            from_text = shape_by_id[from_id].text.strip() if from_id and from_id in shape_by_id else "None"
            to_text = shape_by_id[to_id].text.strip() if to_id and to_id in shape_by_id else "None"
            print(f"  Depuis : {from_text} (ID={from_id})")
            print(f"  Vers : {to_text} (ID={to_id})")
            print(f"  Layer Membership : {layer_member}")

    # Fermeture du fichier (pour éviter le PermissionError).
    try:
        doc.close_vsdx()
    except PermissionError as e:
        print(f"PermissionError ignored: {e}")

if __name__ == "__main__":
    test_layer_membership()
    print("DEBUG: Fin du script test_layer_membership.py")
