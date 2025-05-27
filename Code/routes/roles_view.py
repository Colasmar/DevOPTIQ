from flask import Blueprint, render_template
from sqlalchemy import text, func, bindparam
from Code.extensions import db
from Code.models.models import Role

roles_view_bp = Blueprint('roles_view', __name__, url_prefix='/roles_view', template_folder='templates')

@roles_view_bp.route('/', methods=['GET'])
def view_roles():
    # On récupère tous les rôles par ordre alphabétique (insensible à la casse).
    roles = Role.query.order_by(func.lower(Role.name)).all()

    roles_data = []
    for role in roles:
        # Bloc 1 : Activités où le rôle est Garant
        stmt1 = text("""
            SELECT a.id, a.name, a.description
            FROM activity_roles ar
            JOIN activities a ON ar.activity_id = a.id
            WHERE ar.role_id = :rid AND ar.status = 'Garant'
        """)
        garant_activities = db.session.execute(stmt1, {"rid": role.id}).fetchall()
        block1 = [{"id": row[0], "name": row[1], "description": row[2]} for row in garant_activities]

        # Bloc 2 : Tâches où ce rôle intervient (non Garant)
        stmt2 = text("""
            SELECT a.id AS activity_id, a.name AS activity_name,
                   t.id AS task_id, t.name AS task_name,
                   tr.status AS role_status
            FROM tasks t
            JOIN activities a ON a.id = t.activity_id
            JOIN task_roles tr ON tr.task_id = t.id
            WHERE tr.role_id = :rid
            ORDER BY a.name, t.name
        """)
        non_garant_tasks = db.session.execute(stmt2, {"rid": role.id}).fetchall()
        block2 = [
            {
                "activity_id": row.activity_id,
                "activity_name": row.activity_name,
                "task_id": row.task_id,
                "task_name": row.task_name,
                "status": row.role_status
            }
            for row in non_garant_tasks
        ]

        # Bloc 3 : Récupération des compétences associées aux activités Garant...
        stmt3 = text("""
            SELECT c.id, c.description
            FROM competencies c
            JOIN activity_roles ar ON c.activity_id = ar.activity_id
            WHERE ar.role_id = :rid AND ar.status = 'Garant'
        """)
        competencies = db.session.execute(stmt3, {"rid": role.id}).fetchall()
        block3 = [{"id": comp[0], "description": comp[1]} for comp in competencies]

        # Bloc 4 : Récupération des savoirs, savoir-faire, aptitudes et softskills
        # Filtrés par les activités qui contiennent les tâches où ce rôle intervient

        # Obtenir les IDs des activités qui contiennent des tâches où ce rôle intervient
        # Obtenir les IDs des activités liées aux tâches OU en tant que Garant
        stmt_ids = text("""
            SELECT DISTINCT ar.activity_id
            FROM activity_roles ar
            WHERE ar.role_id = :rid AND ar.status = 'Garant'
        """)
        activity_ids = [row[0] for row in db.session.execute(stmt_ids, {"rid": role.id}).fetchall()]


        savoirs = {}
        savoir_faires = {}
        aptitudes = {}
        softskills = {}

        if activity_ids:  # S’assurer qu’il y a des activités à rechercher
            # Savoirs
            stmt_savoirs = (
                text("SELECT s.id, s.description FROM savoirs s WHERE s.activity_id IN :act_ids")
                .bindparams(bindparam("act_ids", expanding=True))
            )
            for row in db.session.execute(stmt_savoirs, {"act_ids": activity_ids}).fetchall():
                savoirs[row[0]] = row[1]

            # Savoir-faire
            stmt_savoir_faires = (
                text("SELECT sf.id, sf.description FROM savoir_faires sf WHERE sf.activity_id IN :act_ids")
                .bindparams(bindparam("act_ids", expanding=True))
            )
            for row in db.session.execute(stmt_savoir_faires, {"act_ids": activity_ids}).fetchall():
                savoir_faires[row[0]] = row[1]

            # Aptitudes
            stmt_aptitudes = (
                text("SELECT a.id, a.description FROM aptitudes a WHERE a.activity_id IN :act_ids")
                .bindparams(bindparam("act_ids", expanding=True))
            )
            for row in db.session.execute(stmt_aptitudes, {"act_ids": activity_ids}).fetchall():
                aptitudes[row[0]] = row[1]

            # Softskills
            stmt_softskills = (
                text("""
                    SELECT ss.id, ss.habilete, ss.niveau, ss.justification
                    FROM softskills ss
                    WHERE ss.activity_id IN :act_ids
                """)
                .bindparams(bindparam("act_ids", expanding=True))
            )
            for row in db.session.execute(stmt_softskills, {"act_ids": activity_ids}).fetchall():
                softskills[row[0]] = {
                    "habilete": row[1],
                    "niveau": row[2],
                    "justification": row[3] or "Pas de justification"
                }

        # Intégration dans le bloc 4
        block4 = []
        added_savoirs = set()
        added_savoir_faires = set()
        added_aptitudes = set()
        added_softskills = set()

        for _id, desc in savoirs.items():
            if _id not in added_savoirs:
                block4.append({"type": "savoir", "value": desc})
                added_savoirs.add(_id)

        for _id, desc in savoir_faires.items():
            if _id not in added_savoir_faires:
                block4.append({"type": "savoir-faire", "value": desc})
                added_savoir_faires.add(_id)

        for _id, desc in aptitudes.items():
            if _id not in added_aptitudes:
                block4.append({"type": "aptitude", "value": desc})
                added_aptitudes.add(_id)

        for _id, details in softskills.items():
            if _id not in added_softskills:
                block4.append({
                    "type": "softskill",
                    "value": details["habilete"],
                    "niveau": details["niveau"],
                    "justification": details["justification"]
                })
                added_softskills.add(_id)

        # Ajouter les données récapitulatives du rôle
        roles_data.append({
            "role": {"id": role.id, "name": role.name},
            "block1": block1,
            "block2": block2,
            "block3": block3,
            "block4": block4
        })

    return render_template("roles_view.html", roles_data=roles_data)
