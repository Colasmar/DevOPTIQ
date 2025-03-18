from flask import Blueprint, render_template
from sqlalchemy import text, func
from Code.extensions import db
from Code.models.models import Role

roles_view_bp = Blueprint('roles_view', __name__, url_prefix='/roles_view', template_folder='templates')

@roles_view_bp.route('/', methods=['GET'])
def view_roles():
    # On récupère tous les rôles par ordre alphabétique (insensible à la casse).
    roles = Role.query.order_by(func.lower(Role.name)).all()

    roles_data = []
    for role in roles:
        # Bloc 1 : Activités où le rôle est Garant (pas modifié)
        garant_activities = db.session.execute(
            text("""
                SELECT a.id, a.name, a.description
                FROM activity_roles ar
                JOIN activities a ON ar.activity_id = a.id
                WHERE ar.role_id = :rid AND ar.status = 'Garant'
            """),
            {"rid": role.id}
        ).fetchall()
        block1 = [{"id": row[0], "name": row[1], "description": row[2]} for row in garant_activities]

        # Bloc 2 : Tâches où ce rôle intervient (via task_roles).
        # On récupère l'activité parente, le nom de la tâche et le statut.
        non_garant_tasks = db.session.execute(
            text("""
                SELECT a.id AS activity_id, a.name AS activity_name,
                       t.id AS task_id, t.name AS task_name,
                       tr.status AS role_status
                FROM tasks t
                JOIN activities a ON a.id = t.activity_id
                JOIN task_roles tr ON tr.task_id = t.id
                WHERE tr.role_id = :rid
                ORDER BY a.name, t.name
            """),
            {"rid": role.id}
        ).fetchall()
        # On construit block2 en listant chaque activité/tâche/statut
        block2 = []
        for row in non_garant_tasks:
            block2.append({
                "activity_id": row.activity_id,
                "activity_name": row.activity_name,
                "task_id": row.task_id,
                "task_name": row.task_name,
                "status": row.role_status
            })

        # Bloc 3 : Compétences associées aux activités Garant (inchangé)
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

        # Bloc 4 : Habiletés socio-cognitives (inchangé)
        # On agrège en conservant la plus haute valeur de niveau
        softskills_raw = db.session.execute(
            text("""
                SELECT s.id, s.habilete, s.niveau
                FROM activity_roles ar
                JOIN softskills s ON ar.activity_id = s.activity_id
                WHERE ar.role_id = :rid
                  AND ar.status = 'Garant'
            """),
            {"rid": role.id}
        ).fetchall()
        hsc_dict = {}
        for row in softskills_raw:
            hsc_name = row[1]
            try:
                niveau = int(row[2])
            except ValueError:
                niveau = 0
            if hsc_name in hsc_dict:
                # Conserver l'enregistrement si le nouveau niveau est supérieur
                if niveau > hsc_dict[hsc_name]["niveau"]:
                    hsc_dict[hsc_name] = {"id": row[0], "habilete": hsc_name, "niveau": niveau}
            else:
                hsc_dict[hsc_name] = {"id": row[0], "habilete": hsc_name, "niveau": niveau}
        block4 = list(hsc_dict.values())

        roles_data.append({
            "role": {"id": role.id, "name": role.name},
            "block1": block1,
            "block2": block2,
            "block3": block3,
            "block4": block4
        })

    return render_template("roles_view.html", roles_data=roles_data)
