import os
import xml.etree.ElementTree as ET
from vsdx import VisioFile

def debug_dump_connector():
    print("DEBUG: Entering debug_dump_connector() ...")

    current_dir = os.path.dirname(__file__)
    vsdx_path = os.path.join(current_dir, "example.vsdx")

    print(f"DEBUG: Computed vsdx_path = {vsdx_path}")
    if not os.path.exists(vsdx_path):
        print("ERROR: example.vsdx not found at this path!")
        return

    # On essaye d'ouvrir le fichier
    print("DEBUG: Attempting to open VisioFile...")
    doc = VisioFile(vsdx_path)
    print("DEBUG: VisioFile opened successfully (no exception).")

    pages_count = len(doc.pages)
    print(f"DEBUG: doc.pages count = {pages_count}")
    if pages_count == 0:
        print("Aucune page dans le document Visio.")
        return

    for page_index, page in enumerate(doc.pages):
        print(f"\n=== Page index={page_index}, name={page.name} ===")
        shape_by_id = {sh.ID: sh for sh in page.all_shapes}

        total_shapes = len(page.all_shapes)
        print(f"DEBUG: total_shapes in this page = {total_shapes}")
        if total_shapes == 0:
            print("No shapes in this page.")
            continue

        for sh in page.all_shapes:
            master_lower = (sh.master_page.name.lower() if sh.master_page else "")
            text = (sh.text or "").strip()

            print(f"  - Shape ID={sh.ID}, text='{text}', master='{sh.master_page.name if sh.master_page else ''}'")
            # On n'exclut pas encore les shapes vides, on veut tout voir
            # juste pour debug

            # Dump complet du XML
            # (Si trop verbeux, on peut le limiter aux shapes T/D/N)
            root = sh.xml
            print("    -> Dumping partial XML:")
            ET.dump(root)

    # Fermeture du doc
    try:
        doc.close_vsdx()
    except PermissionError as e:
        print(f"Ignored PermissionError: {e}")

if __name__ == "__main__":
    debug_dump_connector()
    print("DEBUG: End of debug_dump_connector script.")
