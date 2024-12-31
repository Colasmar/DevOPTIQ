import os
import xml.etree.ElementTree as ET
from vsdx import VisioFile

def analyze_visio():
    """
    Parcourt le fichier Visio (example.vsdx) et essaie de repérer :
      - Les formes rectangulaires "Activités"
      - Les connecteurs (trait plein vs. pointillé)
      - Les relations entre formes
    """
    current_dir = os.path.dirname(__file__)
    vsdx_path = os.path.join(current_dir, 'example.vsdx')
    
    # On ouvre le fichier Visio
    with VisioFile(vsdx_path) as doc:
        # Parcours de chaque page
        for page_index, page in enumerate(doc.pages):
            print(f"--- Page {page_index+1}: {page.name} ---")

            # Récupération de toutes les formes
            shapes = page.shapes  # liste d'objets Shape
            
            # 1) Lister d’abord toutes les formes, en notant celles qui semblent être des connecteurs
            connectors = []
            rectangles = []
            other_shapes = []
            
            for shape in shapes:
                # Astuce : la propriété shape.master_name aide souvent à distinguer
                # ex: "Dynamic Connector" pour un connecteur
                #     "Rectangle" pour un rectangle
                # Mais ça dépend du diagramme.
                master_name = shape.master_name or ""
                
                # Optionnel : récupérer le XML pour voir s'il contient le paramètre "LinePattern"
                # shape_xml = shape._xml  # si besoin
                
                # On essaye de repérer un connecteur
                if "connector" in master_name.lower():
                    connectors.append(shape)
                # On essaye de repérer un rectangle (pour l'Activité)
                elif "rectangle" in master_name.lower():
                    rectangles.append(shape)
                else:
                    other_shapes.append(shape)
            
            print(f"Formes rectangulaires (possibles Activités) : {[s.text for s in rectangles]}")
            print(f"Formes connecteurs : {[s.text for s in connectors]}")
            print(f"Autres formes : {[s.text for s in other_shapes]}")
            
            # 2) Pour chaque rectangle, voyons s'il a au moins un connecteur "entrant"
            #    On peut regarder les connecteurs qui pointent vers lui.
            #    Dans vsdx, on peut accéder à shape.connects,
            #    mais notez qu'un connecteur a aussi shape.connects (with from_id, to_id).
            
            # Pour faciliter, construisons un dictionnaire des shapes par ID
            shape_by_id = {}
            for s in shapes:
                shape_by_id[s.ID] = s
            
            # Vérifier la direction de connexion
            # connecteur.connects est une liste d'objets Connect,
            #   chaque connect contient from_id, from_rel, from_sheet, to_id, to_rel, to_sheet, ...
            
            for c in connectors:
                # c est un connecteur
                c_master = c.master_name or ""
                
                # Inspecter le XML pour savoir si c'est trait plein ou pointillé
                # -> on cherche un Cell N="LinePattern" dont la valeur = "2" (par exemple) signifierait pointillé
                # Ce n'est pas standard pour tous. Il faut explorer le XML.
                # On se fait une petite fonction auxiliaire (voir plus bas)
                line_pattern = get_line_pattern(c)
                
                # On parcourt c.connects pour voir les shapes connectées
                for conn in c.connects:
                    from_id = conn.from_id
                    to_id = conn.to_id
                    
                    # On récupère la shape source & destination
                    from_shape = shape_by_id.get(from_id)
                    to_shape = shape_by_id.get(to_id)
                    
                    # On peut afficher pour debug
                    # ex: "Connector X (solid) : from [texte shape source] to [texte shape cible]"
                    pattern_str = "POINTILLÉ" if line_pattern == "2" else "PLEIN?"
                    print(f"Connector {c.ID} ({pattern_str}) : from {from_shape.text} to {to_shape.text}")
                    
                    # Logique possible :
                    #  - Si line_pattern == "2" => trait pointillé => "donnée nourrissante" (selon vos règles)
                    #  - Sinon => "donnée déclenchante"
                    #  - On détermine si la "donnée" est la shape source ou la shape cible,
                    #    selon le sens. Si c'est "arrive dans l'activité", c'est to_shape = activité.
                    #    Si c'est "part de l'activité", c'est from_shape = activité.
                    
                    # Exemple simplifié :
                    if to_shape in rectangles:
                        # => le connecteur aboutit sur une forme rectangle => c'est un flux entrant
                        if line_pattern == "2":
                            print(f"  => {from_shape.text} est une donnée nourrissante pour l'activité {to_shape.text}")
                        else:
                            print(f"  => {from_shape.text} est une donnée déclenchante pour l'activité {to_shape.text}")
                    
                    elif from_shape in rectangles:
                        # => le connecteur part de la forme rectangle => flux sortant
                        if line_pattern == "2":
                            print(f"  => {to_shape.text} est nourri par l'activité {from_shape.text}")
                        else:
                            print(f"  => {to_shape.text} est déclenché par l'activité {from_shape.text}")
            
            # 3) Pour chaque rectangle, vérifier s'il a au moins un connecteur entrant
            #    (Ex: on compte combien de connecteurs aboutissent sur ce rectangle)
            for rect in rectangles:
                inbound_connectors = 0
                for c in connectors:
                    for conn in c.connects:
                        if conn.to_id == rect.ID:
                            inbound_connectors += 1
                if inbound_connectors > 0:
                    print(f"ACTIVITÉ détectée : {rect.text} (car {inbound_connectors} connecteur(s) entrant(s))")
                else:
                    print(f"Shape rect. ignorée : {rect.text}, pas de connecteur entrant.")
            
            print()  # saut de ligne de fin de page

def get_line_pattern(shape):
    """
    Inspecte le XML interne d'un connecteur pour en déduire un éventuel 'LinePattern'.
    Retourne la valeur dans la Cell 'N="LinePattern"' (ex: '1', '2', etc.) ou None.
    """
    shape_xml = shape._xml  # c'est un ElementTree.Element
    # On cherche un sous-élément <Cell N="LinePattern" .../>
    # Exemple de code (à adapter si la structure diffère) :
    for cell in shape_xml.iter("Cell"):
        if cell.get("N") == "LinePattern":
            val = cell.get("V")  # la valeur de l'attribut "V" dans <Cell N="LinePattern" V="2" ...>
            return val
    return None

if __name__ == "__main__":
    analyze_visio()
