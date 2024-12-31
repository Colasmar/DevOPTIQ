import os
from vsdx import VisioFile

def list_custom_connectors():
    current_dir = os.path.dirname(__file__)
    vsdx_path = os.path.join(current_dir, "example.vsdx")

    doc = None
    try:
        doc = VisioFile(vsdx_path)

        if not doc.pages:
            print("Aucune page dans le document.")
            return

        page = doc.pages[0]
        print(f"Page : {page.name}")

        all_shapes = page.all_shapes
        shape_by_id = {sh.ID: sh for sh in all_shapes}

        for sh in all_shapes:
            mp = sh.master_page
            master_name = mp.name if (mp and mp.name) else "Aucun master"

            # S'il a l'attribut 'connects'
            if hasattr(sh, 'connects') and sh.connects:
                # sh.connects n'est pas vide
                text_sh = (sh.text or "").strip()
                print(f"\nShape ID={sh.ID} : texte='{text_sh}', master='{master_name}'")
                print(f" -> connect_count = {len(sh.connects)}")

                for c in sh.connects:
                    from_id, to_id = c.from_id, c.to_id
                    source_sh = shape_by_id.get(from_id)
                    target_sh = shape_by_id.get(to_id)

                    # Récupérer le texte éventuel
                    source_text = (source_sh.text or "").strip() if source_sh else "??"
                    target_text = (target_sh.text or "").strip() if target_sh else "??"

                    print(f"    from_id={from_id} ('{source_text}')  => to_id={to_id} ('{target_text}')")

    except PermissionError as e:
        print(f"PermissionError ignoré : {e}")
    finally:
        if doc:
            try:
                doc.close_vsdx()
            except PermissionError as e:
                print(f"PermissionError (ignoré lors du close) : {e}")


if __name__ == "__main__":
    list_custom_connectors()
