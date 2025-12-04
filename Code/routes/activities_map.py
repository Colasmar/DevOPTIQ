# Code/routes/activities_map.py
import os
import re
import shutil
import datetime
import subprocess
import xml.etree.ElementTree as ET

from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    send_file
)

from Code.extensions import db
from Code.models.models import Activities, Entity, Data, Link

# ============================================================
# Blueprint avec prefix /activities
# ============================================================
activities_map_bp = Blueprint(
    "activities_map_bp",
    __name__,
    url_prefix="/activities"
)

# Dossiers
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
IMG_DIR = os.path.join(STATIC_DIR, "img")
ENTITIES_DIR = os.path.join(STATIC_DIR, "entities")

# Extensions acceptées
ALLOWED_EXTENSIONS = {'.svg', '.vsdx'}

# Namespace Visio pour extraction des shape_id
VISIO_NS = "http://schemas.microsoft.com/visio/2003/SVGExtensions/"


def get_file_extension(filename):
    """Retourne l'extension du fichier en minuscule."""
    return os.path.splitext(filename)[1].lower()


def get_entity_svg_path(entity_id):
    """Retourne le chemin du SVG pour une entité donnée."""
    return os.path.join(ENTITIES_DIR, f"entity_{entity_id}", "carto.svg")


def ensure_entity_directories(entity_id):
    """Crée les répertoires nécessaires pour une entité."""
    entity_dir = os.path.join(ENTITIES_DIR, f"entity_{entity_id}")
    os.makedirs(entity_dir, exist_ok=True)
    return entity_dir


# ============================================================
# EXTRACTION DES ACTIVITÉS DEPUIS LE SVG
# ============================================================
def extract_activities_from_svg(svg_path):
    """
    Parse le SVG et extrait les éléments avec un attribut v:mID (Visio shape ID).
    Retourne une liste de dictionnaires {shape_id, name}.
    """
    activities = []
    
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
        
        # Parcourir tous les éléments
        for elem in root.iter():
            # Chercher l'attribut mID dans le namespace Visio
            mid = elem.get(f'{{{VISIO_NS}}}mID')
            if mid:
                # Essayer de récupérer le texte/titre de l'élément
                name = None
                
                # Chercher un élément title enfant
                title_elem = elem.find('.//{http://www.w3.org/2000/svg}title')
                if title_elem is not None and title_elem.text:
                    name = title_elem.text.strip()
                
                # Chercher un élément text
                if not name:
                    text_elem = elem.find('.//{http://www.w3.org/2000/svg}text')
                    if text_elem is not None:
                        texts = []
                        for t in text_elem.itertext():
                            texts.append(t.strip())
                        name = ' '.join(filter(None, texts))
                
                # Nom par défaut si non trouvé
                if not name:
                    name = f"Activité {mid}"
                
                # Éviter les doublons
                if not any(a['shape_id'] == mid for a in activities):
                    activities.append({
                        'shape_id': mid,
                        'name': name
                    })
    
    except Exception as e:
        print(f"Erreur lors du parsing SVG: {e}")
    
    return activities


def sync_activities_with_svg(entity_id, svg_path):
    """
    Synchronise les activités de la base de données avec le SVG.
    - Ajoute les nouvelles activités
    - Ne supprime PAS les activités existantes (pour conserver les données liées)
    
    Retourne un dict avec les statistiques de synchronisation.
    """
    stats = {
        'added': 0,
        'updated': 0,
        'unchanged': 0,
        'total_in_svg': 0
    }
    
    # Extraire les activités du SVG
    svg_activities = extract_activities_from_svg(svg_path)
    stats['total_in_svg'] = len(svg_activities)
    
    print(f"[SYNC] Entité {entity_id}: {len(svg_activities)} activités trouvées dans le SVG")
    
    # Récupérer les activités existantes pour cette entité
    existing_activities = {
        a.shape_id: a 
        for a in Activities.query.filter_by(entity_id=entity_id).all()
        if a.shape_id
    }
    
    print(f"[SYNC] {len(existing_activities)} activités existantes en base")
    
    for svg_act in svg_activities:
        shape_id = svg_act['shape_id']
        name = svg_act['name']
        
        if shape_id in existing_activities:
            stats['unchanged'] += 1
        else:
            print(f"[SYNC] Nouvelle activité: shape_id={shape_id}, name={name}")
            new_activity = Activities(
                entity_id=entity_id,
                shape_id=shape_id,
                name=name,
                description="",
                is_result=False
            )
            db.session.add(new_activity)
            stats['added'] += 1
    
    try:
        db.session.commit()
        print(f"[SYNC] Commit réussi: {stats['added']} ajoutées, {stats['unchanged']} inchangées")
    except Exception as e:
        db.session.rollback()
        print(f"[SYNC] Erreur commit: {e}")
        raise
    
    return stats


# ============================================================
# 1) PAGE CARTOGRAPHIE (GET /activities/map)
# ============================================================
@activities_map_bp.route("/map")
def activities_map_page():
    """
    Affiche la page de cartographie des activités.
    """
    # Récupérer l'entité active
    active_entity = Entity.get_active()
    
    # Récupérer toutes les entités
    all_entities = Entity.query.order_by(Entity.name).all()
    
    # Vérifier si un SVG existe
    svg_exists = False
    if active_entity:
        svg_path = get_entity_svg_path(active_entity.id)
        svg_exists = os.path.exists(svg_path)
    
    # Récupérer les activités
    activities = []
    shape_activity_map = {}
    
    if active_entity:
        activities = Activities.query.filter_by(entity_id=active_entity.id).order_by(Activities.id).all()
        shape_activity_map = {
            str(act.shape_id): act.id
            for act in activities
            if act.shape_id is not None
        }
    
    # Convertir en dictionnaires pour le JSON
    active_entity_dict = None
    if active_entity:
        active_entity_dict = {
            "id": active_entity.id,
            "name": active_entity.name,
            "description": active_entity.description,
            "is_active": active_entity.is_active
        }
    
    all_entities_list = [
        {
            "id": e.id,
            "name": e.name,
            "description": e.description,
            "is_active": e.is_active
        }
        for e in all_entities
    ]
    
    return render_template(
        "activities_map.html",
        svg_exists=svg_exists,
        shape_activity_map=shape_activity_map,
        activities=activities,
        active_entity=active_entity,
        active_entity_dict=active_entity_dict,
        all_entities_list=all_entities_list
    )


# ============================================================
# 2) API: LISTE DES ENTITÉS
# ============================================================
@activities_map_bp.route("/api/entities")
def api_list_entities():
    """Retourne la liste de toutes les entités."""
    entities = Entity.query.order_by(Entity.name).all()
    return jsonify({
        "entities": [
            {
                "id": e.id,
                "name": e.name,
                "description": e.description,
                "is_active": e.is_active,
                "has_svg": os.path.exists(get_entity_svg_path(e.id)),
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "updated_at": e.updated_at.isoformat() if e.updated_at else None,
                "activities_count": Activities.query.filter_by(entity_id=e.id).count()
            }
            for e in entities
        ]
    })


# ============================================================
# 3) API: CRÉER UNE ENTITÉ
# ============================================================
@activities_map_bp.route("/api/entities", methods=["POST"])
def api_create_entity():
    """Crée une nouvelle entité."""
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({"error": "Le nom est requis"}), 400
    
    name = data['name'].strip()
    description = data.get('description', '').strip()
    
    existing = Entity.query.filter_by(name=name).first()
    if existing:
        return jsonify({"error": f"Une entité nommée '{name}' existe déjà"}), 400
    
    entity = Entity(
        name=name,
        description=description,
        is_active=False
    )
    db.session.add(entity)
    db.session.commit()
    
    ensure_entity_directories(entity.id)
    
    return jsonify({
        "status": "ok",
        "message": f"Entité '{name}' créée avec succès",
        "entity": {
            "id": entity.id,
            "name": entity.name,
            "description": entity.description,
            "is_active": entity.is_active
        }
    }), 201


# ============================================================
# 4) API: ACTIVER UNE ENTITÉ
# ============================================================
@activities_map_bp.route("/api/entities/<int:entity_id>/activate", methods=["POST"])
def api_activate_entity(entity_id):
    """Active une entité (et désactive les autres)."""
    entity = Entity.query.get(entity_id)
    
    if not entity:
        return jsonify({"error": "Entité introuvable"}), 404
    
    Entity.query.update({Entity.is_active: False})
    entity.is_active = True
    db.session.commit()
    
    return jsonify({
        "status": "ok",
        "message": f"Entité '{entity.name}' activée",
        "entity_id": entity.id
    })


# ============================================================
# 5) API: SUPPRIMER UNE ENTITÉ
# ============================================================
@activities_map_bp.route("/api/entities/<int:entity_id>", methods=["DELETE"])
def api_delete_entity(entity_id):
    """Supprime une entité et toutes ses données."""
    entity = Entity.query.get(entity_id)
    
    if not entity:
        return jsonify({"error": "Entité introuvable"}), 404
    
    entity_name = entity.name
    was_active = entity.is_active
    
    entity_dir = os.path.join(ENTITIES_DIR, f"entity_{entity_id}")
    if os.path.exists(entity_dir):
        shutil.rmtree(entity_dir)
    
    db.session.delete(entity)
    db.session.commit()
    
    if was_active:
        first_entity = Entity.query.first()
        if first_entity:
            first_entity.is_active = True
            db.session.commit()
    
    return jsonify({
        "status": "ok",
        "message": f"Entité '{entity_name}' supprimée"
    })


# ============================================================
# 6) API: RENOMMER UNE ENTITÉ
# ============================================================
@activities_map_bp.route("/api/entities/<int:entity_id>", methods=["PATCH"])
def api_update_entity(entity_id):
    """Met à jour une entité."""
    entity = Entity.query.get(entity_id)
    
    if not entity:
        return jsonify({"error": "Entité introuvable"}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        new_name = data['name'].strip()
        if new_name:
            existing = Entity.query.filter(
                Entity.name == new_name,
                Entity.id != entity_id
            ).first()
            if existing:
                return jsonify({"error": f"Une entité nommée '{new_name}' existe déjà"}), 400
            entity.name = new_name
    
    if 'description' in data:
        entity.description = data['description'].strip()
    
    entity.updated_at = datetime.datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        "status": "ok",
        "message": "Entité mise à jour",
        "entity": {
            "id": entity.id,
            "name": entity.name,
            "description": entity.description
        }
    })


# ============================================================
# 7) UPLOAD CARTOGRAPHIE
# ============================================================
@activities_map_bp.route("/upload-carto", methods=["POST"])
def upload_carto():
    """Upload et installe une cartographie pour l'entité active."""
    try:
        active_entity = Entity.get_active()
        if not active_entity:
            return jsonify({"error": "Aucune entité active. Créez ou sélectionnez une entité d'abord."}), 400
        
        if "file" not in request.files:
            return jsonify({"error": "Aucun fichier reçu"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "Nom de fichier vide"}), 400

        ext = get_file_extension(file.filename)
        
        if ext not in ALLOWED_EXTENSIONS:
            return jsonify({"error": f"Format non supporté. Formats acceptés: SVG, VSDX"}), 400

        entity_dir = ensure_entity_directories(active_entity.id)
        svg_path = get_entity_svg_path(active_entity.id)
        
        if ext == '.svg':
            file.save(svg_path)
            print(f"[UPLOAD] SVG sauvegardé: {svg_path}")
            
        elif ext == '.vsdx':
            temp_vsdx = os.path.join(entity_dir, "temp_carto.vsdx")
            file.save(temp_vsdx)
            
            success, error_msg = convert_vsdx_to_svg(temp_vsdx, entity_dir)
            
            if not success:
                os.remove(temp_vsdx)
                suggestion = "\n\nAlternative: Exportez votre fichier Visio en SVG et importez le SVG directement."
                return jsonify({"error": error_msg + suggestion}), 500
            
            generated_svg = os.path.join(entity_dir, "temp_carto.svg")
            if os.path.exists(generated_svg):
                shutil.move(generated_svg, svg_path)
            else:
                os.remove(temp_vsdx)
                return jsonify({"error": "Le fichier SVG n'a pas été généré"}), 500
            
            os.remove(temp_vsdx)
        
        active_entity.svg_filename = file.filename
        active_entity.updated_at = datetime.datetime.utcnow()
        db.session.commit()
        
        sync_stats = sync_activities_with_svg(active_entity.id, svg_path)
        
        return jsonify({
            "status": "ok",
            "message": f"Cartographie installée pour '{active_entity.name}'",
            "entity_id": active_entity.id,
            "sync_stats": sync_stats
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"[UPLOAD] Erreur: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ============================================================
# 8) SYNCHRONISER LES ACTIVITÉS
# ============================================================
@activities_map_bp.route("/api/entities/<int:entity_id>/sync", methods=["POST"])
def api_sync_entity(entity_id):
    """Force la synchronisation des activités avec le SVG."""
    entity = Entity.query.get(entity_id)
    
    if not entity:
        return jsonify({"error": "Entité introuvable"}), 404
    
    svg_path = get_entity_svg_path(entity_id)
    if not os.path.exists(svg_path):
        return jsonify({"error": "Aucune cartographie pour cette entité"}), 400
    
    try:
        stats = sync_activities_with_svg(entity_id, svg_path)
        return jsonify({
            "status": "ok",
            "message": "Synchronisation effectuée",
            "stats": stats
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# 9) RÉCUPÉRER LE SVG
# ============================================================
@activities_map_bp.route("/svg")
def get_active_svg():
    """Retourne le contenu du SVG de l'entité active."""
    active_entity = Entity.get_active()
    if not active_entity:
        return jsonify({"error": "Aucune entité active"}), 404
    
    svg_path = get_entity_svg_path(active_entity.id)
    if not os.path.exists(svg_path):
        return jsonify({"error": "Aucune cartographie disponible"}), 404
    
    return send_file(svg_path, mimetype='image/svg+xml')


# ============================================================
# 10) RECHARGER LA CARTOGRAPHIE
# ============================================================
@activities_map_bp.route("/update-cartography")
def update_cartography():
    """Recharge/synchronise la cartographie active."""
    active_entity = Entity.get_active()
    if active_entity:
        svg_path = get_entity_svg_path(active_entity.id)
        if os.path.exists(svg_path):
            try:
                stats = sync_activities_with_svg(active_entity.id, svg_path)
                return jsonify({
                    "status": "ok",
                    "message": "Cartographie rechargée",
                    "stats": stats
                }), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500
    
    return jsonify({"status": "ok", "message": "Aucune entité active"}), 200


# ============================================================
# CONVERSION VSDX -> SVG
# ============================================================
def convert_vsdx_to_svg(vsdx_file, output_dir):
    """Convertit un fichier .vsdx en .svg avec LibreOffice."""
    try:
        result = subprocess.run(["which", "soffice"], capture_output=True, text=True)
        if result.returncode != 0:
            return False, "LibreOffice (soffice) n'est pas installé sur ce serveur"
    except Exception:
        return False, "Impossible de vérifier la présence de LibreOffice"

    try:
        result = subprocess.run(
            ["soffice", "--headless", "--convert-to", "svg", "--outdir", output_dir, vsdx_file],
            capture_output=True, text=True, timeout=120
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Erreur inconnue"
            return False, f"Erreur LibreOffice: {error_msg}"
        
        return True, None
        
    except subprocess.TimeoutExpired:
        return False, "Timeout: la conversion a pris trop de temps (>120s)"
    except FileNotFoundError:
        return False, "LibreOffice (soffice) n'est pas installé"
    except Exception as e:
        return False, f"Erreur inattendue: {str(e)}"