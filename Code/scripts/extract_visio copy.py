import os
import sys
from vsdx import VisioFile
from sqlalchemy.exc import IntegrityError

# Ajouter dynamiquement le chemin du projet pour accéder aux modules internes
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from Code.extensions import db
from Code.models.models import Activities, Data, Connections

# Mapping pour convertir les valeurs de calque en libellé normalisé
LAYER_MAPPING = {
    "1": "Activity",
    "9": "N link",    # Nourrissante (ligne pointillée)
    "10": "T link",   # Déclenchante (ligne pleine)
    "6": "Result",    # Résultat (drapeau) -> sera traité comme activité
    "8": "Return"     # Retour (rond)
}

# Calques à ignorer
IGNORE_LAYERS = ["légende", "Color"]

# Global mapping pour les activités (clé : ID Visio standardisé, valeur : ID en base)
activity_mapping = {}
# Global mapping pour les retours (clé : ID Visio standardisé, valeur : texte de la forme)
return_mapping = {}
# Liste pour résumer les connexions créées (pour le rapport final)
connection_summaries = []

def get_entity_name(entity_id):
    """
    Renvoie le nom de l'entité dans Activities (prioritaire), sinon "inconnue".
    """
    act = Activities.query.get(entity_id)
    if act:
        return act.name.strip()
    return "inconnue"

def create_app():
    """Crée une application Flask minimale avec contexte DB."""
    from flask import Flask
    app = Flask(__name__)
    instance_path = os.path.abspath(os.path.join("Code", "instance"))
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    db_path = os.path.join(instance_path, "optiq.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app

def reset_database():
    """Réinitialise la base en vidant toutes les tables et en réinitialisant les mappings."""
    db.session.query(Connections).delete()
    db.session.query(Data).delete()
    db.session.query(Activities).delete()
    db.session.commit()
    activity_mapping.clear()
    return_mapping.clear()
    connection_summaries.clear()
    print("INFO : La base de données a été réinitialisée avec succès.")

def get_layer(shape):
    """
    Extrait la valeur du calque d'une forme à partir de son XML.
    Retourne le libellé normalisé.
    """
    cell = shape.xml.find(".//{*}Cell[@N='LayerMember']")
    if cell is not None:
        value = cell.get("V")
        return LAYER_MAPPING.get(value, value)
    return None

def get_fill_pattern(shape):
    """
    Extrait la valeur du FillPattern depuis la ShapeSheet.
    Cherche la cellule dont N vaut "FillPattern" et retourne sa valeur (en chaîne),
    ou None si non trouvée.
    """
    cell = shape.xml.find(".//{*}Cell[@N='FillPattern']")
    if cell is not None:
        return cell.get("V")
    return None

def process_visio_file(vsdx_path):
    """Ouvre et traite un fichier Visio pour extraire les données."""
    if not os.path.exists(vsdx_path):
        print(f"ERREUR : Le fichier Visio '{vsdx_path}' est introuvable.")
        return
    with VisioFile(vsdx_path) as visio:
        for page in visio.pages:
            print(f"INFO : Analyse de la page : {page.name}")
            for shape in page.all_shapes:
                process_shape(shape)

def process_shape(shape):
    """Oriente le traitement d'une forme selon son calque."""
    layer = get_layer(shape)
    if layer is None:
        print("INFO : Forme sans calque détectée, ignorée.")
        return
    if layer.lower() in [l.lower() for l in IGNORE_LAYERS]:
        return

    if layer == "Activity":
        add_activity(shape, is_result=False)
    elif layer == "Result":
        add_activity(shape, is_result=True)
    elif layer == "Return":
        add_return(shape)
    elif layer in ["T link", "N link"]:
        add_data_and_connections(shape)
    else:
        print(f"INFO : Calque non traité ({layer}) pour la forme '{shape.text.strip() if shape.text else 'sans texte'}'.")

def standardize_id(visio_id):
    """Convertit l'ID de la forme en chaîne normalisée."""
    try:
        return str(int(visio_id)).strip().lower()
    except (ValueError, TypeError):
        return str(visio_id).strip().lower()

def add_activity(shape, is_result=False):
    """
    Ajoute une activité dans Activities.
    Pour les formes du calque "Activity", si FillPattern vaut "2", force is_result=True.
    """
    name = shape.text.strip() if shape.text else ("Résultat sans nom" if is_result else "Activité sans nom")
    if not is_result:
        fill_pattern = get_fill_pattern(shape)
        if fill_pattern == "2":
            is_result = True
    try:
        act = Activities(name=name, is_result=is_result)
        db.session.add(act)
        db.session.flush()  # Pour obtenir act.id
        key = standardize_id(shape.ID)
        activity_mapping[key] = act.id
        type_str = "Activité de résultat" if is_result else "Activité"
        print(f"INFO : {type_str} ajoutée : {name} (Visio ID: {shape.ID}, DB ID: {act.id})")
    except IntegrityError:
        db.session.rollback()
        print(f"INFO : {('Activité de résultat' if is_result else 'Activité')} existante : {name}")

def add_return(shape):
    """
    Traite une forme de type "Return".
    Enregistre la donnée dans Data avec le type "Retour" et met à jour le mapping des retours.
    """
    name = shape.text.strip() if shape.text else "Return sans nom"
    try:
        existing = Data.query.filter_by(name=name, type="Retour").first()
        if existing:
            print(f"INFO : Return réutilisé : {name}")
        else:
            d = Data(name=name, type="Retour")
            db.session.add(d)
            db.session.flush()
            print(f"INFO : Return ajouté : {name}")
        key = standardize_id(shape.ID)
        return_mapping[key] = name
    except IntegrityError:
        db.session.rollback()
        print(f"INFO : Problème avec le Return : {name}")

def add_data_and_connections(shape):
    """
    Traite une forme connecteur ("T link" ou "N link").
    Crée ou réutilise une donnée dans Data et crée une connexion entre la source et la destination.
    """
    data_name = shape.text.strip() if shape.text else "Donnée sans nom"
    layer = get_layer(shape)
    data_type = "déclenchante" if layer == "T link" else "nourrissante"
    conns = analyze_connections(shape)
    try:
        existing = Data.query.filter_by(name=data_name, type=data_type, layer=layer).first()
        if existing:
            data_record = existing
            print(f"INFO : Donnée réutilisée : {data_name} ({data_type})")
        else:
            data_record = Data(name=data_name, type=data_type, layer=layer)
            db.session.add(data_record)
            db.session.flush()
            print(f"INFO : Donnée ajoutée : {data_name} ({data_type})")
        
        def resolve_id(visio_id):
            if not visio_id:
                return None
            key = standardize_id(visio_id)
            if key in activity_mapping:
                return activity_mapping[key]
            elif key in return_mapping:
                act = Activities.query.filter(Activities.name.ilike(return_mapping[key])).first()
                if act:
                    return act.id
            return None

        source_db_id = resolve_id(conns.get("from_id"))
        target_db_id = resolve_id(conns.get("to_id"))

        s_name = get_entity_name(source_db_id) if source_db_id else "inconnue"
        t_name = get_entity_name(target_db_id) if target_db_id else "inconnue"

        if s_name.strip().lower() == t_name.strip().lower():
            print(f"WARNING: Source et target identiques ('{s_name}') pour donnée '{data_record.name}'. Connexion ignorée.")
            db.session.commit()
            return

        if source_db_id and target_db_id:
            existing_conn = Connections.query.filter_by(
                source_id=source_db_id,
                target_id=target_db_id,
                type=data_type
            ).first()
            if not existing_conn:
                conn = Connections(
                    source_id=source_db_id,
                    target_id=target_db_id,
                    type=data_type,
                    description=data_record.name  # Ajout de la description pour la connexion complète
                )
                db.session.add(conn)
                db.session.flush()
                s_name = get_entity_name(source_db_id)
                t_name = get_entity_name(target_db_id)
                connection_summaries.append((data_record.name, data_record.type, s_name, t_name))
                print(f"INFO : Connexion ajoutée entre {s_name} et {t_name} pour donnée {data_name}")
        else:
            if conns.get("from_id"):
                sid = resolve_id(conns.get("from_id"))
                if sid:
                    existing_conn = Connections.query.filter_by(
                        source_id=sid,
                        target_id=data_record.id,
                        type="output"
                    ).first()
                    if not existing_conn:
                        conn = Connections(
                            source_id=sid,
                            target_id=data_record.id,
                            type="output"
                        )
                        db.session.add(conn)
                        db.session.flush()
                        s_name = get_entity_name(sid)
                        connection_summaries.append((data_record.name, data_record.type, s_name, "inconnue"))
                        print(f"INFO : Connexion output ajoutée entre {s_name} et donnée {data_name}")
            if conns.get("to_id"):
                tid = resolve_id(conns.get("to_id"))
                if tid:
                    existing_conn = Connections.query.filter_by(
                        source_id=data_record.id,
                        target_id=tid,
                        type="input"
                    ).first()
                    if not existing_conn:
                        conn = Connections(
                            source_id=data_record.id,
                            target_id=tid,
                            type="input"
                        )
                        db.session.add(conn)
                        db.session.flush()
                        t_name = get_entity_name(tid)
                        connection_summaries.append((data_record.name, data_record.type, "inconnue", t_name))
                        print(f"INFO : Connexion input ajoutée entre donnée {data_name} et {t_name}")
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        print(f"INFO : Problème d'insertion pour la donnée {data_name}")

def analyze_connections(shape):
    """
    Analyse le XML d'une forme pour extraire les IDs de connexion.
    Recherche les cellules dont N vaut "BeginX" et "EndX" et retourne {"from_id": ..., "to_id": ...}.
    """
    conns = {"from_id": None, "to_id": None}
    for cell in shape.xml.findall(".//{*}Cell"):
        n_val = cell.get("N")
        f_val = cell.get("F")
        if n_val == "BeginX":
            conns["from_id"] = extract_shape_id(f_val)
        elif n_val == "EndX":
            conns["to_id"] = extract_shape_id(f_val)
    return conns

def extract_shape_id(f_val):
    """
    Extrait l'ID d'une forme connectée à partir de la chaîne f_val.
    Cherche la sous-chaîne après "Sheet." et convertit en entier.
    """
    if f_val and "Sheet." in f_val:
        try:
            return int(f_val.split("Sheet.")[1].split("!")[0])
        except ValueError:
            return None
    return None

def print_summary():
    """
    Affiche un résumé clair des connexions enregistrées.
    Pour chaque connexion dans connection_summaries, affiche :
      "Donnée <nom> (<type>) produite par <source> est utilisée par <destination>"
    """
    print("\n--- Résumé des connexions ---")
    if connection_summaries:
        for data_name, data_type, src, tgt in connection_summaries:
            print(f'Donnée "{data_name}" ({data_type}) produite par "{src}" est utilisée par "{tgt}"')
    else:
        print("Aucune connexion enregistrée.")
    print("--- Fin du résumé ---\n")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        reset_database()
        vsdx_path = os.path.join("Code", "example.vsdx")
        process_visio_file(vsdx_path)
        print_summary()
