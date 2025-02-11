import os
import re
from vsdx import VisioFile

def extract_shape_id_from_formula(formula_str):
    """
    Extrait l'ID de la forme dans une formule BeginX/EndX du type :
      PAR(PNT(Relation client.676!Connections.X2,Relation client.676!Connections.Y2))
    On récupère ici "676".
    """
    if not formula_str:
        return None
    # On cherche un motif du genre ".676!Connections"
    match = re.search(r'\.(\d+)!Connections', formula_str)
    return match.group(1) if match else None

def parse_geometry_for_connector(connector_shape):
    """
    Parcourt le XML de la shape (ShapeSheet),
    et renvoie (begin_id, end_id) si trouvable
    via les formules BeginX, EndX.
    """
    # ICI : on utilise shape.xml au lieu de shape._xml
    root = connector_shape.xml  # Un élément XML (ElementTree.Element)

    begin_id = None
    end_id = None

    # On parcourt tous les <Cell> pour trouver "BeginX", "EndX"
    for cell in root.iter('Cell'):
        cell_name = cell.get('N')  # "BeginX", "EndX", ...
        formula   = cell.get('F')  # ex: "PAR(PNT(Relation client.676!Connections.X2, ...)"

        if cell_name == "BeginX" and formula:
            begin_id = extract_shape_id_from_formula(formula)
        elif cell_name == "EndX" and formula:
            end_id = extract_shape_id_from_formula(formula)

    return (begin_id, end_id)

def parse_connectors_geometry():
    """
    1) Ouvre example.vsdx
    2) Pour chaque shape, si son master commence par T/D/N => c'est un connecteur
    3) Lit la ShapeSheet pour trouver (Begin, End).
    4) Affiche la forme source et la forme cible (END = côté flèche).
    """
    current_dir = os.path.dirname(__file__)
    vsdx_path = os.path.join(current_dir, "example.vsdx")

    doc = VisioFile(vsdx_path)
    if not doc.pages:
        print("Aucune page dans le document Visio.")
        return

    for page in doc.pages:
        print(f"\n=== Analyzing Page: {page.name} ===")

        shape_by_id = {sh.ID: sh for sh in page.all_shapes}

        for sh in page.all_shapes:
            master_lower = (sh.master_page.name.lower() if sh.master_page else "")
            sh_text = (sh.text or "").strip()

            # On ignore les shapes sans texte
            if not sh_text:
                continue

            # Vérifions si c'est un "connecteur" T/D/N
            if master_lower.startswith(('t','d','n')):
                beg_id, end_id = parse_geometry_for_connector(sh)
                if beg_id and end_id:
                    try:
                        beg_id_int = int(beg_id)
                        end_id_int = int(end_id)
                    except ValueError:
                        print(f"Shape {sh.ID} ({sh_text}) : impossible de convertir '{beg_id}'/'{end_id}' en entier.")
                        continue

                    shape_begin = shape_by_id.get(beg_id_int)
                    shape_end   = shape_by_id.get(end_id_int)
                    if shape_begin and shape_end:
                        text_begin = (shape_begin.text or "").strip()
                        text_end   = (shape_end.text or "").strip()

                        print(f"[{sh.master_page.name}] '{sh_text}' :")
                        print(f"   -> BEGIN: (ID={beg_id_int}) '{text_begin}'")
                        print(f"   -> END  : (ID={end_id_int}) '{text_end}'\n")
                    else:
                        print(f"   Shape(s) introuvable(s) pour begin={beg_id}, end={end_id}")
                else:
                    print(f"[{sh.master_page.name}] '{sh_text}' : Pas de BeginX/EndX dans le ShapeSheet")

    # Tentative de fermeture du doc
    try:
        doc.close_vsdx()
    except PermissionError as e:
        print(f"Ignored PermissionError: {e}")

if __name__ == "__main__":
    parse_connectors_geometry()
