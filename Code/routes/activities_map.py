# Code/routes/activities_map.py
import os
import re
import shutil
import datetime
import subprocess

from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    redirect,
    url_for
)

from Code.extensions import db
from Code.models.models import Activities

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
HISTORY_DIR = os.path.join(STATIC_DIR, "carto_history")

# Chemin du SVG actif
ACTIVE_SVG = os.path.join(IMG_DIR, "carto_activities.svg")

# Extensions acceptées
ALLOWED_EXTENSIONS = {'.svg', '.vsdx'}


def get_file_extension(filename):
    """Retourne l'extension du fichier en minuscule."""
    return os.path.splitext(filename)[1].lower()


# ============================================================
# 1) PAGE CARTOGRAPHIE (GET /activities/map)
# ============================================================
@activities_map_bp.route("/map")
def activities_map_page():
    """
    Affiche la page de cartographie des activites.
    """
    # Verifier si le SVG existe
    svg_exists = os.path.exists(ACTIVE_SVG)

    # Recuperer toutes les activites avec leur shape_id
    rows = db.session.query(Activities).order_by(Activities.id).all()

    # Creer le mapping ShapeID -> ActivityID
    shape_activity_map = {
        str(act.shape_id): act.id
        for act in rows
        if act.shape_id is not None
    }

    # Recuperer l'historique des fichiers
    history = []
    if os.path.exists(HISTORY_DIR):
        for f in sorted(os.listdir(HISTORY_DIR), reverse=True):
            ext = get_file_extension(f)
            if ext in ALLOWED_EXTENSIONS:
                # Format du nom: YYYYMMDD_HHMMSS_nomoriginal.ext
                parts = f.split("_", 2)  # Split en max 3 parties
                date_str = parts[0] if len(parts) > 0 else ""
                time_str = parts[1] if len(parts) > 1 else ""
                # Le nom original est après les deux premiers underscores
                original_name = parts[2] if len(parts) > 2 else f
                
                history.append({
                    "filename": f,
                    "date": f"{date_str}_{time_str}" if time_str else date_str,
                    "original_name": original_name,
                    "type": ext.upper().replace(".", "")
                })

    return render_template(
        "activities_map.html",
        svg_exists=svg_exists,
        shape_activity_map=shape_activity_map,
        activities=rows,
        carto_history=history
    )


# ============================================================
# 2) RECHARGER LA CARTOGRAPHIE (GET /activities/update-cartography)
# ============================================================
@activities_map_bp.route("/update-cartography")
def update_cartography():
    """
    Point d'entree pour recharger la cartographie (utilise par le frontend).
    """
    return jsonify({"status": "ok", "message": "Cartographie rechargee"}), 200


# ============================================================
# 3) Conversion Visio -> SVG via LibreOffice
# ============================================================
def convert_vsdx_to_svg(vsdx_file, output_dir):
    """
    Convertit un fichier .vsdx en .svg avec LibreOffice en mode headless.
    
    Args:
        vsdx_file: Chemin complet vers le fichier .vsdx
        output_dir: Dossier de sortie pour le SVG
    
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    # Verifier que LibreOffice est disponible
    try:
        result = subprocess.run(
            ["which", "soffice"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return False, "LibreOffice (soffice) n'est pas installe sur ce serveur"
    except Exception:
        return False, "Impossible de verifier la presence de LibreOffice"

    try:
        result = subprocess.run(
            [
                "soffice",
                "--headless",
                "--convert-to", "svg",
                "--outdir", output_dir,
                vsdx_file
            ],
            capture_output=True,
            text=True,
            timeout=120  # Timeout de 120 secondes
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Erreur inconnue"
            return False, f"Erreur LibreOffice: {error_msg}"
        
        return True, None
        
    except subprocess.TimeoutExpired:
        return False, "Timeout: la conversion a pris trop de temps (>120s)"
    except FileNotFoundError:
        return False, "LibreOffice (soffice) n'est pas installe"
    except Exception as e:
        return False, f"Erreur inattendue: {str(e)}"


# ============================================================
# 4) UPLOAD NOUVELLE CARTOGRAPHIE (POST /activities/upload-carto)
# ============================================================
@activities_map_bp.route("/upload-carto", methods=["POST"])
def upload_carto():
    """
    Upload et installe une nouvelle cartographie.
    Accepte les fichiers SVG (direct) ou VSDX (conversion requise).
    """
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier recu"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Nom de fichier vide"}), 400

    ext = get_file_extension(file.filename)
    
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({
            "error": f"Format non supporte. Formats acceptes: SVG, VSDX"
        }), 400

    # Creer les dossiers si necessaire
    os.makedirs(HISTORY_DIR, exist_ok=True)
    os.makedirs(IMG_DIR, exist_ok=True)

    # Sauvegarder le fichier avec timestamp + nom original
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # Nettoyer le nom original (enlever caractères spéciaux)
    original_name = re.sub(r'[^\w\-_\.]', '_', file.filename)
    
    if ext == '.svg':
        # === CAS SVG: Installation directe ===
        svg_name = f"{timestamp}_{original_name}"
        save_path = os.path.join(HISTORY_DIR, svg_name)
        file.save(save_path)
        
        # Copier vers le SVG actif
        shutil.copy(save_path, ACTIVE_SVG)
        
        return jsonify({
            "status": "ok",
            "message": "Cartographie SVG installee avec succes",
            "filename": svg_name
        })
    
    elif ext == '.vsdx':
        # === CAS VSDX: Conversion necessaire ===
        vsdx_name = f"{timestamp}_{original_name}"
        save_path = os.path.join(HISTORY_DIR, vsdx_name)
        file.save(save_path)

        # Convertir en SVG
        success, error_msg = convert_vsdx_to_svg(save_path, HISTORY_DIR)
        
        if not success:
            # Garder le VSDX dans l'historique mais signaler l'erreur
            suggestion = (
                "\n\nAlternative: Exportez votre fichier Visio en SVG "
                "(Fichier > Exporter > SVG) et importez le SVG directement."
            )
            return jsonify({
                "error": error_msg + suggestion
            }), 500

        # Verifier que le SVG a ete genere
        expected_svg = os.path.join(HISTORY_DIR, vsdx_name.replace(".vsdx", ".svg"))
        if not os.path.exists(expected_svg):
            return jsonify({
                "error": "Le fichier SVG n'a pas ete genere. "
                         "Essayez d'exporter en SVG depuis Visio directement."
            }), 500

        # Remplacer le SVG actif
        shutil.copy(expected_svg, ACTIVE_SVG)

        return jsonify({
            "status": "ok",
            "message": "Cartographie VSDX convertie et installee",
            "filename": vsdx_name
        })


# ============================================================
# 5) UTILISER UNE CARTOGRAPHIE PRECEDENTE
# ============================================================
@activities_map_bp.route("/use-carto/<filename>")
def use_carto(filename):
    """
    Restaure une cartographie precedente depuis l'historique.
    """
    # Securite: empecher la traversee de repertoire
    if ".." in filename or "/" in filename or "\\" in filename:
        return jsonify({"error": "Nom de fichier invalide"}), 400

    file_path = os.path.join(HISTORY_DIR, filename)

    if not os.path.exists(file_path):
        return jsonify({"error": "Fichier introuvable dans l'historique"}), 404

    ext = get_file_extension(filename)
    os.makedirs(IMG_DIR, exist_ok=True)

    if ext == '.svg':
        # SVG: copie directe
        shutil.copy(file_path, ACTIVE_SVG)
        
    elif ext == '.vsdx':
        # VSDX: conversion necessaire
        success, error_msg = convert_vsdx_to_svg(file_path, HISTORY_DIR)
        if not success:
            return jsonify({"error": error_msg}), 500

        expected_svg = os.path.join(HISTORY_DIR, filename.replace(".vsdx", ".svg"))
        if not os.path.exists(expected_svg):
            return jsonify({"error": "SVG non genere"}), 500

        shutil.copy(expected_svg, ACTIVE_SVG)
    else:
        return jsonify({"error": "Format de fichier non supporte"}), 400

    return redirect(url_for("activities_map_bp.activities_map_page"))