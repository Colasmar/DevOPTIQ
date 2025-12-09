#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SCRIPT DE NETTOYAGE DE LA BASE DE DONNÉES
==========================================
Ce script supprime les fausses activités (éléments graphiques Visio)
de la base de données.

UTILISATION:
    python cleanup_activities.py

ATTENTION: Faire une sauvegarde avant d'exécuter ce script!
"""

import os
import sys
import re
import sqlite3

# Chemin vers la base de données
DB_PATH = os.path.join(os.path.dirname(__file__), "Code", "instance", "optiq.db")

# Patterns des fausses activités à supprimer
FAKE_PATTERNS = [
    r'^Feuille\.',
    r'^Sheet\.',
    r'^Page\s*\d*$',
    r'^Connecteur',
    r'^Connector',
    r'^Dynamic connector',
    r'^Lien dynamique',
    r'^Ligne',
    r'^Line\.',
    r'^Rectangle\.',
    r'^Ellipse',
    r'^Cercle',
    r'^Circle',
    r'^Texte\.',
    r'^Text\.',
    r'^Coche',
    r'^Document\.',
    r'^Processus arrondi',
    r'^Votre avis',
    r'^Séparateur$',
    r'^Conteneur',
    r'^Liste de couloirs',
    r'^Liste de phases',
    r'^Couloir',
    r'^Swimlane',
    r'^Customer relation\.\d+$',
    r'^Administration\.\d+$',
    r'^Big If\.\d+$',
]

def is_fake_activity(name):
    """Vérifie si une activité est une fausse activité."""
    if not name:
        return False
    
    for pattern in FAKE_PATTERNS:
        if re.match(pattern, name, re.IGNORECASE):
            return True
    
    # Aussi supprimer les noms trop courts ou juste des chiffres
    if len(name) <= 2:
        return True
    if name.isdigit():
        return True
    
    return False


def main():
    print("=" * 60)
    print("SCRIPT DE NETTOYAGE DES ACTIVITÉS")
    print("=" * 60)
    
    # Vérifier que la DB existe
    if not os.path.exists(DB_PATH):
        print(f"\n❌ Base de données non trouvée: {DB_PATH}")
        print("Vérifiez le chemin.")
        sys.exit(1)
    
    print(f"\n📁 Base de données: {DB_PATH}")
    
    # Connexion
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Récupérer toutes les activités
    cursor.execute("SELECT id, name, entity_id FROM activities")
    activities = cursor.fetchall()
    
    print(f"\n📊 Total activités dans la DB: {len(activities)}")
    
    # Identifier les fausses activités
    to_delete = []
    to_keep = []
    
    for act_id, name, entity_id in activities:
        if is_fake_activity(name):
            to_delete.append((act_id, name, entity_id))
        else:
            to_keep.append((act_id, name, entity_id))
    
    print(f"\n✅ Activités valides à conserver: {len(to_keep)}")
    print(f"❌ Fausses activités à supprimer: {len(to_delete)}")
    
    if not to_delete:
        print("\n✨ Aucune fausse activité à supprimer!")
        conn.close()
        return
    
    # Afficher les activités à supprimer
    print("\n" + "-" * 60)
    print("ACTIVITÉS QUI SERONT SUPPRIMÉES:")
    print("-" * 60)
    for act_id, name, entity_id in to_delete[:30]:  # Max 30 pour affichage
        print(f"  ID {act_id}: {name} (entity_id={entity_id})")
    if len(to_delete) > 30:
        print(f"  ... et {len(to_delete) - 30} autres")
    
    # Afficher les activités conservées
    print("\n" + "-" * 60)
    print("ACTIVITÉS QUI SERONT CONSERVÉES:")
    print("-" * 60)
    for act_id, name, entity_id in to_keep:
        print(f"  ID {act_id}: {name} (entity_id={entity_id})")
    
    # Confirmation
    print("\n" + "=" * 60)
    response = input("Confirmer la suppression ? (oui/non): ")
    
    if response.lower() != "oui":
        print("\n⏹️ Opération annulée.")
        conn.close()
        return
    
    # Suppression
    print("\n🔄 Suppression en cours...")
    
    deleted_count = 0
    for act_id, name, entity_id in to_delete:
        try:
            # Supprimer les données liées d'abord
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
            deleted_count += 1
            
        except Exception as e:
            print(f"  ⚠️ Erreur pour ID {act_id}: {e}")
    
    # Commit
    conn.commit()
    conn.close()
    
    print(f"\n✅ {deleted_count} fausses activités supprimées!")
    print("\n🎉 Nettoyage terminé!")
    print("=" * 60)


if __name__ == "__main__":
    main()
