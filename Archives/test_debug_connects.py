import os
from vsdx import VisioFile

def debug_connects_for_data():
    current_dir = os.path.dirname(__file__)
    vsdx_path = os.path.join(current_dir, "example.vsdx")  # adaptez si besoin

    doc = VisioFile(vsdx_path)
    if not doc.pages:
        print("No pages in the document.")
        return

    for page in doc.pages:
        print(f"\n=== Page: {page.name} ===")
        shape_by_id = {sh.ID: sh for sh in page.all_shapes}

        # On va extraire toutes les "données" (T, D, N) comme vous faites
        declenchante_data = []
        nourrissante_data = []

        for sh in page.all_shapes:
            master = sh.master_page.name.lower() if sh.master_page else "no master"
            txt = (sh.text or "").strip()
            if not txt:
                continue

            if master.startswith(('t','d')):
                declenchante_data.append(sh)
            elif master.startswith('n'):
                nourrissante_data.append(sh)

        # Fonction utilitaire pour imprimer tous les connects
        def print_connects(data_shape):
            data_id = data_shape.ID
            data_text = (data_shape.text or "").strip()
            data_master = (data_shape.master_page.name if data_shape.master_page else "??")
            print(f"\nData shape: '{data_text}' (ID={data_id}, master='{data_master}')")

            if hasattr(data_shape, 'connects') and data_shape.connects:
                for i, conn in enumerate(data_shape.connects, start=1):
                    f_id, t_id = conn.from_id, conn.to_id
                    f_txt = shape_by_id[f_id].text.strip() if f_id in shape_by_id else "??"
                    t_txt = shape_by_id[t_id].text.strip() if t_id in shape_by_id else "??"

                    print(f"  Conn #{i}: from_id={f_id} ('{f_txt}')  => to_id={t_id} ('{t_txt}')")
            else:
                print("  Aucune connexion enregistrée.")
        
        # Affichage
        print("** Données déclenchantes **")
        for data in declenchante_data:
            print_connects(data)

        print("\n** Données nourrissantes **")
        for data in nourrissante_data:
            print_connects(data)

    # Tentative de fermeture
    try:
        doc.close_vsdx()
    except PermissionError as e:
        print(f"Ignored PermissionError: {e}")


if __name__ == "__main__":
    debug_connects_for_data()
