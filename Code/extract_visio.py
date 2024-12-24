import os
import json
from vsdx import VisioFile

# Chemin du fichier Visio
visio_file_path = r"C:\Users\Hubert.AFDEC\A.F.D.E.C\Projet OPTIQ - DevOPTIQ\Archives\test.vsdx"

def extract_visio_data(file_path):
    try:
        # Ouvrir le fichier Visio
        visio = VisioFile(file_path)
        activities = []
        data_connections = []

        print(f"Ouverture du fichier : {file_path}")

        for page in visio.pages:
            print(f"Analyse de la page : {page.name}")

            for shape in page.child_shapes:  # Remplacer 'shapes' par 'child_shapes'
                # Vérifier si des propriétés pertinentes sont disponibles
                text = shape.text.strip() if shape.text else "Pas de texte"
                layer_member = shape.cell_value("LayerMember") if "LayerMember" in shape.cells else "Aucun calque"
                width = getattr(shape, "width", None)
                height = getattr(shape, "height", None)
                fill_color = getattr(shape, "fill_color", None)
                line_color = getattr(shape, "line_color", None)

                # Afficher les propriétés analysées
                print(
                    f"Forme analysée : texte='{text}', calque='{layer_member}', "
                    f"largeur={width}, hauteur={height}, couleur_remplissage={fill_color}, "
                    f"couleur_ligne={line_color}"
                )

                # Identifier les activités selon des critères (ex. : dimensions et calque)
                if layer_member == "Activity" and isinstance(width, (float, int)) and width > 1.0:
                    activities.append({
                        "name": text,
                        "width": width,
                        "height": height,
                        "fill_color": fill_color,
                        "line_color": line_color
                    })

                # Extraire les connexions
                if hasattr(shape, "connects"):
                    for connection in shape.connects:
                        source_text = connection.shape.text.strip() if connection.shape.text else "Pas de texte"
                        data_connections.append({
                            "source": source_text,
                            "target": text
                        })

        # Sauvegarder les activités extraites
        with open("activities.json", "w", encoding="utf-8") as f:
            json.dump(activities, f, indent=4, ensure_ascii=False)
        print("Activités sauvegardées dans 'activities.json'.")

        # Sauvegarder les connexions extraites
        with open("data_connections.json", "w", encoding="utf-8") as f:
            json.dump(data_connections, f, indent=4, ensure_ascii=False)
        print("Connexions sauvegardées dans 'data_connections.json'.")

    except Exception as e:
        print(f"Erreur lors de l'extraction : {e}")

# Exécution du script
extract_visio_data(visio_file_path)

