#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SCRIPT DE MIGRATION - CORRECTION CONTRAINTE UNIQUE
===================================================
Ce script corrige la contrainte UNIQUE sur activities.shape_id
pour qu'elle soit sur (entity_id, shape_id) au lieu de shape_id seul.

UTILISATION:
    python fix_unique_constraint.py

ATTENTION: Faire une sauvegarde avant d'exécuter ce script!
"""

import os
import sqlite3
import shutil
from datetime import datetime

# Chemin vers la base de données
DB_PATH = os.path.join(os.path.dirname(__file__), "Code", "instance", "optiq.db")

def main():
    print("=" * 70)
    print("MIGRATION: Correction contrainte UNIQUE sur activities")
    print("=" * 70)
    
    # Vérifier que la DB existe
    if not os.path.exists(DB_PATH):
        print(f"\n❌ Base de données non trouvée: {DB_PATH}")
        return False
    
    print(f"\n📁 Base de données: {DB_PATH}")
    
    # Créer une sauvegarde
    backup_path = DB_PATH + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"📦 Création sauvegarde: {backup_path}")
    shutil.copy2(DB_PATH, backup_path)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Vérifier les index existants sur activities
        print("\n🔍 Analyse des index existants...")
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='activities'")
        indexes = cursor.fetchall()
        
        for idx_name, idx_sql in indexes:
            print(f"  - {idx_name}: {idx_sql}")
        
        # Supprimer les index UNIQUE sur shape_id seul
        print("\n🗑️ Suppression des anciens index sur shape_id...")
        for idx_name, idx_sql in indexes:
            if idx_name and 'shape_id' in (idx_sql or '').lower():
                print(f"  Suppression de: {idx_name}")
                cursor.execute(f"DROP INDEX IF EXISTS {idx_name}")
        
        # Vérifier s'il y a une contrainte UNIQUE inline dans la table
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='activities'")
        table_sql = cursor.fetchone()[0]
        print(f"\n📋 Définition actuelle de la table:\n{table_sql}")
        
        # Si la contrainte UNIQUE est dans la définition de la table, on doit recréer la table
        if 'UNIQUE' in table_sql.upper() and 'shape_id' in table_sql.lower():
            print("\n⚠️ Contrainte UNIQUE inline détectée - Recréation de la table nécessaire...")
            
            # 1. Renommer l'ancienne table
            cursor.execute("ALTER TABLE activities RENAME TO activities_old")
            
            # 2. Créer la nouvelle table sans contrainte UNIQUE sur shape_id
            cursor.execute("""
                CREATE TABLE activities (
                    id INTEGER NOT NULL PRIMARY KEY,
                    shape_id VARCHAR(50),
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    is_result BOOLEAN NOT NULL DEFAULT 0,
                    duration_minutes REAL DEFAULT 0,
                    delay_minutes REAL DEFAULT 0,
                    entity_id INTEGER,
                    FOREIGN KEY(entity_id) REFERENCES entities(id)
                )
            """)
            
            # 3. Copier les données
            cursor.execute("""
                INSERT INTO activities (id, shape_id, name, description, is_result, duration_minutes, delay_minutes, entity_id)
                SELECT id, shape_id, name, description, is_result, duration_minutes, delay_minutes, entity_id
                FROM activities_old
            """)
            
            # 4. Supprimer l'ancienne table
            cursor.execute("DROP TABLE activities_old")
            
            print("  ✓ Table recréée sans contrainte UNIQUE sur shape_id")
        
        # Créer le nouvel index UNIQUE sur (entity_id, shape_id)
        print("\n✨ Création du nouvel index UNIQUE sur (entity_id, shape_id)...")
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS ix_activities_entity_shape 
            ON activities(entity_id, shape_id)
            WHERE shape_id IS NOT NULL
        """)
        print("  ✓ Index créé: ix_activities_entity_shape")
        
        # Commit
        conn.commit()
        
        # Vérification finale
        print("\n🔍 Vérification des index après migration...")
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='activities'")
        indexes = cursor.fetchall()
        for idx_name, idx_sql in indexes:
            if idx_name:
                print(f"  - {idx_name}")
        
        print("\n" + "=" * 70)
        print("✅ MIGRATION TERMINÉE AVEC SUCCÈS!")
        print("=" * 70)
        print(f"\n💾 Sauvegarde conservée: {backup_path}")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERREUR: {e}")
        print(f"\n🔄 Restauration depuis la sauvegarde...")
        conn.close()
        shutil.copy2(backup_path, DB_PATH)
        print("  ✓ Base restaurée")
        return False
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
