# Code/routes/roles_view.py

from flask import Blueprint, render_template
from sqlalchemy import text
from Code.extensions import db
from Code.models.models import Role

roles_view_bp = Blueprint('roles_view', __name__, url_prefix='/roles_view', template_folder='templates')

@roles_view_bp.route('/', methods=['GET'])
def view_roles():
    # Récupérer tous les rôles par ordre alphabétique
    roles = Role.query.order_by(Role.name).all()
    
    roles_data = []
    for role in roles:
        # Bloc 1 : Activités où le rôle est Garant
        garant_activities = db.session.execute(
            text("SELECT a.id, a.name, a.description FROM activity_roles ar JOIN activities a ON ar.activity_id = a.id "
                 "WHERE ar.role_id = :rid AND ar.status = 'Garant'"),
            {"rid": role.id}
        ).fetchall()
        block1 = [{"id": row[0], "name": row[1], "description": row[2]} for row in garant_activities]

        # Bloc 2 : Pour l'instant, on laisse ce bloc vide
        block2 = []

        # Bloc 3 : Compétences associées aux activités où le rôle est Garant
        competencies = db.session.execute(
            text("SELECT c.id, c.description FROM activity_roles ar JOIN competencies c ON ar.activity_id = c.activity_id "
                 "WHERE ar.role_id = :rid AND ar.status = 'Garant'"),
            {"rid": role.id}
        ).fetchall()
        block3 = [{"id": comp[0], "description": comp[1]} for comp in competencies]

        # Bloc 4 : Habiletés socio-cognitives associées aux activités où le rôle est Garant
        softskills = db.session.execute(
            text("SELECT s.habilete, s.niveau FROM activity_roles ar JOIN softskills s ON ar.activity_id = s.activity_id "
                 "WHERE ar.role_id = :rid AND ar.status = 'Garant'"),
            {"rid": role.id}
        ).fetchall()
        hsc_dict = {}
        for habilete, niveau in softskills:
            try:
                niveau_int = int(niveau)
            except:
                niveau_int = 0
            if habilete in hsc_dict:
                if niveau_int > hsc_dict[habilete]:
                    hsc_dict[habilete] = niveau_int
            else:
                hsc_dict[habilete] = niveau_int
        block4 = [{"habilete": k, "niveau": str(v)} for k, v in hsc_dict.items()]

        roles_data.append({
            "role": {"id": role.id, "name": role.name},
            "block1": block1,
            "block2": block2,
            "block3": block3,
            "block4": block4
        })
    return render_template("roles_view.html", roles_data=roles_data)
