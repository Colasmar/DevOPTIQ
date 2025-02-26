import os
import sys
from vsdx import VisioFile
from sqlalchemy.exc import IntegrityError

# Pour pouvoir importer Code.extensions et Code.models.models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from Code.extensions import db
from Code.models.models import Activities, Data, Link

# Calques Visio qu’on gère
LAYER_MAPPING = {
    "1": "Activity",     # rectangle "normal"
    "9": "N link",       # ligne pointillée => nourrissante
    "10": "T link",      # ligne pleine => déclenchante
    "6": "Result",       # drapeau => activité de résultat
    "8": "Return"        # rond => retour
}

# Calques à ignorer
IGNORE_LAYERS = ["légende", "Color"]

# Dictionnaires globaux pour stocker le mapping shape_id => id en base
activity_mapping = {}
data_mapping = {}
return_mapping = {}  # pour retours (stockés aussi dans data, type='Retour')

# Listes de résumé
link_summaries = []     # pour afficher "data_name (type) : src -> tgt"
rename_summaries = []   # pour "ancien_nom => nouveau_nom"

def create_app():
    """Pour exécuter ce script directement (en standalone)."""
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
    Retourne le calque normalisé (Activity, N link, T link, Result, Return)
    ou None si inconnu.
    """
    cell = shape.xml.find(".//{*}Cell[@N='LayerMember']")
    if cell is not None:
        val = cell.get("V")
        return LAYER_MAPPING.get(val, val)
    return None

def get_fill_pattern(shape):
    """Retourne la valeur de FillPattern (str) ou None."""
    cell = shape.xml.find(".//{*}Cell[@N='FillPattern']")
    if cell is not None:
        return cell.get("V")
    return None

def standardize_id(visio_id):
    """Convertit l’ID en string normalisée."""
    try:
        return str(int(visio_id)).strip().lower()
    except:
        return str(visio_id).strip().lower()

def process_visio_file(vsdx_path):
    """
    Import "partiel" en recréant les liens dans Link.
    1) On parcourt toutes les formes
    2) On met à jour Activities, Data (type='Retour' ou connecteur)
    3) On supprime en base les Activities/Data qui n’existent plus
    """
    if not os.path.exists(vsdx_path):
        print(f"ERREUR : Fichier Visio introuvable : {vsdx_path}")
        return

    print(f"INFO : Démarrage de l’import depuis {vsdx_path}")
    global activity_mapping, data_mapping, return_mapping
    global link_summaries, rename_summaries
    activity_mapping.clear()
    data_mapping.clear()
    return_mapping.clear()
    link_summaries.clear()
    rename_summaries.clear()

    with VisioFile(vsdx_path) as visio:
        for page in visio.pages:
            print(f"INFO : Analyse de la page : {page.name}")
            for shape in page.all_shapes:
                process_shape(shape)

    # Suppression des activités plus présentes
    existing_acts = Activities.query.filter(Activities.shape_id.isnot(None)).all()
    del_act_count = 0
    for act in existing_acts:
        if act.shape_id not in activity_mapping:
            print(f"INFO : Suppression activité '{act.name}' (ID={act.id}, shape_id={act.shape_id})")
            db.session.delete(act)
            del_act_count += 1
    db.session.commit()

    # Suppression des data plus présents
    existing_data = Data.query.filter(Data.shape_id.isnot(None)).all()
    del_data_count = 0
    for d in existing_data:
        shape_id = d.shape_id
        if shape_id not in data_mapping and shape_id not in return_mapping:
            print(f"INFO : Suppression data '{d.name}' (ID={d.id}, type={d.type}, shape_id={shape_id})")
            # Supprimer liens associés
            old_links = Link.query.filter(
                (Link.source_data_id == d.id) | (Link.target_data_id == d.id)
            ).all()
            for lk in old_links:
                print(f"    -> Suppression link (ID={lk.id}, desc='{lk.description}')")
                db.session.delete(lk)
            db.session.delete(d)
            del_data_count += 1
    db.session.commit()

    print("INFO : Import terminé.")
    print(f"      Activités ajoutées/mises à jour : {len(activity_mapping)} ; supprimées : {del_act_count}")
    print(f"      Data (connecteurs/retours) totaux : {len(data_mapping)+len(return_mapping)} ; supprimés : {del_data_count}")
    print_summary()

def process_shape(shape):
    """Dirige selon le calque."""
    layer = get_layer(shape)
    if layer is None:
        return
    if layer.lower() in [x.lower() for x in IGNORE_LAYERS]:
        return

    if layer == "Activity":
        add_or_update_activity(shape, is_result=False)
    elif layer == "Result":
        add_or_update_activity(shape, is_result=True)
    elif layer == "Return":
        add_or_update_return(shape)
    elif layer in ("T link", "N link"):
        add_or_update_connector(shape, layer)
    else:
        print(f"INFO : Calque {layer} non traité. Forme '{shape.text or 'sans texte'}' ignorée.")

def add_or_update_activity(shape, is_result=False):
    """Crée/MAJ Activities en se basant sur shape_id."""
    key = standardize_id(shape.ID)
    txt = shape.text.strip() if shape.text else ("Résultat sans nom" if is_result else "Activité sans nom")

    fill = get_fill_pattern(shape)
    if fill and fill != "1":
        is_result = True

    act = Activities.query.filter_by(shape_id=key).first()
    if act:
        changed = False
        old_name = act.name
        if act.name != txt:
            act.name = txt
            rename_summaries.append((old_name, txt))
            changed = True
        if act.is_result != is_result:
            act.is_result = is_result
            changed = True
        if changed:
            print(f"INFO : Activité (ID={act.id}) mise à jour => name='{txt}', is_result={is_result}")
        else:
            print(f"INFO : Activité (ID={act.id}) déjà existante, pas de modif.")
    else:
        new_a = Activities(name=txt, is_result=is_result, shape_id=key)
        db.session.add(new_a)
        db.session.flush()
        print(f"INFO : Activité créée => '{txt}' (ID={new_a.id}, shape_id={key}, is_result={is_result})")
        act = new_a

    activity_mapping[key] = act.id
    db.session.commit()

def add_or_update_return(shape):
    """Traite un 'Return' => on stocke dans Data(type='Retour')."""
    key = standardize_id(shape.ID)
    txt = shape.text.strip() if shape.text else "Retour sans nom"

    existing = Data.query.filter_by(shape_id=key, type="Retour").first()
    if existing:
        old = existing.name
        if old != txt:
            existing.name = txt
            rename_summaries.append((old, txt))
            db.session.commit()
            print(f"INFO : Return (ID={existing.id}) renommé '{old}' => '{txt}'")
        else:
            print(f"INFO : Return (ID={existing.id}) pas de modif.")
        return_mapping[key] = existing.id
        return

    # Sinon cherche par nom
    same_name = Data.query.filter_by(name=txt, type="Retour").first()
    if same_name:
        same_name.shape_id = key
        db.session.commit()
        print(f"INFO : Return existant par nom => shape_id={key} (ID={same_name.id})")
        return_mapping[key] = same_name.id
        return

    # Création
    d = Data(name=txt, type="Retour", shape_id=key)
    db.session.add(d)
    db.session.flush()
    print(f"INFO : Return créé => '{txt}' (ID={d.id}, shape_id={key})")
    return_mapping[key] = d.id
    db.session.commit()

def add_or_update_connector(shape, layer):
    """
    Gère un connecteur T link ou N link => Data + Link
    1) Récupère/crée un Data (type='déclenchante' ou 'nourrissante')
    2) Supprime les anciens Link liés à ce Data
    3) Analyse from_id/to_id => crée un unique lien (ou rien si incomplètement connecté)
    """
    key = standardize_id(shape.ID)
    txt = shape.text.strip() if shape.text else "Donnée sans nom"
    data_type = "déclenchante" if layer == "T link" else "nourrissante"

    d = Data.query.filter_by(shape_id=key, type=data_type).first()
    if d:
        old = d.name
        if old != txt:
            d.name = txt
            rename_summaries.append((old, txt))
            db.session.commit()
            print(f"INFO : Connector (ID={d.id}) rename '{old}' => '{txt}'")
    else:
        # Cherche par name+type si shape_id pas défini
        same = Data.query.filter_by(name=txt, type=data_type).first()
        if same:
            same.shape_id = key
            db.session.commit()
            print(f"INFO : Connector existant par nom => shape_id={key} (ID={same.id}, nom='{txt}')")
            d = same
        else:
            new_d = Data(name=txt, type=data_type, shape_id=key, layer=layer)
            db.session.add(new_d)
            db.session.flush()
            print(f"INFO : Connector créé => '{txt}' (ID={new_d.id}, shape_id={key})")
            d = new_d

    data_mapping[key] = d.id

    # Supprimer tous les liens existants pour ce Data (pour éviter doublons)
    old_links = Link.query.filter(
        (Link.source_data_id == d.id) | (Link.target_data_id == d.id)
    ).all()
    for lk in old_links:
        print(f"INFO : Suppression ancien link (ID={lk.id}, desc='{lk.description}') pour data='{d.name}'")
        db.session.delete(lk)
    db.session.commit()

    # Récupérer from_id / to_id
    conns = analyze_connections(shape)
    (src_kind, src_id) = resolve_visio_id(conns.get("from_id"))
    (tgt_kind, tgt_id) = resolve_visio_id(conns.get("to_id"))

    # Si on a deux extrémités (source & target) => un seul lien
    if src_id and tgt_id:
        if src_id == tgt_id:
            print(f"WARNING : src_id == tgt_id => on ignore ce lien data='{d.name}'")
            return
        create_single_link(d, data_type, src_kind, src_id, tgt_kind, tgt_id)
    else:
        # Sinon, on ignore. (Si vous voulez gérer un "partiel", décommentez.)
        print(f"INFO : Connecteur partiel ignoré => data='{d.name}'")

def create_single_link(data_obj, data_type, skind, sid, tkind, tid):
    """
    Crée un unique link (source=..., target=...) si on n’a pas déjà un lien identique.
    Gère le cas retours => si en final on obtient la même paire d’activités, on ne crée qu’un seul lien.
    """
    # Récupère le "nom" de la source et de la cible, pour logs
    s_name = get_entity_name(sid, skind)
    t_name = get_entity_name(tid, tkind)

    # Cas où source & cible sont tous deux des "activities"
    # => c’est le lien normal. On le crée en un exemplaire unique.
    new_link = Link(type=data_type, description=data_obj.name)

    if skind == 'activity':
        new_link.source_activity_id = sid
    else:
        new_link.source_data_id = sid

    if tkind == 'activity':
        new_link.target_activity_id = tid
    else:
        new_link.target_data_id = tid

    # Vérif qu’on n’a pas déjà le même link (source, target, type, desc)
    if link_exists_already(new_link):
        print(f"INFO : Lien déjà existant => {s_name} -> {t_name} (data='{data_obj.name}') => on ignore")
        return

    db.session.add(new_link)
    db.session.flush()
    link_summaries.append((data_obj.name, data_type, s_name, t_name))
    print(f"INFO : Lien créé => {s_name} -> {t_name} (data='{data_obj.name}')")

    db.session.commit()

def link_exists_already(link_obj):
    """
    Vérifie si on a déjà un Link équivalent (même type, même description, même source & target).
    """
    q = Link.query.filter_by(type=link_obj.type, description=link_obj.description)

    if link_obj.source_activity_id:
        q = q.filter_by(source_activity_id=link_obj.source_activity_id)
    else:
        q = q.filter_by(source_data_id=link_obj.source_data_id)

    if link_obj.target_activity_id:
        q = q.filter_by(target_activity_id=link_obj.target_activity_id)
    else:
        q = q.filter_by(target_data_id=link_obj.target_data_id)

    return q.first() is not None

def analyze_connections(shape):
    """
    Récupère from_id & to_id.
    """
    conns = {"from_id": None, "to_id": None}
    for cell in shape.xml.findall(".//{*}Cell"):
        n = cell.get("N")
        f = cell.get("F")
        if n == "BeginX":
            conns["from_id"] = extract_shape_id(f)
        elif n == "EndX":
            conns["to_id"] = extract_shape_id(f)
    return conns

def extract_shape_id(f_val):
    if f_val and "Sheet." in f_val:
        try:
            return int(f_val.split("Sheet.")[1].split("!")[0])
        except:
            return None
    return None

def resolve_visio_id(raw_id):
    """
    Retourne (kind, id):
      kind='activity' => ID dans Activities
      kind='data' => ID dans Data
    ou (None, None) si inconnu
    Gère le cas d’un shape "Return" => on mappe sur l’activité de même nom si possible.
    """
    if not raw_id:
        return (None, None)
    key = standardize_id(raw_id)

    # 1) Activity ?
    if key in activity_mapping:
        return ('activity', activity_mapping[key])

    # 2) Data "normal" ?
    if key in data_mapping:
        return ('data', data_mapping[key])

    # 3) Data "Retour" ?
    if key in return_mapping:
        d_id = return_mapping[key]
        d = Data.query.get(d_id)
        if d and d.type.lower() == "retour":
            # On cherche l’activité portant le même nom
            same_act = Activities.query.filter_by(name=d.name).first()
            if same_act:
                return ('activity', same_act.id)
        return ('data', d_id)

    return (None, None)

def get_entity_name(eid, kind):
    """Renvoie le nom de l’entité pour logs."""
    if not eid:
        return "??"
    if kind == 'activity':
        a = Activities.query.get(eid)
        return a.name if a else "activité_inconnue"
    elif kind == 'data':
        dd = Data.query.get(eid)
        return dd.name if dd else "data_inconnue"
    return "inconnu"

def print_summary():
    print("\n--- RÉSUMÉ DES LIENS ---")
    if link_summaries:
        for (data_name, data_type, s_name, t_name) in link_summaries:
            print(f"  - '{data_name}' ({data_type}) : {s_name} -> {t_name}")
    else:
        print("  Aucun lien créé")
    print("--- Fin du résumé ---\n")

    if rename_summaries:
        print("--- Renommages détectés ---")
        for (old, new) in rename_summaries:
            print(f"  * '{old}' => '{new}'")
        print("--- Fin des renommages ---\n")

    print("CONFIRMATION : toutes les opérations ont été effectuées avec succès.")


if __name__ == "__main__":
    from flask import Flask
    app = create_app()
    with app.app_context():
        vsdx_path = os.path.join("Code", "example.vsdx")
        process_visio_file(vsdx_path)
