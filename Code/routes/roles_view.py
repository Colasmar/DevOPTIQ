from flask import Blueprint, render_template
from sqlalchemy import text
from Code.extensions import db
from Code.models.models import Role

roles_view_bp = Blueprint('roles_view', __name__, url_prefix='/roles_view', template_folder='templates')

@roles_view_bp.route('/', methods=['GET'])
def view_roles():
    roles = Role.query.order_by(Role.name).all()

    roles_data = []
    for role in roles:
        # Bloc 1 : Activités où ce rôle est Garant
        garant_activities = db.session.execute(
            text("""
                SELECT a.id, a.name, a.description
                FROM activity_roles ar
                JOIN activities a ON ar.activity_id = a.id
                WHERE ar.role_id = :rid
                  AND ar.status = 'Garant'
            """),
            {"rid": role.id}
        ).fetchall()
        block1 = [{"id": row[0], "name": row[1], "description": row[2]} for row in garant_activities]

        # Bloc 2 : Activités/Tâches où ce rôle intervient (non Garant)
        non_garant_activities = db.session.execute(
            text("""
                SELECT a.id, a.name, a.description
                FROM activity_roles ar
                JOIN activities a ON ar.activity_id = a.id
                WHERE ar.role_id = :rid
                  AND ar.status != 'Garant'
            """),
            {"rid": role.id}
        ).fetchall()
        block2 = [{"id": row[0], "name": row[1], "description": row[2]} for row in non_garant_activities]

        # Bloc 3 : Compétences associées aux activités Garant
        competencies = db.session.execute(
            text("""
                SELECT c.id, c.description
                FROM activity_roles ar
                JOIN competencies c ON ar.activity_id = c.activity_id
                WHERE ar.role_id = :rid
                  AND ar.status = 'Garant'
            """),
            {"rid": role.id}
        ).fetchall()
        block3 = [{"id": comp[0], "description": comp[1]} for comp in competencies]

        # Bloc 4 : Habiletés socio-cognitives de TOUTES les activités du rôle
        # (peu importe le status)
        softskills_raw = db.session.execute(
            text("""
                SELECT s.id, s.habilete, s.niveau
                FROM activity_roles ar
                JOIN softskills s ON ar.activity_id = s.activity_id
                WHERE ar.role_id = :rid
            """),
            {"rid": role.id}
        ).fetchall()

        # On parse la partie numérique pour comparer les niveaux
        import re
        hsc_dict = {}
        for row in softskills_raw:
            s_id, s_habilete, s_niveau = row
            # Cherche le premier chiffre dans la chaîne (ex: "4 (excellence)" => 4)
            match = re.search(r'(\d)', s_niveau)
            numeric_val = int(match.group(1)) if match else 0

            if s_habilete in hsc_dict:
                # Si la nouvelle occurrence a un niveau numérique supérieur, on met à jour
                if numeric_val > hsc_dict[s_habilete]["numeric_val"]:
                    hsc_dict[s_habilete] = {
                        "id": s_id,
                        "habilete": s_habilete,
                        "niveau": s_niveau,       # on conserve la chaîne complète
                        "numeric_val": numeric_val
                    }
            else:
                # Première fois qu'on voit cette HSC
                hsc_dict[s_habilete] = {
                    "id": s_id,
                    "habilete": s_habilete,
                    "niveau": s_niveau,         # on conserve la chaîne complète
                    "numeric_val": numeric_val
                }

        # Construire la liste finale, en ignorant le champ numeric_val
        block4 = []
        for hsc_data in hsc_dict.values():
            block4.append({
                "id": hsc_data["id"],
                "habilete": hsc_data["habilete"],
                "niveau": hsc_data["niveau"]
            })

        roles_data.append({
            "role": {"id": role.id, "name": role.name},
            "block1": block1,
            "block2": block2,
            "block3": block3,
            "block4": block4
        })

    return render_template("roles_view.html", roles_data=roles_data)
