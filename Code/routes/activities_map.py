# Code/routes/activities_map.py
"""
Cartographie des activités avec gestion multi-entités.
+ Import des connexions depuis fichiers VSDX
+ WIZARD UNIFIÉ SVG + VSDX
"""
import os
import shutil
import datetime
import re
import xml.etree.ElementTree as ET
import tempfile

from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    send_file
)

from sqlalchemy import or_
from Code.extensions import db
from Code.models.models import Activities, Entity, Link, Data

# Import du parser de connexions VSDX
from Code.routes.vsdx_conection_parser import (
    parse_vsdx_connections,
    validate_connections_against_activities
)


# ============================================================
# Blueprint
# ============================================================
activities_map_bp = Blueprint(
    "activities_map_bp",
    __name__,
    url_prefix="/activities"
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
ENTITIES_DIR = os.path.join(STATIC_DIR, "entities")
OLD_SVG_PATH = os.path.join(STATIC_DIR, "img", "carto_activities.svg")


def get_entity_svg_path(entity_id):
    return os.path.join(ENTITIES_DIR, f"entity_{entity_id}", "carto.svg")


def get_entity_vsdx_path(entity_id):
    return os.path.join(ENTITIES_DIR, f"entity_{entity_id}", "connections.vsdx")


def ensure_entity_dir(entity_id):
    entity_dir = os.path.join(ENTITIES_DIR, f"entity_{entity_id}")
    os.makedirs(entity_dir, exist_ok=True)
    return entity_dir


def _normalize_link_type(raw):
    """
    Normalise le type de connexion pour la BDD.
    Retourne 'déclenchante' | 'nourrissante' ou None si non déterminable.
    """
    if raw is None:
        return None

    t = str(raw).strip().lower()
    if not t:
        return None

    mapping = {
        "t link": "déclenchante",
        "trigger": "déclenchante",
        "déclenchante": "déclenchante",
        "n link": "nourrissante",
        "nourrissante": "nourrissante",
    }
    return mapping.get(t, None)


# ============================================================
# PAGE CARTOGRAPHIE
# ============================================================
@activities_map_bp.route("/map")
def activities_map_page():
    from flask import session
    
    active_entity = Entity.get_active()
    active_entity_id = session.get('active_entity_id')
    
    svg_exists = False
    vsdx_exists = False
    current_svg = None
    current_vsdx = None
    
    if active_entity:
        svg_path = get_entity_svg_path(active_entity.id)
        svg_exists = os.path.exists(svg_path)
        if not svg_exists and os.path.exists(OLD_SVG_PATH):
            svg_exists = True
        
        vsdx_path = get_entity_vsdx_path(active_entity.id)
        vsdx_exists = os.path.exists(vsdx_path)
        
        # Noms des fichiers pour l'affichage
        if svg_exists:
            current_svg = active_entity.svg_filename or "carto.svg"
        if vsdx_exists:
            current_vsdx = active_entity.vsdx_filename if hasattr(active_entity, 'vsdx_filename') else "connections.vsdx"
    
    if active_entity:
        rows = Activities.query.filter_by(entity_id=active_entity.id).order_by(Activities.id).all()
    else:
        rows = []
    
    shape_activity_map = {
        str(act.shape_id): act.id
        for act in rows
        if act.shape_id is not None
    }
    
    all_entities = Entity.for_user().all()
    
    active_entity_dict = None
    if active_entity:
        active_entity_dict = {
            "id": active_entity.id,
            "name": active_entity.name,
            "description": active_entity.description or "",
            "svg_filename": active_entity.svg_filename,
            "is_active": True
        }
    
    all_entities_list = [
        {
            "id": e.id,
            "name": e.name,
            "description": e.description or "",
            "svg_filename": e.svg_filename,
            "is_active": (e.id == active_entity_id)
        }
        for e in all_entities
    ]
    
    return render_template(
        "activities_map.html",
        svg_exists=svg_exists,
        vsdx_exists=vsdx_exists,
        current_svg=current_svg,
        current_vsdx=current_vsdx,
        shape_activity_map=shape_activity_map,
        activities=rows,
        active_entity=active_entity_dict,
        all_entities=all_entities_list
    )


# ============================================================
# SERVIR LE SVG
# ============================================================
@activities_map_bp.route("/svg")
def serve_svg():
    active_entity = Entity.get_active()
    
    if not active_entity:
        return jsonify({"error": "Aucune entité active"}), 404
    
    svg_path = get_entity_svg_path(active_entity.id)
    
    if not os.path.exists(svg_path) and os.path.exists(OLD_SVG_PATH):
        svg_path = OLD_SVG_PATH
    
    if not os.path.exists(svg_path):
        return jsonify({"error": "SVG non trouvé"}), 404
    
    return send_file(svg_path, mimetype='image/svg+xml')


# ============================================================
# API ENTITÉS
# ============================================================
@activities_map_bp.route("/api/entities", methods=["GET"])
def list_entities():
    from flask import session
    
    user_id = session.get('user_id')
    active_entity_id = session.get('active_entity_id')
    
    if not user_id:
        return jsonify([])
    
    entities = Entity.query.filter_by(owner_id=user_id).order_by(Entity.name).all()
    
    return jsonify([
        {
            "id": e.id,
            "name": e.name,
            "description": e.description,
            "svg_filename": e.svg_filename,
            "is_active": (e.id == active_entity_id),
            "activities_count": Activities.query.filter_by(entity_id=e.id).count()
        }
        for e in entities
    ])


@activities_map_bp.route("/api/entities", methods=["POST"])
def create_entity():
    from flask import session
    
    data = request.get_json()
    
    if not data or not data.get("name"):
        return jsonify({"error": "Nom requis"}), 400
    
    user_id = session.get('user_id')
    
    entity = Entity(
        name=data["name"],
        description=data.get("description", ""),
        owner_id=user_id,
        is_active=False
    )
    db.session.add(entity)
    db.session.commit()
    
    ensure_entity_dir(entity.id)
    
    return jsonify({
        "status": "ok",
        "entity": {
            "id": entity.id,
            "name": entity.name,
            "description": entity.description,
            "is_active": entity.is_active
        }
    })


@activities_map_bp.route("/api/entities/<int:entity_id>/activate", methods=["POST"])
def activate_entity(entity_id):
    from flask import session
    
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({"error": "Non connecté"}), 401
    
    entity = Entity.query.filter_by(id=entity_id, owner_id=user_id).first()
    
    if not entity:
        return jsonify({"error": "Entité non trouvée ou non autorisée"}), 404
    
    try:
        session['active_entity_id'] = entity.id
        
        return jsonify({
            "status": "ok",
            "message": f"Entité '{entity.name}' activée"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@activities_map_bp.route("/api/entities/<int:entity_id>", methods=["DELETE"])
def delete_entity(entity_id):
    from flask import session
    
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({"error": "Non connecté"}), 401
    
    entity = Entity.query.filter_by(id=entity_id, owner_id=user_id).first()
    
    if not entity:
        return jsonify({"error": "Entité non trouvée ou non autorisée"}), 404
    
    entity_dir = os.path.join(ENTITIES_DIR, f"entity_{entity_id}")
    if os.path.exists(entity_dir):
        shutil.rmtree(entity_dir)
    
    entity_name = entity.name
    
    try:
        db.session.delete(entity)
        db.session.commit()
        
        if session.get('active_entity_id') == entity_id:
            first = Entity.query.filter_by(owner_id=user_id).first()
            if first:
                session['active_entity_id'] = first.id
            else:
                session.pop('active_entity_id', None)
        
        return jsonify({
            "status": "ok",
            "message": f"Entité '{entity_name}' supprimée"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@activities_map_bp.route("/api/entities/<int:entity_id>", methods=["PATCH"])
def update_entity(entity_id):
    from flask import session
    
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({"error": "Non connecté"}), 401
    
    entity = Entity.query.filter_by(id=entity_id, owner_id=user_id).first()
    
    if not entity:
        return jsonify({"error": "Entité non trouvée ou non autorisée"}), 404
    
    data = request.get_json()
    
    if data.get("name"):
        entity.name = data["name"]
    if "description" in data:
        entity.description = data["description"]
    
    db.session.commit()
    
    return jsonify({
        "status": "ok",
        "entity": {
            "id": entity.id,
            "name": entity.name,
            "description": entity.description
        }
    })


# ============================================================
# EXTRACTION DES ACTIVITÉS DEPUIS LE SVG
# ============================================================
def extract_activities_from_svg(svg_path):
    """
    Parse un fichier SVG Visio et extrait les activités valides.
    """
    activities = []
    seen_names = set()
    
    print(f"[EXTRACT] Parsing SVG: {svg_path}")
    
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
        
        SVG_NS = "http://www.w3.org/2000/svg"
        VISIO_NS = "http://schemas.microsoft.com/visio/2003/SVGExtensions/"
        
        for elem in root.iter():
            mid = elem.get(f"{{{VISIO_NS}}}mID")
            if not mid:
                continue
            
            layer = elem.get(f"{{{VISIO_NS}}}layerMember", "")
            if layer != "1":
                continue
            
            text_content = None
            for text_elem in elem.iter(f"{{{SVG_NS}}}text"):
                t = "".join(text_elem.itertext()).strip()
                if t and len(t) > 2:
                    text_content = t
                    break
            
            if not text_content:
                continue
            
            if len(text_content) > 80:
                continue
            
            if text_content.lower() not in seen_names:
                seen_names.add(text_content.lower())
                activities.append({
                    "shape_id": mid,
                    "name": text_content
                })
                print(f"[EXTRACT] ✓ Activité: shape_id={mid}, name={text_content}")
        
        print(f"[EXTRACT] Total activités extraites: {len(activities)}")
        
    except Exception as e:
        print(f"[EXTRACT] Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    return activities


def sync_activities_with_svg(entity_id, svg_path):
    """
    Synchronise les activités en base avec celles du SVG.
    """
    stats = {
        "added": 0,
        "renamed": 0,
        "unchanged": 0,
        "deleted_warning": 0,
        "skipped": 0,
        "total_in_svg": 0,
        "renamed_list": [],
        "deleted_list": [],
        "errors": []
    }
    
    print(f"[SYNC] Démarrage pour entity_id={entity_id}")
    
    svg_activities = extract_activities_from_svg(svg_path)
    stats["total_in_svg"] = len(svg_activities)
    
    if not svg_activities:
        print("[SYNC] Aucune activité extraite!")
        return stats
    
    svg_shape_map = {str(act["shape_id"]): act["name"] for act in svg_activities}
    svg_shape_ids = set(svg_shape_map.keys())
    
    existing_activities = Activities.query.filter_by(entity_id=entity_id).all()
    existing_shape_map = {str(a.shape_id): a for a in existing_activities if a.shape_id}
    existing_shape_ids = set(existing_shape_map.keys())
    
    print(f"[SYNC] SVG: {len(svg_shape_ids)} activités | Base: {len(existing_shape_ids)} activités")
    
    # Nouvelles activités
    new_shape_ids = svg_shape_ids - existing_shape_ids
    for shape_id in new_shape_ids:
        name = svg_shape_map[shape_id]
        try:
            new_activity = Activities(
                entity_id=entity_id,
                shape_id=shape_id,
                name=name,
                description=""
            )
            db.session.add(new_activity)
            db.session.flush()
            stats["added"] += 1
            print(f"[SYNC] ➕ AJOUTÉ: '{name}' (shape_id={shape_id})")
        except Exception as e:
            db.session.rollback()
            stats["errors"].append(f"Erreur création {name}: {str(e)[:50]}")
            print(f"[SYNC] ❌ ERREUR création '{name}': {e}")
    
    # Activités existantes (vérifier renommages)
    common_shape_ids = svg_shape_ids & existing_shape_ids
    for shape_id in common_shape_ids:
        svg_name = svg_shape_map[shape_id]
        db_activity = existing_shape_map[shape_id]
        
        if db_activity.name != svg_name:
            old_name = db_activity.name
            db_activity.name = svg_name
            stats["renamed"] += 1
            stats["renamed_list"].append({"old": old_name, "new": svg_name})
            print(f"[SYNC] ✏️ RENOMMÉ: '{old_name}' → '{svg_name}'")
        else:
            stats["unchanged"] += 1
    
    # Activités supprimées du SVG
    deleted_shape_ids = existing_shape_ids - svg_shape_ids
    for shape_id in deleted_shape_ids:
        db_activity = existing_shape_map[shape_id]
        activity_id = db_activity.id
        activity_name = db_activity.name
        
        try:
            Link.query.filter(
                (Link.source_activity_id == activity_id) | 
                (Link.target_activity_id == activity_id)
            ).delete(synchronize_session=False)
            
            db.session.delete(db_activity)
            db.session.commit()
            
            stats["deleted_warning"] += 1
            stats["deleted_list"].append({
                "id": activity_id,
                "name": activity_name,
                "shape_id": shape_id
            })
            print(f"[SYNC] 🗑️ SUPPRIMÉ: '{activity_name}' (shape_id={shape_id})")
        except Exception as e:
            db.session.rollback()
            print(f"[SYNC] ❌ ERREUR suppression '{activity_name}': {e}")
    
    db.session.commit()
    print(f"[SYNC] Terminé: +{stats['added']} ajoutées, ✏️{stats['renamed']} renommées, 🗑️{stats['deleted_warning']} supprimées")
    return stats


# ============================================================
# WIZARD - UPLOAD CARTOGRAPHIE UNIFIÉ (SVG + VSDX)
# ============================================================
@activities_map_bp.route("/upload-cartography", methods=["POST"])
def upload_cartography():
    """
    Route unifiée pour uploader SVG et/ou VSDX.
    Traite d'abord le SVG (création des activités) puis le VSDX (connexions).
    """
    print("[WIZARD] ========================================")
    print("[WIZARD] Début upload cartographie unifié")
    
    active_entity = Entity.get_active()
    
    if not active_entity:
        return jsonify({"error": "Aucune entité active. Veuillez d'abord activer une entité."}), 400
    
    entity_id = active_entity.id
    print(f"[WIZARD] Entité: {active_entity.name} (id={entity_id})")
    
    # Récupérer les paramètres
    mode = request.form.get("mode", "new")
    keep_svg = request.form.get("keep_svg", "false").lower() == "true"
    keep_vsdx = request.form.get("keep_vsdx", "false").lower() == "true"
    clear_connections = request.form.get("clear_connections", "false").lower() == "true"
    
    svg_file = request.files.get("svg_file")
    vsdx_file = request.files.get("vsdx_file")
    
    print(f"[WIZARD] Mode: {mode}")
    print(f"[WIZARD] SVG file: {svg_file.filename if svg_file else 'None'} (keep={keep_svg})")
    print(f"[WIZARD] VSDX file: {vsdx_file.filename if vsdx_file else 'None'} (keep={keep_vsdx})")
    print(f"[WIZARD] Clear connections: {clear_connections}")
    
    stats = {
        "activities": 0,
        "connections": 0,
        "svg_updated": False,
        "vsdx_updated": False,
        "sync": None
    }
    
    try:
        entity_dir = ensure_entity_dir(entity_id)
        
        # ==================== TRAITEMENT SVG ====================
        if svg_file and svg_file.filename:
            if not svg_file.filename.lower().endswith(".svg"):
                return jsonify({"error": "Le fichier cartographie doit être au format SVG"}), 400
            
            svg_path = os.path.join(entity_dir, "carto.svg")
            svg_file.save(svg_path)
            print(f"[WIZARD] SVG sauvegardé: {svg_path}")
            
            active_entity.svg_filename = svg_file.filename
            db.session.commit()
            
            # Synchroniser les activités
            sync_stats = sync_activities_with_svg(entity_id, svg_path)
            stats["sync"] = sync_stats
            stats["activities"] = sync_stats.get("total_in_svg", 0)
            stats["svg_updated"] = True
            
        elif not keep_svg and mode == "new":
            return jsonify({"error": "Veuillez fournir un fichier SVG pour créer une cartographie"}), 400
        
        # Compter les activités existantes si pas de nouveau SVG
        if not stats["activities"]:
            stats["activities"] = Activities.query.filter_by(entity_id=entity_id).count()
        
        # ==================== TRAITEMENT VSDX ====================
        if vsdx_file and vsdx_file.filename:
            if not vsdx_file.filename.lower().endswith(".vsdx"):
                return jsonify({"error": "Le fichier connexions doit être au format VSDX"}), 400
            
            # Sauvegarder le VSDX
            vsdx_path = os.path.join(entity_dir, "connections.vsdx")
            vsdx_file.save(vsdx_path)
            print(f"[WIZARD] VSDX sauvegardé: {vsdx_path}")
            
            # Parser les connexions
            connections, errors = parse_vsdx_connections(vsdx_path)
            
            if errors:
                print(f"[WIZARD] Erreurs parsing VSDX: {errors}")
            
            if connections:
                # Récupérer les activités pour validation
                activities = Activities.query.filter_by(entity_id=entity_id).all()
                existing_activities = {act.name: act.id for act in activities}
                
                valid_conns, invalid_conns, missing = validate_connections_against_activities(
                    connections, existing_activities
                )
                
                print(f"[WIZARD] Connexions: {len(valid_conns)} valides, {len(invalid_conns)} invalides")
                
                # Supprimer les anciennes connexions si demandé
                if clear_connections:
                    deleted = Link.query.filter_by(entity_id=entity_id).delete()
                    print(f"[WIZARD] {deleted} anciennes connexions supprimées")
                
                # Importer les connexions valides
                imported_count = 0
                for conn in valid_conns:
                    source_activity_id = conn['source_activity_id']
                    target_activity_id = conn['target_activity_id']
                    
                    # Vérifier si existe déjà
                    existing_link = Link.query.filter_by(
                        entity_id=entity_id,
                        source_activity_id=source_activity_id,
                        target_activity_id=target_activity_id
                    ).first()
                    
                    if existing_link:
                        continue
                    
                    # Créer la Data si nécessaire
                    data_id = None
                    if conn.get('data_name'):
                        existing_data = Data.query.filter_by(
                            entity_id=entity_id,
                            name=conn['data_name']
                        ).first()
                        
                        if existing_data:
                            data_id = existing_data.id
                        else:
                            new_data = Data(
                                entity_id=entity_id,
                                name=conn['data_name'],
                                type=_normalize_link_type(conn.get("data_type")) or "nourrissante"
                            )
                            db.session.add(new_data)
                            db.session.flush()
                            data_id = new_data.id
                    
                    # Type du lien
                    raw_type = conn.get("data_type") or conn.get("type")
                    link_type = _normalize_link_type(raw_type) or "nourrissante"
                    
                    new_link = Link(
                        entity_id=entity_id,
                        source_activity_id=source_activity_id,
                        target_activity_id=target_activity_id,
                        source_data_id=data_id,
                        type=link_type,
                        description=conn.get("data_name") or conn.get("description")
                    )
                    
                    db.session.add(new_link)
                    imported_count += 1
                
                db.session.commit()
                stats["connections"] = imported_count
                stats["vsdx_updated"] = True
                print(f"[WIZARD] {imported_count} connexions importées")
        
        # Compter les connexions existantes si pas de nouveau VSDX
        if not stats["connections"]:
            stats["connections"] = Link.query.filter_by(entity_id=entity_id).count()
        
        print(f"[WIZARD] ========================================")
        print(f"[WIZARD] Terminé: {stats['activities']} activités, {stats['connections']} connexions")
        
        return jsonify({
            "status": "ok",
            "message": "Cartographie mise à jour avec succès",
            "stats": stats
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"[WIZARD] ❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ============================================================
# UPLOAD CARTOGRAPHIE (ancien - conservé pour compatibilité)
# ============================================================
@activities_map_bp.route("/upload-carto", methods=["POST"])
def upload_carto():
    """Upload une nouvelle cartographie SVG."""
    print("[UPLOAD] Début upload")
    
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier reçu"}), 400
    
    file = request.files["file"]
    
    if file.filename == "":
        return jsonify({"error": "Nom de fichier vide"}), 400
    
    filename_lower = file.filename.lower()
    
    if not filename_lower.endswith(".svg"):
        return jsonify({"error": "Format SVG requis"}), 400
    
    active_entity = Entity.get_active()
    
    if not active_entity:
        return jsonify({"error": "Aucune entité active"}), 400
    
    print(f"[UPLOAD] Entité: {active_entity.name} (id={active_entity.id})")
    
    try:
        entity_dir = ensure_entity_dir(active_entity.id)
        svg_path = os.path.join(entity_dir, "carto.svg")
        
        file.save(svg_path)
        print(f"[UPLOAD] Fichier sauvegardé: {svg_path}")
        
        active_entity.svg_filename = "carto.svg"
        db.session.commit()
        
        sync_stats = sync_activities_with_svg(active_entity.id, svg_path)
        
        return jsonify({
            "status": "ok",
            "message": f"Cartographie mise à jour",
            "sync": sync_stats
        })
        
    except Exception as e:
        print(f"[UPLOAD] Erreur: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ============================================================
# CONNEXIONS - PREVIEW
# ============================================================
@activities_map_bp.route("/preview-connections", methods=["POST"])
def preview_connections():
    """Analyse un fichier VSDX et retourne un aperçu des connexions."""
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier reçu"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Nom de fichier vide"}), 400

    if not file.filename.lower().endswith(".vsdx"):
        return jsonify({"error": "Format non supporté (VSDX requis)"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix='.vsdx') as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        connections, errors = parse_vsdx_connections(tmp_path)

        if errors:
            return jsonify({
                "status": "error",
                "errors": errors
            }), 400

        active_entity = Entity.get_active()
        if not active_entity:
            return jsonify({"error": "Aucune entité active"}), 400
            
        activities = Activities.query.filter_by(entity_id=active_entity.id).all()
        existing_activities = {act.name: act.id for act in activities}

        valid, invalid, missing = validate_connections_against_activities(
            connections, existing_activities
        )

        return jsonify({
            "status": "ok",
            "total_connections": len(connections),
            "valid_connections": len(valid),
            "invalid_connections": len(invalid),
            "connections": [
                {
                    "source": c['source_name'],
                    "target": c['target_name'],
                    "data_name": c.get('data_name'),
                    "data_type": c.get('data_type'),
                    "valid": c['source_name'] in existing_activities and c['target_name'] in existing_activities
                }
                for c in connections
            ],
            "missing_activities": missing
        })

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ============================================================
# CONNEXIONS - IMPORT
# ============================================================
@activities_map_bp.route("/import-connections", methods=["POST"])
def import_connections():
    """Importe les connexions d'un fichier VSDX dans la base de données."""
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier reçu"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Nom de fichier vide"}), 400

    if not file.filename.lower().endswith(".vsdx"):
        return jsonify({"error": "Format non supporté (VSDX requis)"}), 400

    clear_existing = request.form.get('clear_existing', 'false').lower() == 'true'

    with tempfile.NamedTemporaryFile(delete=False, suffix='.vsdx') as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        connections, errors = parse_vsdx_connections(tmp_path)

        if errors:
            return jsonify({
                "status": "error",
                "errors": errors
            }), 400

        active_entity = Entity.get_active()
        if not active_entity:
            return jsonify({"error": "Aucune entité active"}), 400
            
        activities = Activities.query.filter_by(entity_id=active_entity.id).all()
        existing_activities = {act.name: act.id for act in activities}

        entity_id = active_entity.id

        valid_conns, invalid_conns, missing = validate_connections_against_activities(
            connections, existing_activities
        )

        if not valid_conns:
            return jsonify({
                "status": "error",
                "error": "Aucune connexion valide trouvée",
                "missing_activities": missing
            }), 400

        if clear_existing:
            Link.query.filter_by(entity_id=entity_id).delete()
            db.session.commit()

        imported_count = 0
        skipped_count = 0

        for conn in valid_conns:
            source_activity_id = conn['source_activity_id']
            target_activity_id = conn['target_activity_id']

            existing_link = Link.query.filter_by(
                entity_id=entity_id,
                source_activity_id=source_activity_id,
                target_activity_id=target_activity_id
            ).first()

            if existing_link:
                skipped_count += 1
                continue

            data_id = None
            if conn.get('data_name'):
                existing_data = Data.query.filter_by(
                    entity_id=entity_id,
                    name=conn['data_name']
                ).first()

                if existing_data:
                    data_id = existing_data.id
                else:
                    new_data = Data(
                        entity_id=entity_id,
                        name=conn['data_name'],
                        type=_normalize_link_type(conn.get("data_type")) or "nourrissante"
                    )
                    db.session.add(new_data)
                    db.session.flush()
                    data_id = new_data.id

            raw_type = conn.get("data_type") or conn.get("type")
            link_type = _normalize_link_type(raw_type)

            if not link_type and data_id:
                d = Data.query.get(data_id)
                if d and getattr(d, "type", None):
                    link_type = _normalize_link_type(d.type) or d.type

            if not link_type:
                link_type = "nourrissante"

            description = conn.get("data_name") or conn.get("description")

            new_link = Link(
                entity_id=entity_id,
                source_activity_id=source_activity_id,
                target_activity_id=target_activity_id,
                source_data_id=data_id,
                type=link_type,
                description=description
            )

            db.session.add(new_link)
            imported_count += 1

        db.session.commit()

        return jsonify({
            "status": "ok",
            "message": f"{imported_count} connexion(s) importée(s)",
            "imported": imported_count,
            "skipped": skipped_count,
            "invalid": len(invalid_conns),
            "missing_activities": missing
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ============================================================
# CONNEXIONS - LISTE
# ============================================================
@activities_map_bp.route("/list-connections")
def list_connections():
    """Retourne la liste des connexions existantes."""
    active_entity = Entity.get_active()
    
    if not active_entity:
        return jsonify({"connections": []})
    
    entity_id = active_entity.id
    activities = Activities.query.filter_by(entity_id=entity_id).all()
    activity_names = {act.id: act.name for act in activities}
    
    links = Link.query.filter_by(entity_id=entity_id).all()
    
    connections = []
    for link in links:
        source_name = activity_names.get(link.source_activity_id, "?")
        target_name = activity_names.get(link.target_activity_id, "?")
        
        data_name = None
        if link.source_data_id:
            data = Data.query.get(link.source_data_id)
            if data:
                data_name = data.name
        
        connections.append({
            "id": link.id,
            "source": source_name,
            "target": target_name,
            "data_name": data_name or link.description,
            "data_type": link.type
        })
    
    return jsonify({
        "status": "ok",
        "count": len(connections),
        "connections": connections
    })


# ============================================================
# CONNEXIONS - SUPPRIMER UNE
# ============================================================
@activities_map_bp.route("/delete-connection/<int:link_id>", methods=["DELETE"])
def delete_connection(link_id):
    """Supprime une connexion spécifique."""
    link = Link.query.get(link_id)
    
    if not link:
        return jsonify({"error": "Connexion non trouvée"}), 404
    
    db.session.delete(link)
    db.session.commit()
    
    return jsonify({
        "status": "ok",
        "message": "Connexion supprimée"
    })


# ============================================================
# CONNEXIONS - SUPPRIMER TOUTES
# ============================================================
@activities_map_bp.route("/clear-connections", methods=["DELETE"])
def clear_connections():
    """Supprime toutes les connexions de l'entité active."""
    active_entity = Entity.get_active()
    
    if not active_entity:
        return jsonify({"status": "ok", "deleted": 0})
    
    entity_id = active_entity.id
    
    deleted = Link.query.filter_by(entity_id=entity_id).delete()
    db.session.commit()
    
    return jsonify({
        "status": "ok",
        "message": f"{deleted} connexion(s) supprimée(s)",
        "deleted": deleted
    })


# ============================================================
# RE-SYNCHRONISATION MANUELLE
# ============================================================
@activities_map_bp.route("/resync", methods=["POST"])
def resync_activities():
    """Re-synchronise les activités depuis le SVG existant."""
    active_entity = Entity.get_active()
    
    if not active_entity:
        return jsonify({"error": "Aucune entité active"}), 400
    
    svg_path = get_entity_svg_path(active_entity.id)
    
    if not os.path.exists(svg_path) and os.path.exists(OLD_SVG_PATH):
        svg_path = OLD_SVG_PATH
    
    if not os.path.exists(svg_path):
        return jsonify({"error": "SVG non trouvé"}), 404
    
    try:
        sync_stats = sync_activities_with_svg(active_entity.id, svg_path)
        
        return jsonify({
            "status": "ok",
            "message": f"Re-synchronisation terminée",
            "sync": sync_stats
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@activities_map_bp.route("/update-cartography")
def update_cartography():
    return jsonify({"status": "ok", "message": "Cartographie rechargée"}), 200