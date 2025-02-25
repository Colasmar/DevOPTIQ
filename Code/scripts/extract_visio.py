import os
import sys
from vsdx import VisioFile
from sqlalchemy.exc import IntegrityError

# Ajouter dynamiquement le chemin du projet pour accéder aux modules internes
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from Code.extensions import db
from Code.models.models import Activities, Data, Link  # Notez que nous n'utilisons plus la table Connections

# Mapping pour convertir les valeurs de calque en libellé normalisé
LAYER_MAPPING = {
    "1": "Activity",
    "9": "N link",    # Nourrissante (ligne pointillée)
    "10": "T link",   # Déclenchante (ligne pleine)
    "6": "Result",    # Résultat (drapeau) -> ces activités ne seront pas affichées
    "8": "Return"     # Retour (rond)
}

# Calques à ignorer
IGNORE_LAYERS = ["légende", "Color"]

# Global mappings
activity_mapping = {}   # key: shape_id, value: DB id de l'activité
return_mapping = {}     # key: shape_id, value: nom du retour
data_mapping = {}       # key: shape_id, value: DB id du connecteur (Data)

# Liste pour résumer les liens créés
link_summaries = []
rename_summaries = []

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
    Retourne la valeur en chaîne, ou None.
    """
    cell = shape.xml.find(".//{*}Cell[@N='FillPattern']")
    if cell is not None:
        return cell.get("V")
    return None

def standardize_id(visio_id):
    """Convertit l'ID de la forme en chaîne normalisée."""
    try:
        return str(int(visio_id)).strip().lower()
    except (ValueError, TypeError):
        return str(visio_id).strip().lower()

def process_visio_file(vsdx_path):
    """
    Ouvre et traite un fichier Visio pour extraire/mettre à jour les données.
    - Ajoute ou met à jour les activités (avec leur shape_id)
    - Gère les retours et les connecteurs
    - Met à jour la table Data pour les connecteurs, et crée des entrées dans Link
    - Supprime les activités et Data dont le shape_id n'est plus présent
    """
    if not os.path.exists(vsdx_path):
        print(f"ERREUR : Le fichier Visio '{vsdx_path}' est introuvable.")
        return

    with VisioFile(vsdx_path) as visio:
        print(f"INFO : Début de l'importation de la cartographie depuis {vsdx_path}")
        global activity_mapping, return_mapping, data_mapping, link_summaries, rename_summaries
        activity_mapping.clear()
        return_mapping.clear()
        data_mapping.clear()
        link_summaries.clear()
        rename_summaries.clear()

        for page in visio.pages:
            print(f"INFO : Analyse de la page : {page.name}")
            for shape in page.all_shapes:
                process_shape(shape)

        # Suppression des activités en base dont le shape_id n'est plus présent
        existing_activities = Activities.query.filter(Activities.shape_id.isnot(None)).all()
        deleted_activities_count = 0
        for act in existing_activities:
            if act.shape_id not in activity_mapping:
                print(f"INFO : Suppression de l'activité {act.name} (DB ID: {act.id}) car absente")
                db.session.delete(act)
                deleted_activities_count += 1
        db.session.commit()

        # Suppression des Data (connecteurs/retours) dont le shape_id n'est plus présent
        existing_data = Data.query.filter(Data.shape_id.isnot(None)).all()
        deleted_data_count = 0
        for d in existing_data:
            if d.shape_id not in data_mapping and d.shape_id not in return_mapping:
                print(f"INFO : Suppression de la donnée '{d.name}' (type: {d.type}, DB ID: {d.id}) car absente")
                db.session.delete(d)
                deleted_data_count += 1
        db.session.commit()

        print(f"INFO : Importation terminée.")
        print(f"INFO : Activités ajoutées/mises à jour: {len(activity_mapping)}, activités supprimées: {deleted_activities_count}")
        print(f"INFO : Données supprimées: {deleted_data_count}")
        print_summary()

def add_or_update_activity(shape, is_result=False):
    """
    Ajoute ou met à jour une activité en se basant sur son shape_id.
    Seules les formes dont fill_pattern == "1" sont considérées comme 'non-result'; sinon is_result=True.
    """
    key = standardize_id(shape.ID)
    name = shape.text.strip() if shape.text else ("Résultat sans nom" if is_result else "Activité sans nom")
    fill_pattern = get_fill_pattern(shape)
    if fill_pattern is not None and fill_pattern != "1":
        is_result = True

    act = Activities.query.filter_by(shape_id=key).first()
    if act:
        updated = False
        if act.name != name:
            old_name = act.name
            act.name = name
            updated = True
            rename_summaries.append((old_name, name))
        if act.is_result != is_result:
            act.is_result = is_result
            updated = True
        if updated:
            print(f"INFO : Activité (DB ID: {act.id}) mise à jour : {name} (is_result={is_result})")
        else:
            print(f"INFO : Activité (DB ID: {act.id}) déjà existante, aucune modification.")
    else:
        try:
            act = Activities(name=name, is_result=is_result, shape_id=key)
            db.session.add(act)
            db.session.flush()
            print(f"INFO : Nouvelle activité ajoutée : {name} (Visio ID: {key}, DB ID: {act.id}, is_result={is_result})")
        except IntegrityError as e:
            db.session.rollback()
            print(f"ERREUR : Problème lors de l'ajout de l'activité {name}: {str(e)}")
            return
    activity_mapping[key] = act.id

def add_return(shape):
    """
    Traite une forme de type "Return".
    On utilise le shape_id pour éviter les doublons et on met à jour Data.
    """
    key = standardize_id(shape.ID)
    name = shape.text.strip() if shape.text else "Return sans nom"

    existing = Data.query.filter_by(shape_id=key, type="Retour").first()
    if existing:
        old_name = existing.name
        if old_name != name:
            existing.name = name
            db.session.commit()
            print(f"INFO : Return mis à jour : {old_name} => {name} (shape_id={key})")
            rename_summaries.append((old_name, name))
        else:
            print(f"INFO : Return existant, aucune modification : {name} (shape_id={key})")
        return_mapping[key] = name
        data_mapping[key] = existing.id
    else:
        old_by_name = Data.query.filter_by(name=name, type="Retour").first()
        if old_by_name:
            old_by_name.shape_id = key
            db.session.commit()
            print(f"INFO : Return existant par nom, shape_id mis à jour : {name} (shape_id={key})")
            return_mapping[key] = name
            data_mapping[key] = old_by_name.id
        else:
            try:
                d = Data(name=name, type="Retour", shape_id=key)
                db.session.add(d)
                db.session.flush()
                print(f"INFO : Return ajouté : {name} (shape_id={key}, DB ID={d.id})")
                return_mapping[key] = name
                data_mapping[key] = d.id
            except IntegrityError:
                db.session.rollback()
                print(f"ERREUR : Problème avec le Return : {name}")

def add_data_and_connections(shape):
    """
    Traite une forme connecteur ("T link" ou "N link").
    - Cherche ou crée un enregistrement Data basé sur (shape_id, type)
    - Supprime toutes les liaisons (Links) existantes pour ce Data
    - Crée de nouvelles liaisons selon les points de raccord
    """
    key = standardize_id(shape.ID)
    data_name = shape.text.strip() if shape.text else "Donnée sans nom"
    layer = get_layer(shape)
    data_type = "déclenchante" if layer == "T link" else "nourrissante"

    existing = Data.query.filter_by(shape_id=key, type=data_type).first()
    if existing:
        old_name = existing.name
        if old_name != data_name:
            existing.name = data_name
            db.session.commit()
            print(f"INFO : Donnée connecteur renommée : '{old_name}' => '{data_name}' (shape_id={key})")
            rename_summaries.append((old_name, data_name))
        data_record = existing
    else:
        data_record = Data(name=data_name, type=data_type, layer=layer, shape_id=key)
        db.session.add(data_record)
        db.session.flush()
        print(f"INFO : Donnée connecteur ajoutée : '{data_name}' (shape_id={key}, ID={data_record.id})")
    data_mapping[key] = data_record.id

    # Supprimer les anciens liens associés à ce Data
    old_links = Link.query.filter(
        (Link.source_data_id == data_record.id) | (Link.target_data_id == data_record.id)
    ).all()
    for lnk in old_links:
        print(f"INFO : Suppression de l'ancien lien (ID={lnk.id}, desc='{lnk.description}') pour donnée '{data_record.name}'")
        db.session.delete(lnk)
    db.session.commit()

    conns = analyze_connections(shape)

    def resolve_id(visio_id):
        if not visio_id:
            return (None, None)
        key_visio = standardize_id(visio_id)
        if key_visio in activity_mapping:
            return ('activity', activity_mapping[key_visio])
        if key_visio in data_mapping:
            return ('data', data_mapping[key_visio])
        if key_visio in return_mapping:
            ret_name = return_mapping[key_visio]
            act = Activities.query.filter(Activities.name.ilike(ret_name)).first()
            if act:
                return ('activity', act.id)
        return (None, None)

    (src_type, src_id) = resolve_id(conns.get("from_id"))
    (trg_type, trg_id) = resolve_id(conns.get("to_id"))

    # Récupérer les noms pour le log
    s_name = get_entity_name(src_id) if src_id else "inconnue"
    t_name = get_entity_name(trg_id) if trg_id else "inconnue"

    if s_name.strip().lower() == t_name.strip().lower():
        print(f"WARNING : Source et cible identiques ('{s_name}') pour donnée '{data_record.name}'. Liaison ignorée.")
        db.session.commit()
        return

    # Créer le lien via le nouveau modèle Link
    if src_id and trg_id:
        new_link = Link(
            type=data_type,
            description=data_record.name
        )
        if src_type == 'activity':
            new_link.source_activity_id = src_id
        else:
            new_link.source_data_id = src_id

        if trg_type == 'activity':
            new_link.target_activity_id = trg_id
        else:
            new_link.target_data_id = trg_id

        db.session.add(new_link)
        db.session.flush()
        link_summaries.append((data_record.name, data_record.type, s_name, t_name))
        print(f"INFO : Lien ajouté entre {s_name} et {t_name} pour donnée '{data_record.name}'")
    else:
        # Gérer les cas partiels si nécessaire
        if src_id:
            new_link = Link(
                type="output",
                description=f"Output partiel pour {data_record.name}"
            )
            if src_type == 'activity':
                new_link.source_activity_id = src_id
            else:
                new_link.source_data_id = src_id
            new_link.target_data_id = data_record.id
            db.session.add(new_link)
            db.session.flush()
            print(f"INFO : Lien output ajouté pour donnée '{data_record.name}'")
        if trg_id:
            new_link = Link(
                type="input",
                description=f"Input partiel pour {data_record.name}"
            )
            new_link.source_data_id = data_record.id
            if trg_type == 'activity':
                new_link.target_activity_id = trg_id
            else:
                new_link.target_data_id = trg_id
            db.session.add(new_link)
            db.session.flush()
            print(f"INFO : Lien input ajouté pour donnée '{data_record.name}'")
    db.session.commit()

def analyze_connections(shape):
    """
    Analyse le XML d'une forme pour extraire les IDs de connexion.
    Recherche les cellules dont N vaut "BeginX" et "EndX" et retourne un dictionnaire.
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
    Affiche un résumé clair des liens enregistrés et une confirmation finale.
    """
    print("\n--- Résumé des liens ---")
    if link_summaries:
        for data_name, data_type, src, tgt in link_summaries:
            print(f'Donnée "{data_name}" ({data_type}) produite par "{src}" est utilisée par "{tgt}"')
    else:
        print("Aucun lien enregistré.")
    print("--- Fin du résumé ---\n")
    if rename_summaries:
        print("\n--- Renommages détectés ---")
        for old_name, new_name in rename_summaries:
            print(f"Renommé : '{old_name}' => '{new_name}'")
        print("--- Fin des renommages ---\n")
    print("CONFIRMATION : Toutes les opérations (ajout, mise à jour, suppression) ont été effectuées avec succès.")

def process_shape(shape):
    """
    Oriente le traitement d'une forme selon son calque.
    Traite uniquement les formes appartenant aux calques "Activity", "Result", "Return" et aux connecteurs ("T link", "N link").
    """
    layer = get_layer(shape)
    if layer is None:
        print("INFO : Forme sans calque détectée, ignorée.")
        return
    if layer.lower() in [l.lower() for l in IGNORE_LAYERS]:
        return

    if layer == "Activity":
        add_or_update_activity(shape, is_result=False)
    elif layer == "Result":
        add_or_update_activity(shape, is_result=True)
    elif layer == "Return":
        add_return(shape)
    elif layer in ["T link", "N link"]:
        add_data_and_connections(shape)
    else:
        print(f"INFO : Calque non traité ({layer}) pour la forme '{shape.text.strip() if shape.text else 'sans texte'}'.")

if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)
    instance_path = os.path.abspath(os.path.join("Code", "instance"))
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    db_path = os.path.join(instance_path, "optiq.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    with app.app_context():
        print("INFO : Démarrage de l'importation de la cartographie avec mise à jour partielle")
        vsdx_path = os.path.join("Code", "example.vsdx")
        process_visio_file(vsdx_path)
