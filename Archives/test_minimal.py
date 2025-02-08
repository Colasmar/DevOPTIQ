import os
from vsdx import VisioFile

def debug_single_shape(shape):
    print(f"DEBUG: Shape ID={shape.ID}, text='{shape.text or ''}', master='{shape.master_page.name if shape.master_page else ''}'")
    root = shape.xml  # important : shape.xml (pas shape._xml)

    # Essai 1 : iteration naive
    print("DEBUG: Iteration naive root.iter('Cell')")
    for cell in root.iter('Cell'):
        n_val = cell.get('N')  # ex: "BeginX"
        f_val = cell.get('F')  # ex: "PAR(PNT(...))"
        print(f"  Found Cell N='{n_val}' F='{f_val}'")

    # Essai 2 : iteration namespace wildcard
    print("DEBUG: Iteration wildcard root.findall('.//{*}Cell')")
    for cell in root.findall('.//{*}Cell'):
        n_val = cell.get('N')
        f_val = cell.get('F')
        print(f"  (Wildcard) Found Cell N='{n_val}' F='{f_val}'")

def test_debug_shape():
    """
    Ouvre example.vsdx, répertorie les IDs des shapes,
    et appelle debug_single_shape() sur une cible spécifique.
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
    
    # Affichage de toutes les IDs disponibles
    print("DEBUG: Liste des IDs disponibles :")
    for sh in shapes:
        print(f"  Shape ID={sh.ID}, text='{sh.text or ''}', master='{sh.master_page.name if sh.master_page else ''}'")

    # On cherche la shape ID=681
    target_id = "681"  # Convertir l'ID cible en chaîne pour cohérence
    target_shape = None

    for sh in shapes:
        print(f"Comparing shape ID='{sh.ID}' to target_id='{target_id}'")
        if str(sh.ID) == target_id:  # Forcer la comparaison avec des chaînes
            target_shape = sh
            break

    if not target_shape:
        print(f"Aucune shape trouvée avec ID={target_id}")
    else:
        debug_single_shape(target_shape)

    # Fermeture du fichier (pour éviter le PermissionError).
    try:
        doc.close_vsdx()
    except PermissionError as e:
        print(f"PermissionError ignored: {e}")

if __name__ == '__main__':
    test_debug_shape()
    print("DEBUG: Fin du script test_minimal.py")
