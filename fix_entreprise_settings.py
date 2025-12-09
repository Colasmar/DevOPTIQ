#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SCRIPT DE MIGRATION - Paramètres entreprise par entité
=======================================================
Ajoute une colonne entity_id à la table entreprise_settings
pour que chaque entité ait ses propres paramètres.

UTILISATION:
    python fix_entreprise_settings.py
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "Code", "instance", "optiq.db")

def main():
    print("=" * 70)
    print("MIGRATION: Paramètres entreprise par entité")
    print("=" * 70)
    
    if not os.path.exists(DB_PATH):
        print(f"\n❌ Base de données non trouvée: {DB_PATH}")
        return False
    
    print(f"\n📁 Base de données: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Vérifier si la colonne entity_id existe déjà
        cursor.execute("PRAGMA table_info(entreprise_settings)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'entity_id' in columns:
            print("\n✅ La colonne entity_id existe déjà!")
            conn.close()
            return True
        
        print("\n🔄 Ajout de la colonne entity_id...")
        
        # Ajouter la colonne entity_id
        cursor.execute("ALTER TABLE entreprise_settings ADD COLUMN entity_id INTEGER")
        
        # Trouver l'entité active ou l'entité 1
        cursor.execute("SELECT id FROM entities WHERE is_active = 1 LIMIT 1")
        row = cursor.fetchone()
        if row:
            entity_id = row[0]
        else:
            cursor.execute("SELECT id FROM entities ORDER BY id LIMIT 1")
            row = cursor.fetchone()
            entity_id = row[0] if row else 1
        
        # Mettre à jour les lignes existantes avec cette entité
        cursor.execute("UPDATE entreprise_settings SET entity_id = ? WHERE entity_id IS NULL", (entity_id,))
        
        conn.commit()
        
        print(f"  ✓ Colonne entity_id ajoutée")
        print(f"  ✓ Paramètres existants associés à l'entité {entity_id}")
        
        print("\n" + "=" * 70)
        print("✅ MIGRATION TERMINÉE!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERREUR: {e}")
        return False
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
