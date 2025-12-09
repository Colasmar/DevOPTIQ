#!/usr/bin/env python3
"""
Script pour nettoyer les activités en trop d'une entité.
"""

import os
import glob
import sqlite3
import xml.etree.ElementTree as ET

# Configuration
DB_PATH = "Code/instance/optiq.db"

SVG_NS = "http://www.w3.org/2000/svg"
VISIO_NS = "http://schemas.microsoft.com/visio/2003/SVGExtensions/"


def find_svg_path(entities_id):
    """Trouve le chemin du SVG pour une entité."""
    
    # Dossier de l'entité
    entities_folder = f"Code/static/entities/entities_{entities_id}"
    
    if os.path.exists(entities_folder):
        # Chercher tous les fichiers .svg dans le dossier
        svg_files = glob.glob(os.path.join(entities_folder, "*.svg"))
        if svg_files:
            return svg_files[0]  # Prendre le premier SVG trouvé
    
    # Fallback: ancien chemin par défaut
    old_path = "Code/static/img/carto_activities.svg"
    if os.path.exists(old_path):
        return old_path
    
    return None


def get_layer1_shape_ids(svg_path):
    """Extrait les shape_id des éléments du layer 1."""
    shape_ids = set()
    
    if not os.path.exists(svg_path):
        print(f"❌ SVG non trouvé: {svg_path}")
        return shape_ids
    
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
        
        for elem in root.iter():
            mid = elem.get(f"{{{VISIO_NS}}}mID")
            if not mid:
                continue
            
            layer = elem.get(f"{{{VISIO_NS}}}layerMember", "")
            if layer == "1":
                shape_ids.add(mid)
        
        print(f"✅ {len(shape_ids)} shape_id trouvés dans le layer 1")
        
    except Exception as e:
        print(f"❌ Erreur parsing SVG: {e}")
    
    return shape_ids


def cleanup_entities_activities(entities_id):
    """Nettoie les activités en trop d'une entité."""
    
    # Trouver le SVG de l'entité
    svg_path = find_svg_path(entities_id)
    
    if not svg_path:
        print(f"❌ SVG non trouvé pour l'entité {entities_id}")
        print(f"   Dossier recherché: Code/static/entities/entities_{entities_id}/")
        return
    
    print(f"📄 SVG trouvé: {svg_path}")
    
    # Extraire les shape_id valides (layer 1)
    valid_shape_ids = get_layer1_shape_ids(svg_path)
    
    if not valid_shape_ids:
        print("❌ Aucun shape_id valide trouvé dans le layer 1")
        return
    
    # Connexion à la base
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Récupérer les activités de cette entité
    cursor.execute("""
        SELECT id, name, shape_id 
        FROM activities 
        WHERE entities.id = ?
        ORDER BY name
    """, (entities_id,))
    
    activities = cursor.fetchall()
    print(f"\n📋 {len(activities)} activités dans l'entité {entities_id}")
    
    # Identifier les activités à supprimer
    to_delete = []
    to_keep = []
    
    for act_id, name, shape_id in activities:
        if shape_id and str(shape_id) in valid_shape_ids:
            to_keep.append((act_id, name, shape_id))
        else:
            to_delete.append((act_id, name, shape_id))
    
    print(f"\n✅ À GARDER ({len(to_keep)}):")
    for act_id, name, shape_id in sorted(to_keep, key=lambda x: x[1]):
        print(f"   {act_id}: {name}")
    
    print(f"\n❌ À SUPPRIMER ({len(to_delete)}):")
    for act_id, name, shape_id in sorted(to_delete, key=lambda x: x[1]):
        print(f"   {act_id}: {name} (shape_id={shape_id})")
    
    if not to_delete:
        print("\n✨ Rien à supprimer !")
        conn.close()
        return
    
    # Demander confirmation
    print(f"\n⚠️  {len(to_delete)} activités seront supprimées.")
    confirm = input("Confirmer ? (oui/non) : ").strip().lower()
    
    if confirm != "oui":
        print("❌ Annulé")
        conn.close()
        return
    
    # Supprimer les activités (avec cascade sur les tables liées)
    deleted = 0
    for act_id, name, _ in to_delete:
        try:
            # Supprimer les données liées
            cursor.execute("DELETE FROM savoirs WHERE activity_id = ?", (act_id,))
            cursor.execute("DELETE FROM savoir_faires WHERE activity_id = ?", (act_id,))
            cursor.execute("DELETE FROM aptitudes WHERE activity_id = ?", (act_id,))
            cursor.execute("DELETE FROM softskills WHERE activity_id = ?", (act_id,))
            cursor.execute("DELETE FROM competencies WHERE activity_id = ?", (act_id,))
            cursor.execute("DELETE FROM constraints WHERE activity_id = ?", (act_id,))
            cursor.execute("DELETE FROM activity_roles WHERE activity_id = ?", (act_id,))
            cursor.execute("DELETE FROM competency_evaluation WHERE activity_id = ?", (act_id,))
            
            # Supprimer l'activité
            cursor.execute("DELETE FROM activities WHERE id = ?", (act_id,))
            
            deleted += 1
            print(f"   ✓ Supprimé: {name}")
            
        except Exception as e:
            print(f"   ✗ Erreur pour {name}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ {deleted} activités supprimées avec succès !")


def main():
    print("=" * 60)
    print("NETTOYAGE DES ACTIVITÉS EN TROP")
    print("=" * 60)
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Base de données non trouvée: {DB_PATH}")
        return
    
    # Lister les entités
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM entities ORDER BY id")
    entities = cursor.fetchall()
    conn.close()
    
    print("\n📋 Entités disponibles:")
    for eid, name in entities:
        # Vérifier si un SVG existe
        svg_path = find_svg_path(eid)
        svg_status = "✓" if svg_path else "✗"
        print(f"   {eid}: {name} [{svg_status}]")
    
    # Demander quelle entité nettoyer
    try:
        entities_id = int(input("\nEntrez l'ID de l'entité à nettoyer: ").strip())
    except ValueError:
        print("❌ ID invalide")
        return
    
    cleanup_entities_activities(entities_id)


if __name__ == "__main__":
    main()