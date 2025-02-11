import os
import sys
from flask import Flask
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
    "6": "Result",    # Résultat (drapeau) -> sera traité comme activité avec is_result=True
    "8": "Return"     # Retour (rond)
}

# Calques à ignorer
IGNORE_LAYERS = ["légende", "Color"]

# Global mappings
activity_mapping = {}    # Pour les formes insérées dans Activities (incluant les activités de résultat)
# Pour les formes Return, on stocke leur texte qui indique le nom de l'activité associée
return_mapping = {}      # Clé : ID Visio standardisé d'une forme Return, Valeur : le texte (nom) inscrit dans la forme
connection_summaries = []  # Liste des tuples (data_name, data_type, source_activity, target_activity)

def get_entity_name(entity_id):
    """
    Renvoie le nom de l'activité correspondant à l'ID dans Activities.
    """
    act = Activities.query.get(entity_id)
    if act:
        return act.name.strip()
    return "inconnue"

def create_app():
    """Crée une application Flask minimale avec contexte DB."""
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
    Cherche la cellule avec N="LayerMember".
    Retourne le libellé normalisé si possible.
    """
    cell = shape.xml.find(".//{*}Cell[@N='LayerMember']")
    if cell is not None:
        value = cell.get("V")
        return LAYER_MAPPING.get(value, value)
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
        # Traiter les formes Result comme des activités avec is_result True
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
    Le flag is_result permet de différencier une activité de résultat.
    """
    name = shape.text.strip() if shape.text else ("Résultat sans nom" if is_result else "Activité sans nom")
    try:
        act = Activities(name=name, is_result=is_result)
        db.session.add(act)
        db.session.flush()  # pour obtenir act.id
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
    Enregistre la forme dans Data (avec type "Retour") et ajoute dans return_mapping
    le mapping entre l'ID Visio et le nom inscrit dans la forme.
    """
    name = shape.text.strip() if shape.text else "Return sans nom"
    special_type = "Retour"
    try:
        existing = Data.query.filter_by(name=name, type=special_type).first()
        if existing:
            d = existing
            print(f"INFO : Return réutilisé : {name}")
        else:
            d = Data(name=name, type=special_type)
            db.session.add(d)
            db.session.flush()
            print(f"INFO : Return ajouté : {name}")
        key = standardize_id(shape.ID)
        # Enregistrer dans return_mapping : on stocke le nom du retour
        return_mapping[key] = name
    except IntegrityError:
        db.session.rollback()
        print(f"INFO : Problème avec le Return : {name}")

def add_data_and_connections(shape):
    """
    Traite une forme connecteur ("T link" ou "N link").
    Crée ou réutilise une donnée dans Data et crée une connexion fusionnée entre la source et la destination.
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
            # Priorité : si l'ID correspond à un Return, utiliser le nom du retour pour retrouver l'activité associée
            if key in return_mapping:
                act = Activities.query.filter_by(name=return_mapping[key]).first()
                if act:
                    return act.id
            # Sinon, rechercher dans activity_mapping
            return activity_mapping.get(key, None)

        source_db_id = resolve_id(conns.get("from_id"))
        target_db_id = resolve_id(conns.get("to_id"))

        # Récupération des noms pour le résumé
        s_name = get_entity_name(source_db_id) if source_db_id else "inconnue"
        t_name = get_entity_name(target_db_id) if target_db_id else "inconnue"

        # Ne pas créer de connexion si la source et la destination sont identiques
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
                    type=data_type
                )
                db.session.add(conn)
                db.session.flush()
                s_name = get_entity_name(source_db_id)
                t_name = get_entity_name(target_db_id)
                summary = (data_record.name, data_record.type, s_name, t_name)
                if summary not in connection_summaries:
                    connection_summaries.append(summary)
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
                        summary = (data_record.name, data_record.type, s_name, "inconnue")
                        if summary not in connection_summaries:
                            connection_summaries.append(summary)
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
                        summary = (data_record.name, data_record.type, "inconnue", t_name)
                        if summary not in connection_summaries:
                            connection_summaries.append(summary)
                        print(f"INFO : Connexion input ajoutée entre donnée {data_name} et {t_name}")
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        print(f"INFO : Problème d'insertion pour la donnée {data_name}")

def analyze_connections(shape):
    """
    Analyse le XML d'une forme pour extraire les IDs de connexion.
    Recherche les cellules dont l'attribut N vaut "BeginX" et "EndX".
    Retourne un dictionnaire {"from_id": ..., "to_id": ...}.
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
    Cherche la sous-chaîne après "Sheet." et la convertit en entier.
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
