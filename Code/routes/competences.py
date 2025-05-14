# Code/routes/competences.py

from flask import Blueprint, jsonify, session, render_template, request
from Code.extensions import db
from datetime import datetime
from Code.models.models import (
    Competency, Role, Activities, User, UserRole, Link, activity_roles,
    CompetencyEvaluation, Savoir, SavoirFaire, Aptitude, Softskill
)

competences_bp = Blueprint('competences_bp', __name__, url_prefix='/competences')

@competences_bp.route('/view', methods=['GET'])
def competences_view():
    return render_template('competences_view.html')

# --- Route pour récupérer la liste des rôles ---
@competences_bp.route('/roles', methods=['GET'])
def get_roles():
    roles = Role.query.all()
    return jsonify([{'id': r.id, 'name': r.name} for r in roles])

# --- Routes pour gérer les managers ---

@competences_bp.route('/managers', methods=['GET'])
def get_managers():
    try:
        # Assurez-vous que le rôle 'manager' existe bien dans votre base
        role_manager = Role.query.filter_by(name='manager').first()
        if not role_manager:
            # Gérer le cas où le rôle 'manager' n'existe pas
            print("Warning: Role 'manager' not found in database.")
            return jsonify([])
        # Joindre User avec UserRole pour filtrer par rôle
        managers = User.query.join(UserRole).filter(UserRole.role_id == role_manager.id).all()
        manager_data = [{'id': m.id, 'name': f"{m.first_name} {m.last_name}"} for m in managers]
        return jsonify(manager_data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# --- Route pour tous les utilisateurs ---

@competences_bp.route('/all_users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    result = [{'id': u.id, 'name': f"{u.first_name} {u.last_name}"} for u in users]
    return jsonify(result)

# --- Route pour récupérer les collaborateurs d’un manager ---

@competences_bp.route('/collaborators/<int:manager_id>', methods=['GET'])
def get_collaborators(manager_id):
    # Assurez-vous que le manager_id est valide
    manager = User.query.get(manager_id)
    if not manager:
        return jsonify([]) # Retourne une liste vide si le manager n'existe pas

    # Récupère les utilisateurs dont le manager_id correspond
    collaborateurs = User.query.filter_by(manager_id=manager_id).all()
    result = [{'id': u.id, 'first_name': u.first_name, 'last_name': u.last_name} for u in collaborateurs]
    return jsonify(result)

# --- Route pour récupérer les rôles d'un user ---

@competences_bp.route('/get_user_roles/<int:user_id>', methods=['GET'])
def get_user_roles(user_id):
     # Vérifier si l'utilisateur existe
    user = User.query.get(user_id)
    if not user:
        return jsonify({'roles': []}) # Retourne une liste vide si l'utilisateur n'existe pas

    user_roles = UserRole.query.filter_by(user_id=user_id).all()
    roles = [Role.query.get(ur.role_id) for ur in user_roles]
    roles = [r for r in roles if r] # Filtrer les rôles non trouvés (devrait pas arriver si BDD cohérente)
    return jsonify({'roles': [{'id': r.id, 'name': r.name} for r in roles]})

# --- Route pour ajouter un collaborateur ---

@competences_bp.route('/add_collaborator', methods=['POST'])
def add_collaborator():
    data = request.json
    user_id = data.get('user_id')
    manager_id = data.get('manager_id')
    role_id = data.get('role_id') # Le rôle à ASSIGNER lors de l'ajout

    if not user_id or not manager_id or not role_id:
         return jsonify({'success': False, 'message': 'Données manquantes'}), 400

    # Vérification de l'existence de l'utilisateur
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'Utilisateur non trouvé'}), 404

    # Vérification du manager
    manager = User.query.get(manager_id)
    if not manager:
        return jsonify({'success': False, 'message': 'Manager non trouvé'}), 404

    # Vérification du rôle
    role_to_assign = Role.query.get(role_id)
    if not role_to_assign:
         return jsonify({'success': False, 'message': 'Rôle non trouvé'}), 404


    # Mise à jour du manager de l'utilisateur
    user.manager_id = manager_id

    # Ajouter le rôle à l'utilisateur si ce n'est pas déjà fait
    # Utilise la logique de add_role_to_user pour éviter la duplication de code
    assign_role_resp = add_role_to_user_logic(user_id, role_id)
    if not assign_role_resp['success']:
         # Gérer l'erreur si l'ajout du rôle échoue, mais l'ajout du manager peut quand même réussir
         print(f"Warning: Failed to assign role {role_id} to user {user_id}: {assign_role_resp.get('message')}")
         # On peut quand même continuer si l'ajout du manager a fonctionné

    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Error adding collaborator: {e}")
        return jsonify({'success': False, 'message': 'Database error during add collaborator'}), 500


# --- Route pour ajouter un rôle à un utilisateur (sans supprimer autres rôles) ---
@competences_bp.route('/add_role_to_user', methods=['POST'])
def add_role_to_user_route():
    data = request.json
    user_id = data.get('user_id')
    role_id = data.get('role_id')

    if not user_id or not role_id:
         return jsonify({'success': False, 'message': 'User ID and Role ID are required'}), 400

    result = add_role_to_user_logic(user_id, role_id)
    return jsonify(result)

# Logique interne pour ajouter un rôle (réutilisée par add_collaborator)
def add_role_to_user_logic(user_id, role_id):
    # Vérifier si l'association existe déjà
    existing = UserRole.query.filter_by(user_id=user_id, role_id=role_id).first()
    if existing:
        return {'success': True, 'message': 'Rôle déjà attribué à cet utilisateur'}

    # Vérifier si l'utilisateur et le rôle existent
    user = User.query.get(user_id)
    role = Role.query.get(role_id)
    if not user or not role:
        return {'success': False, 'message': 'Utilisateur ou Rôle non trouvé'}

    # Sinon, ajouter le rôle
    try:
        new_user_role = UserRole(user_id=user_id, role_id=role_id)
        db.session.add(new_user_role)
        # Note: Le commit devrait idéalement être fait par la fonction appelante (ex: add_collaborator)
        # pour gérer les transactions. Si cette fonction est appelée seule, un commit est nécessaire ici.
        # Pour l'instant, on laisse le commit dans la route si elle est appelée directement.
        # Si elle est appelée par add_collaborator, le commit sera fait là-bas.
        # On peut ajouter un paramètre pour contrôler le commit si besoin.
        # db.session.commit() # Commenté ici pour que add_collaborator gère le commit

        return {'success': True, 'message': 'Rôle ajouté avec succès'}
    except Exception as e:
        # db.session.rollback() # Commenté pour la même raison que le commit
        print(f"Error adding role to user: {e}")
        return {'success': False, 'message': f'Database error: {e}'}



# --- Route pour récupérer compétences d’un rôle avec connexions sortantes ---
# Cette route convient parfaitement pour la liste des compétences (avec connexions)
# ET pour la liste des compétences pour la synthèse.
@competences_bp.route('/get_role_competencies/<int:role_id>', methods=['GET'])
def get_role_competencies(role_id):
    role = Role.query.get(role_id)
    if not role:
        return jsonify({'competencies': []})

    # Récupérer les activités liées via activity_roles
    # Utilise distinct pour éviter les doublons si une même compétence est liée via plusieurs activités du même rôle
    activities = db.session.query(Activities).join(activity_roles).filter(activity_roles.c.role_id == role_id).all()

    # Récupérer les compétences (compétencies seulement ici) associées à ces activités
    competencies_list = []
    seen_competency_ids = set() # Pour éviter les doublons de compétences
    for activity in activities:
        for competency in activity.competencies:
             if competency.id not in seen_competency_ids:
                competencies_list.append({
                    'id': competency.id,
                    'name': competency.description,
                    # 'connections_outgoing': [] # Vous pouvez ajouter les connexions ici si vous avez la relation dans le modèle Competency
                })
                seen_competency_ids.add(competency.id)


    return jsonify({'competencies': competencies_list})

# --- Route pour récupérer Savoirs, SavoirFaire, et HSC d’un rôle ---
@competences_bp.route('/get_role_knowledge/<int:role_id>', methods=['GET'])
def get_role_knowledge(role_id):
    # Assurez-vous que les modèles Savoir, SavoirFaire, Softskill sont importés
    from Code.models.models import activity_roles, Savoir, SavoirFaire, Softskill # Importez Softskill

    role = Role.query.get(role_id)
    if not role:
         return jsonify({
            'savoirs': [],
            'savoir_faires': [],
            'softskills': [] # Changez 'aptitudes' en 'softskills'
        })

    # Récupérer les activités liées via activity_roles
    activities = db.session.query(Activities).join(activity_roles).filter(activity_roles.c.role_id == role_id).all()

    result = {
        'savoirs': [],
        'savoir_faires': [],
        'softskills': [] # Changez 'aptitudes' en 'softskills'
    }

    # Changez les clés dans seen_ids
    seen_ids = { 'savoirs': set(), 'savoir_faires': set(), 'softskills': set() } # Changez 'aptitudes' en 'softskills'

    for activity in activities:
        for savoir in activity.savoirs:
            if savoir.id not in seen_ids['savoirs']:
                result['savoirs'].append({'id': savoir.id, 'description': savoir.description})
                seen_ids['savoirs'].add(savoir.id)
        for savoir_faire in activity.savoir_faires:
             if savoir_faire.id not in seen_ids['savoir_faires']:
                result['savoir_faires'].append({'id': savoir_faire.id, 'description': savoir_faire.description})
                seen_ids['savoir_faires'].add(savoir_faire.id)
        # Modifiez pour récupérer les softskills au lieu des aptitudes
        for softskill in activity.softskills: # Changez activity.aptitudes en activity.softskills
             if softskill.id not in seen_ids['softskills']: # Changez 'aptitudes' en 'softskills'
                # CORRECTION ICI: Remplacez softskill.description par softskill.name
                result['softskills'].append({'id': softskill.id, 'description': softskill.habilete,'niveau': softskill.niveau})
                seen_ids['softskills'].add(softskill.id) # Changez 'aptitudes' en 'softskills'


    return jsonify(result)


# --- Route pour récupérer les connexions d’une compétence ---
# Vous devrez implémenter cette logique si vous avez un modèle ou une table pour les connexions de compétences.
# Actuellement, elle semble simulée ou manquante dans votre modèle Competency.
@competences_bp.route('/get_competency_connections/<int:competency_id>', methods=['GET'])
def get_competency_connections(competency_id):
    competency = Competency.query.get(competency_id)
    if not competency:
        return jsonify({'connections': []})

    # --- TODO: Implémenter la logique pour récupérer les connexions réelles ---
    # Cela dépend de la façon dont vos connexions sont modélisées.
    # Si une compétence est liée à des activités, puis les activités sont liées à d'autres choses via des Links,
    # vous devrez traverser ces relations.
    # Exemple (hypothétique, dépend de votre modèle Link et des relations):
    # connections_list = []
    # for activity in competency.activities: # Si Competency a une relation backref vers Activity
    #     for link in activity.outgoing_links: # Si Activity a une relation vers Link
    #          target_name = "Unknown"
    #          if link.target_activity:
    #              target_name = link.target_activity.name
    #          elif link.target_data:
    #              target_name = link.target_data.name
    #          connections_list.append({'id': link.id, 'name': target_name})

    # Pour l'instant, retourne juste une liste vide ou simulée si la logique n'est pas implémentée
    print(f"Warning: get_competency_connections route called for competency {competency_id}, but connection logic is not fully implemented.")
    connections_list = [] # Remplacez par votre logique réelle si elle existe
    # Exemple de données simulées:
    # if competency_id == 1: connections_list = [{'id': 101, 'name': 'Tâche X'}, {'id': 102, 'name': 'Donnée Y'}]

    result = [{'id': c.id, 'name': c.get('name', 'Élément lié')} for c in connections_list] # Utilise .get pour la sécurité
    return jsonify({'connections': result})


# --- Route pour enregistrer les évaluations ---
# Cette route est déjà bien conçue pour gérer les différents types d'évaluations.
@competences_bp.route('/save_user_evaluations', methods=['POST'])
def save_user_evaluations():
    data = request.get_json()
    user_id = data.get('userId')
    role_id = data.get('roleId')
    evaluations = data.get('evaluations', [])

    if not user_id or not role_id:
        return jsonify({'success': False, 'message': 'User ID and Role ID are required'}), 400

    # Vérifier si l'utilisateur et le rôle existent
    user = User.query.get(user_id)
    role = Role.query.get(role_id)
    if not user or not role:
         return jsonify({'success': False, 'message': 'Utilisateur ou Rôle non trouvé'}), 404


    for eval_item in evaluations:
        item_id = eval_item.get('item_id')
        item_type = eval_item.get('item_type')
        eval_number = eval_item.get('eval_number') # Peut être un entier (1,2,3) ou une chaîne ('collaborator', 'manager', 'rh')
        note = eval_item.get('note')

        # Valider les données de chaque évaluation
        if item_id is None or item_type is None or eval_number is None or note is None or note not in ['red', 'orange', 'green']:
             print(f"Skipping invalid evaluation data: {eval_item}")
             continue # Ignore les évaluations invalides

        # Convertir eval_number en entier si c'est une chaîne numérique, sinon garder la chaîne
        try:
             eval_number = int(eval_number)
        except (ValueError, TypeError):
             # eval_number reste une chaîne ('collaborator', 'manager', 'rh')
             pass


        # 1. On cherche si une évaluation existe déjà
        evaluation = CompetencyEvaluation.query.filter_by(
            user_id=user_id,
            role_id=role_id,
            item_id=item_id,
            item_type=item_type,
            eval_number=eval_number # Utilise la valeur potentiellement convertie
        ).first()

        if evaluation:
            # 2. Si une évaluation existe, on met à jour sa note.
            evaluation.note = note
        else:
            # 3. Si aucune évaluation n'existe, on en crée une nouvelle.
            evaluation = CompetencyEvaluation(
                user_id=user_id,
                role_id=role_id,
                item_id=item_id,
                item_type=item_type,
                eval_number=eval_number,
                note=note,
                created_at=datetime.utcnow().isoformat() 
            )
            db.session.add(evaluation)

    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Error saving evaluations: {e}")
        return jsonify({'success': False, 'message': 'Database error during save'}), 500


# --- Route pour récupérer les évaluations d'un user et d'un rôle ---
# Cette route est utilisée par le JS pour charger TOUTES les évaluations
# pour un utilisateur et un rôle donnés. Le JS filtre ensuite par item_type ('savoirs', etc. ou 'competencies')
# et eval_number ('1','2','3' ou 'collaborator','manager','rh').
@competences_bp.route('/get_user_evaluations/<int:user_id>/<int:role_id>')
def get_user_evaluations(user_id, role_id):
    try:
        # Vérifier si l'utilisateur et le rôle existent
        user = User.query.get(user_id)
        role = Role.query.get(role_id)
        if not user or not role:
             return jsonify([]) # Retourne une liste vide si l'utilisateur ou le rôle n'existe pas

        evaluations = CompetencyEvaluation.query.filter_by(user_id=user_id, role_id=role_id).all()
        # Assurez-vous que eval_number est renvoyé correctement (peut être int ou string)
        return jsonify([
            {
                'item_id': e.item_id,
                'item_type': e.item_type,
                'eval_number': str(e.eval_number),
                'note': e.note,
                'created_at': e.created_at
            } for e in evaluations
        ])
    except Exception as e:
        print(f"Error fetching user evaluations: {e}")
        return jsonify([])