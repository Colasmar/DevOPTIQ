import os
import shutil
from vsdx import VisioFile

def categorize_layer(layer_value):
    """Retourne la catégorie d'une forme en fonction de son numéro de layer."""
    layer_categories = {
        "1": "Activité",
        "10": "Donnée déclenchante",
        "9": "Donnée nourrissante",
        "6": "Résultat",
        "8": "Retour",
    }
    return layer_categories.get(layer_value, "Exclu")

def test_layer_extraction_with_categories(vsdx_path):
    """Test pour extraire et catégoriser les formes en fonction de leur layer."""
    if not os.path.exists(vsdx_path):
        print(f"Erreur : Le fichier '{vsdx_path}' est introuvable.")
        return

    print(f"DEBUG: Ouverture du fichier Visio '{vsdx_path}'")
    try:
        with VisioFile(vsdx_path) as visio:
            for page in visio.pages:
                print(f"Analyse de la page : {page.name}")
                for shape in page.all_shapes:
                    layer = shape.xml.find(".//{*}Cell[@N='LayerMember']")
                    layer_value = layer.get("V") if layer is not None else "None"
                    text = shape.text.strip() if shape.text else "None"
                    
                    # Catégoriser les layers
                    category = categorize_layer(layer_value)
                    if category != "Exclu":
                        print(f"Shape ID={shape.ID}, Text='{text}', Layer='{layer_value}' ({category})")
                    else:
                        print(f"Shape ID={shape.ID}, Text='{text}', Layer='{layer_value}' (Exclu)")

    except PermissionError as e:
        print(f"PermissionError ignorée : {e}")
    finally:
        # Nettoyer explicitement les fichiers temporaires
        if visio.directory and os.path.exists(visio.directory):
            shutil.rmtree(visio.directory, ignore_errors=True)
        print("Fichiers temporaires nettoyés.")

# Tester le code
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
vsdx_file = os.path.join(project_root, 'Code', 'example.vsdx')

test_layer_extraction_with_categories(vsdx_file)
