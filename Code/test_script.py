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
            activities = []
            declenchante_data = []
            nourrissante_data = []

            shape_by_id = {sh.ID: sh for sh in page.all_shapes}
            for shape in page.all_shapes:
                master_name = shape.master_page.name if shape.master_page else "No Master"
                text = (shape.text or "").strip()

                # Exclude irrelevant shapes based on master name or empty text
                if master_name.lower() in ["swimlane", "couloir color", "separator", "cff container", "phase list", "document", "feedback", "rounded process", "no master"] or not text:
                    continue

                # Identify data vs activity
                if master_name.lower().startswith(('t', 'd')):
                    declenchante_data.append(shape)
                elif master_name.lower().startswith('n'):
                    nourrissante_data.append(shape)
                else:
                    # Process connections to determine type and direction
                    incoming_declenchante = []
                    incoming_nourrissante = []
                    outgoing_values = []

                    if hasattr(shape, 'connects') and shape.connects:
                        for connect in shape.connects:
                            from_id, to_id = connect.from_id, connect.to_id
                            source = shape_by_id.get(from_id)
                            target = shape_by_id.get(to_id)

                            if source and target:
                                source_text = (source.text or "").strip()
                                target_text = (target.text or "").strip()
                                connection_type = "Declenchante" if source.master_page and source.master_page.name.lower().startswith(('t', 'd')) else "Nourrissante"

                                # Determine direction of connection
                                if shape.ID == to_id:  # Incoming connection
                                    if connection_type == "Declenchante":
                                        incoming_declenchante.append(source_text)
                                    else:
                                        incoming_nourrissante.append(source_text)
                                elif shape.ID == from_id:  # Outgoing connection
                                    outgoing_values.append(target_text)

                    # Store activity details
                    activities.append({
                        "id": shape.ID,
                        "text": text,
                        "master": master_name,
                        "incoming_declenchante": incoming_declenchante,
                        "incoming_nourrissante": incoming_nourrissante,
                        "outgoing_values": outgoing_values
                    })

            # Display results for activities
            for activity in activities:
                print(f"Activity: {activity['text']} (ID={activity['id']}, Master={activity['master']})")
                print(f" - Données déclenchantes entrantes : {', '.join(activity['incoming_declenchante']) if activity['incoming_declenchante'] else 'None'}")
                print(f" - Données nourrissantes entrantes : {', '.join(activity['incoming_nourrissante']) if activity['incoming_nourrissante'] else 'None'}")
                print(f" - Valeurs ajoutées sortantes : {', '.join(activity['outgoing_values']) if activity['outgoing_values'] else 'None'}\n")

            # Display results for data
            print("Données déclenchantes:")
            for data in declenchante_data:
                from_shapes = [conn.from_id for conn in data.connects if conn.from_id != data.ID]
                to_shapes = [conn.to_id for conn in data.connects if conn.to_id != data.ID]

                from_texts = [shape_by_id[fs].text.strip() for fs in from_shapes if fs in shape_by_id]
                to_texts = [shape_by_id[ts].text.strip() for ts in to_shapes if ts in shape_by_id]

                if from_texts or to_texts:
                    print(f"Donnée déclenchante : {data.text.strip()}")
                    print(f"  Depuis : {', '.join(from_texts)}")  # Correct origin
                    print(f"  Vers : {', '.join(to_texts)}")  # Correct destination

            print("\nDonnées nourrissantes:")
            for data in nourrissante_data:
                from_shapes = [conn.from_id for conn in data.connects if conn.from_id != data.ID]
                to_shapes = [conn.to_id for conn in data.connects if conn.to_id != data.ID]

                from_texts = [shape_by_id[fs].text.strip() for fs in from_shapes if fs in shape_by_id]
                to_texts = [shape_by_id[ts].text.strip() for ts in to_shapes if ts in shape_by_id]

                if from_texts or to_texts:
                    print(f"Donnée nourrissante : {data.text.strip()}")
                    print(f"  Depuis : {', '.join(from_texts)}")  # Correct origin
                    print(f"  Vers : {', '.join(to_texts)}")  # Correct destination

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
