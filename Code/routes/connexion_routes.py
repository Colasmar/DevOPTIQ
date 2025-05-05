from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from Code.models.models import User, Role, UserRole  # Ajout de UserRole
from Code.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Vérifier si l'utilisateur existe dans la base de données
        user = User.query.filter_by(email=email).first()
        if user is None:
            flash('Compte introuvable.', 'error')
            return redirect(url_for('auth.login'))

        # Vérifier si le mot de passe correspond
        if not check_password_hash(user.password, password):
            flash('Mot de passe incorrect.', 'error')
            return redirect(url_for('auth.login'))

        # Stocker l'email dans la session si la connexion est réussie
        session['user_email'] = email  
        return redirect(url_for('activities.view_activities'))  # Endpoint à adapter si nécessaire

    return render_template('connexion.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Récupérer les données du formulaire
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        age = request.form.get('age')
        email = request.form.get('email')
        password = request.form.get('password')  # Mot de passe en clair
        role_name = request.form.get('role')  # Récupérer le nom du rôle sélectionné

        # Hachage du mot de passe
        hashed_password = generate_password_hash(password)

        # Créer un nouvel utilisateur
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            age=age,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.flush()  # Ne pas commit encore

        # Récupérer le rôle correspondant via le nom
        role = Role.query.filter_by(name=role_name).first()
        if role:
            # Ajouter l'entrée dans la table de liaison user_roles
            user_role = UserRole(user_id=new_user.id, role_id=role.id)
            db.session.add(user_role)
        else:
            # Si le rôle n'existe pas, vous pouvez gérer cette erreur
            flash('Rôle invalide.', 'error')
            db.session.rollback()
            return redirect(url_for('auth.register'))

        db.session.commit()
        print(f"Utilisateur enregistré : {new_user.first_name} {new_user.last_name} avec rôle {role_name}")

        flash('Inscription réussie, vous pouvez vous connecter.', 'success')
        return redirect(url_for('auth.login'))

    # Obtenir la liste des rôles pour le formulaire
    roles = Role.query.all()
    return render_template('enregistrer.html', roles=roles)

@auth_bp.route('/logout')
def logout():
    session.pop('user_email', None)
    flash('Déconnexion réussie.', 'success')
    return redirect(url_for('auth.login'))