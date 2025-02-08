import os
from vsdx import VisioFile

def analyze_visio_file():
    current_dir = os.path.dirname(__file__)
    vsdx_path = os.path.join(current_dir, "example.vsdx")

    doc = None
    try:
        doc = VisioFile(vsdx_path)
        if not doc.pages:
            print("No pages in the document.")
            return

        for page in doc.pages:
            print(f"Analyzing page: {page.name}\n")

            # 1) On prépare trois listes : données déclenchantes, nourrissantes, activités
            declenchante_data = []
            nourrissante_data = []
            activities = []

            shape_by_id = {sh.ID: sh for sh in page.all_shapes}

            # --- ÉTAPE A : Classer les formes ---
            for shape in page.all_shapes:
                master_raw = shape.master_page.name if shape.master_page else "No Master"
                master_name = master_raw.lower()
                text = (shape.text or "").strip()

                # Filtres pour ignorer les shapes "inutiles"
                if (
                    not text or
                    master_name in [
                        "swimlane", "couloir color", "separator",
                        "cff container", "phase list", "document",
                        "feedback", "rounded process", "no master"
                    ]
                ):
                    continue

                # Distinction : T ou D => Déclenchante, N => Nourrissante, sinon => Activité
                if master_name.startswith(('t', 'd')):
                    declenchante_data.append(shape)
                elif master_name.startswith('n'):
                    nourrissante_data.append(shape)
                else:
                    activities.append(shape)

            # --- ÉTAPE B : Analyser chaque activité ---
            activity_info_list = []
            for activity in activities:
                a_id = activity.ID
                a_text = (activity.text or "").strip()
                a_master = (activity.master_page.name if activity.master_page else "??")

                incoming_declenchante = []
                incoming_nourrissante = []
                outgoing_values = []

                # Si l'activité a des connexions
                if hasattr(activity, 'connects') and activity.connects:
                    for conn in activity.connects:
                        from_id, to_id = conn.from_id, conn.to_id
                        src = shape_by_id.get(from_id)
                        dst = shape_by_id.get(to_id)
                        if not (src and dst):
                            continue

                        src_master = (src.master_page.name.lower() if src.master_page else "")
                        dst_master = (dst.master_page.name.lower() if dst.master_page else "")

                        # SI l'activité est la cible => flux entrant
                        if a_id == to_id:
                            # => la source, c'est 'src'
                            # On regarde son type (déclenchante, nourrissante...)
                            if src_master.startswith(('t', 'd')):
                                incoming_declenchante.append(src.text.strip())
                            elif src_master.startswith('n'):
                                incoming_nourrissante.append(src.text.strip())
                            else:
                                # autre activité -> flux entrant ?
                                pass

                        # SI l'activité est la source => flux sortant
                        elif a_id == from_id:
                            outgoing_values.append(dst.text.strip())

                activity_info_list.append({
                    "id": a_id,
                    "text": a_text,
                    "master": a_master,
                    "incoming_declenchante": incoming_declenchante,
                    "incoming_nourrissante": incoming_nourrissante,
                    "outgoing_values": outgoing_values
                })

            # --- ÉTAPE C : Affichage des activités ---
            for info in activity_info_list:
                print(f"Activity: {info['text']} (ID={info['id']}, Master={info['master']})")
                d_in = ", ".join(info['incoming_declenchante']) or "None"
                n_in = ", ".join(info['incoming_nourrissante']) or "None"
                val_out = ", ".join(info['outgoing_values']) or "None"
                print(f" - Données déclenchantes entrantes : {d_in}")
                print(f" - Données nourrissantes entrantes : {n_in}")
                print(f" - Valeurs ajoutées sortantes     : {val_out}\n")

            # --- ÉTAPE D : Affichage des données déclenchantes ---
            print("Données déclenchantes:")
            for data in declenchante_data:
                dt_text = (data.text or "").strip()
                dt_id = data.ID

                from_shapes = []
                to_shapes = []

                if hasattr(data, 'connects') and data.connects:
                    for conn in data.connects:
                        f_id, t_id = conn.from_id, conn.to_id
                        # Si la donnée est la source => flux "data -> other"
                        if f_id == dt_id and t_id != dt_id and t_id in shape_by_id:
                            to_shapes.append(shape_by_id[t_id].text.strip())
                        # Si la donnée est la cible => flux "other -> data"
                        elif t_id == dt_id and f_id != dt_id and f_id in shape_by_id:
                            from_shapes.append(shape_by_id[f_id].text.strip())

                if from_shapes or to_shapes:
                    print(f"Donnée déclenchante : {dt_text} (ID={dt_id})")
                    print(f"  Depuis : {', '.join(from_shapes) or 'None'}")
                    print(f"  Vers   : {', '.join(to_shapes) or 'None'}")

            # --- ÉTAPE E : Affichage des données nourrissantes ---
            print("\nDonnées nourrissantes:")
            for data in nourrissante_data:
                dt_text = (data.text or "").strip()
                dt_id = data.ID

                from_shapes = []
                to_shapes = []

                if hasattr(data, 'connects') and data.connects:
                    for conn in data.connects:
                        f_id, t_id = conn.from_id, conn.to_id
                        # Si la donnée est la source => flux "data -> other"
                        if f_id == dt_id and t_id != dt_id and t_id in shape_by_id:
                            to_shapes.append(shape_by_id[t_id].text.strip())
                        # Si la donnée est la cible => flux "other -> data"
                        elif t_id == dt_id and f_id != dt_id and f_id in shape_by_id:
                            from_shapes.append(shape_by_id[f_id].text.strip())

                if from_shapes or to_shapes:
                    print(f"Donnée nourrissante : {dt_text} (ID={dt_id})")
                    print(f"  Depuis : {', '.join(from_shapes) or 'None'}")
                    print(f"  Vers   : {', '.join(to_shapes) or 'None'}")

    except PermissionError as e:
        print(f"Permission error ignored: {e}")
    finally:
        if doc:
            try:
                doc.close_vsdx()
            except PermissionError as e:
                print(f"Permission error during closure ignored: {e}")


if __name__ == "__main__":
    analyze_visio_file()
