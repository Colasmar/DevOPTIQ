# Code/routes/roles_view.py

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
        # Bloc 1 : Activités où le rôle est Garant
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

        # Bloc 2 : Tâches où ce rôle intervient (non Garant)
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
        block2 = []
        for row in non_garant_tasks:
            block2.append({
                "activity_id": row.activity_id,
                "activity_name": row.activity_name,
                "task_id": row.task_id,
                "task_name": row.task_name,
                "status": row.role_status
            })

        # Bloc 3 : Récupération des compétences associées aux activités Garant...
        competencies = db.session.execute(
            text("""
                SELECT c.id, c.description
                FROM competencies c
                JOIN activity_roles ar ON c.activity_id = ar.activity_id
                WHERE ar.role_id = :rid AND ar.status = 'Garant'
            """),
            {"rid": role.id}
        ).fetchall()
        block3 = [{"id": comp[0], "description": comp[1]} for comp in competencies]

        # Bloc 4 : Récupération des savoirs, savoir-faire, aptitudes et softskills de toutes les activités
        savoirs = {}
        savoir_faires = {}
        aptitudes = {}
        softskills = {}

        # Récupération des savoirs
        savoirs_query = db.session.execute(
            text("""
                SELECT s.id, s.description
                FROM savoirs s
                JOIN activity_roles ar ON s.activity_id = ar.activity_id
                WHERE ar.role_id IN (
                    SELECT role_id FROM activity_roles WHERE activity_id IN (
                        SELECT activity_id FROM task_roles WHERE role_id = :rid
                    )
                )
            """),
            {"rid": role.id}
        ).fetchall()

        # Remplir le dictionnaire des savoirs
        for row in savoirs_query:
            savoirs[row[0]] = row[1]

        # Récupération des savoir-faire
        savoir_faires_query = db.session.execute(
            text("""
                SELECT sf.id, sf.description
                FROM savoir_faires sf
                JOIN activity_roles ar ON sf.activity_id = ar.activity_id
                WHERE ar.role_id IN (
                    SELECT role_id FROM activity_roles WHERE activity_id IN (
                        SELECT activity_id FROM task_roles WHERE role_id = :rid
                    )
                )
            """),
            {"rid": role.id}
        ).fetchall()

        # Remplir le dictionnaire des savoir-faire
        for row in savoir_faires_query:
            savoir_faires[row[0]] = row[1]

        # Récupération des aptitudes
        aptitudes_query = db.session.execute(
            text("""
                SELECT a.id, a.description
                FROM aptitudes a
                JOIN activity_roles ar ON a.activity_id = ar.activity_id
                WHERE ar.role_id IN (
                    SELECT role_id FROM activity_roles WHERE activity_id IN (
                        SELECT activity_id FROM task_roles WHERE role_id = :rid
                    )
                )
            """),
            {"rid": role.id}
        ).fetchall()

        # Remplir le dictionnaire des aptitudes
        for row in aptitudes_query:
            aptitudes[row[0]] = row[1]

        # Récupération des softskills (avec détails)
        softskills_query = db.session.execute(
            text("""
                SELECT ss.id, ss.habilete, ss.niveau, ss.justification
                FROM softskills ss
                JOIN activity_roles ar ON ss.activity_id = ar.activity_id
                WHERE ar.role_id IN (
                    SELECT role_id FROM activity_roles WHERE activity_id IN (
                        SELECT activity_id FROM task_roles WHERE role_id = :rid
                    )
                )
            """),
            {"rid": role.id}
        ).fetchall()

        # Remplir le dictionnaire des softskills avec details
        for row in softskills_query:
            softskills[row[0]] = {
                "habilete": row[1],
                "niveau": row[2],
                "justification": row[3] if row[3] else "Pas de justification"
            }

        # Intégration dans le bloc 4
        block4 = []
        for id, details in savoirs.items():
            block4.append({"type": "savoir", "value": details})
        for id, details in savoir_faires.items():
            block4.append({"type": "savoir-faire", "value": details})
        for id, details in aptitudes.items():
            block4.append({"type": "aptitude", "value": details})

        # Ajout des softskills dans le bloc 4
        for id, details in softskills.items():
            block4.append({
                "type": "softskill",
                "value": details["habilete"],
                "niveau": details["niveau"],
                "justification": details["justification"]
            })

        # Ajouter les données récapitulatives du rôle
        roles_data.append({
            "role": {"id": role.id, "name": role.name},
            "block1": block1,
            "block2": block2,
            "block3": block3,
            "block4": block4
        })

    return render_template("roles_view.html", roles_data=roles_data)