from flask import render_template
from sqlalchemy import or_, desc
from .activities_bp import activities_bp
from Code.extensions import db
# Importez Role et activity_roles
from Code.models.models import Activities, Task, Link, Data, Performance, Role, activity_roles

@activities_bp.route('/view', methods=['GET'])
def view_activities():
    """
    Reprend la logique d'affichage de l'ancien activities_old.py :
    - On liste toutes les activités (sauf éventuellement celles marquées is_result si vous le souhaitez)
    - Pour chaque activité :
      * Tâches (triées par order)
      * Connexions entrantes (source data ou activity)
      * Connexions sortantes (idem)
      * Performance associée à chaque lien (si existante)
      * Contraintes, etc. (si le template l'exploite)
      * **Garant (le rôle avec le statut 'Garant')** <-- AJOUT
    - On renvoie le tout à display_list.html
    """

    # Si vous souhaitez exclure les activités de type "result", décommentez :
    # activities = Activities.query.filter_by(is_result=False).all()

    # Sinon on récupère tout :
    activities = Activities.query.all()

    activity_data = []
    for activity in activities:
        # Tâches => triées par "order"
        tasks_sorted = db.session.query(Task).filter_by(activity_id=activity.id)\
                           .order_by(Task.order.asc().nullsfirst()).all()

        # Connexions entrantes = liens où (target_activity_id == activity.id) OU (target_data_id == activity.id)
        incoming_links = db.session.query(Link).filter(
            or_(
                Link.target_activity_id == activity.id,
                Link.target_data_id == activity.id
            )
        ).all()

        incoming_list = []
        for link in incoming_links:
            data_name = resolve_data_name(link, incoming=True)
            source_name = resolve_source_name(link)
            d_type = resolve_data_type(link, incoming=True)

            incoming_list.append({
                'type': d_type,
                'data_name': data_name,
                'source_name': source_name
            })

        # Connexions sortantes = liens où (source_activity_id == activity.id) OU (source_data_id == activity.id)
        outgoing_links = db.session.query(Link).filter(
            or_(
                Link.source_activity_id == activity.id,
                Link.source_data_id == activity.id
            )
        ).all()

        outgoing_list = []
        for link in outgoing_links:
            data_name = resolve_data_name(link, incoming=False)
            target_name = resolve_target_name(link)
            d_type = resolve_data_type(link, incoming=False)
            perf_obj = link.performance  # relation One-to-One ?

            # On prépare un dict pour la performance
            perf_dict = None
            if perf_obj:
                perf_dict = {
                    "id": perf_obj.id,
                    "name": perf_obj.name,
                    "description": perf_obj.description
                }

            outgoing_list.append({
                'type': d_type,
                'data_name': data_name,
                'target_name': target_name,
                'link_id': link.id,
                'performance': perf_dict
            })

        # NOUVEAU CODE : Récupérer le rôle "Garant" pour cette activité
        # On joint Activities avec la table d'association activity_roles et le modèle Role
        # On filtre sur l'activity_id et le statut 'Garant'
        garant_role = db.session.query(Role).\
                      join(activity_roles).\
                      filter(activity_roles.c.activity_id == activity.id).\
                      filter(activity_roles.c.role_id == Role.id).\
                      filter(activity_roles.c.status == 'Garant').\
                      first() # On prend le premier (et idéalement le seul) garant

        # Préparer le dict pour le garant
        garant_dict = None
        if garant_role:
            garant_dict = {
                "id": garant_role.id,
                "name": garant_role.name
            }


        # Ajout dans la liste pour le template
        activity_data.append({
            'activity': activity,
            'tasks': tasks_sorted,
            'incoming': incoming_list,
            'outgoing': outgoing_list,
            'garant': garant_dict, # <-- AJOUTEZ CETTE LIGNE
            # Les contraintes, softskills, etc. si le template l’exploite :
            'constraints': activity.constraints,
            'competencies': activity.competencies,
            'softskills': activity.softskills,
            'savoirs': activity.savoirs,
            'savoir_faires': activity.savoir_faires,
            'aptitudes': activity.aptitudes
        })

    return render_template('display_list.html', activity_data=activity_data)


# ===================== FONCTIONS UTILITAIRES =====================

def resolve_data_name(link, incoming=True):
    """
    Cherche le nom "data" pour un link, comme dans l'ancien code.
    - Si c'est un incoming link, on va regarder "source_data_id" ou "description" ...
    - Sinon un outgoing => "target_data_id" ...
    - On renvoie le .name de Data si on le trouve, sinon link.description
    """
    # On regarde s'il s'agit d'un incoming (donc la data est sur link.source_data_id)
    # ou un outgoing (data sur link.source_data_id)
    data_id = link.source_data_id if incoming else link.source_data_id
    # L'ancien code considérait aussi link.target_data_id suivant le cas,
    # mais la plus fréquente :
    # - incoming => data sur source_data_id
    # - outgoing => data sur source_data_id
    # Cf. votre ancien code "resolve_data_name_for_incoming/outgoing"
    if not data_id:
        # Si pas de data_id, fallback sur link.description
        return link.description or "[Data inconnue]"
    d_obj = Data.query.get(data_id)
    if d_obj:
        return d_obj.name
    return link.description or "[Data sans nom]"

def resolve_source_name(link):
    """
    Si link.source_activity_id n'est pas null => c'est le nom de l'activité,
    sinon, si link.source_data_id => on va voir si c'est un "Retour" ...
    """
    if link.source_activity_id:
        act = Activities.query.get(link.source_activity_id)
        if act:
            return act.name
        return "[Activité inconnue]"
    elif link.source_data_id:
        d_obj = Data.query.get(link.source_data_id)
        if d_obj:
            return d_obj.name
        return "[Data inconnue]"
    return "[Source ?]"

def resolve_target_name(link):
    """
    Symétrique du source_name, pour link.target_activity_id / target_data_id
    """
    if link.target_activity_id:
        act = Activities.query.get(link.target_activity_id)
        if act:
            return act.name
        return "[Activité inconnue]"
    elif link.target_data_id:
        d_obj = Data.query.get(link.target_data_id)
        if d_obj:
            return d_obj.name
        return "[Data inconnue]"
    return "[Cible ?]"

def resolve_data_type(link, incoming=True):
    """
    Renvoie le type du Data (ex: "déclenchante", "nourrissante", "Retour", etc.)
    ou link.type, selon ce qui est stocké.
    """
    # Ancien code : on regardait Data.type si on a un data_id
    data_id = link.source_data_id if incoming else link.source_data_id
    # Ça peut sembler redondant,
    # mais on reproduit le comportement de l'ancien code pour cohérence.
    if data_id:
        d_obj = Data.query.get(data_id)
        if d_obj and d_obj.type:
            return d_obj.type
    # Fallback : link.type ou "[type?]"
    return link.type or "[type non défini]"