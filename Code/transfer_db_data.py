import sqlite3
import os
from shutil import copyfile

# --- Chemins ---
source_db = r"C:\Users\Hubert.AFDEC\OneDrive - A.F.D.E.C\Documents\DevOPTIQ_Recup\ProjetOPTIQ\Code\instance\optiq.db"
target_db = os.path.join("Code", "instance", "optiq.db")

# --- Étape 1 : Sauvegarde de sécurité de la nouvelle base (juste au cas où) ---
backup_path = target_db + ".backup"
if not os.path.exists(backup_path):
    copyfile(target_db, backup_path)
    print(f"✅ Sauvegarde de la base actuelle : {backup_path}")

# --- Connexion aux deux bases ---
src_conn = sqlite3.connect(source_db)
tgt_conn = sqlite3.connect(target_db)
src_cursor = src_conn.cursor()
tgt_cursor = tgt_conn.cursor()

# --- Étape 2 : Transfert table par table ---
src_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = src_cursor.fetchall()

for (table_name,) in tables:
    if table_name.startswith("sqlite_"):
        continue  # Tables système
    print(f"🔁 Transfert de la table : {table_name}")

    # Récupérer les données
    src_cursor.execute(f"SELECT * FROM {table_name}")
    rows = src_cursor.fetchall()

    # Nettoyage avant insertion
    tgt_cursor.execute(f"DELETE FROM {table_name}")
    columns = [desc[0] for desc in src_cursor.description]
    placeholders = ", ".join(["?"] * len(columns))
    columns_safe = ", ".join([f'"{col}"' for col in columns])  # <-- ici guillemets doubles
    insert_query = f'INSERT INTO "{table_name}" ({columns_safe}) VALUES ({placeholders})'


    # Réinsertion
    for row in rows:
        tgt_cursor.execute(insert_query, row)

tgt_conn.commit()
print("✅ Données copiées avec succès.")

# --- Fermeture ---
src_conn.close()
tgt_conn.close()
print("🚪 Connexions fermées.")
