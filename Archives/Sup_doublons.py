import sys
import os

# Ajouter dynamiquement le répertoire racine et le répertoire "Code" au chemin d'import
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'Code'))

try:
    from Code.extensions import db
    from Code.models.models import Activity
    from Code.app import create_app  # Assurez-vous que create_app existe dans votre fichier d'application Flask
except ImportError as e:
    print(f"ERREUR : Problème d'importation des modules. Détails : {e}")
    sys.exit(1)

# Initialisation de l'application Flask
app = create_app()

def clean_duplicates():
    """Supprime les doublons dans la table Activity."""
    with app.app_context():
        try:
            subquery = db.session.query(
                Activity.name,
                db.func.min(Activity.id).label('min_id')
            ).group_by(Activity.name).subquery()

            duplicates = db.session.query(Activity).filter(
                ~Activity.id.in_(db.session.query(subquery.c.min_id))
            ).all()

            for duplicate in duplicates:
                db.session.delete(duplicate)

            db.session.commit()
            print("INFO : Doublons supprimés avec succès.")
        except Exception as e:
            print(f"ERREUR : Une erreur s'est produite lors du nettoyage des doublons. Détails : {e}")

if __name__ == "__main__":
    clean_duplicates()
