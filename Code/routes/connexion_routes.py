from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from Code.models.models import Role

auth_bp = Blueprint('auth', __name__)

# Simuler une base de données pour les utilisateurs en mémoire
user_storage = {}

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Vérifier si l'utilisateur existe
        if email not in user_storage:
            flash('Compte introuvable.', 'error')  # Message d'erreur
            return redirect(url_for('auth.login'))

        # Vérifier si le mot de passe correspond
        if user_storage[email]['password'] != password:
            flash('Mot de passe incorrect.', 'error')  # Message d'erreur
            return redirect(url_for('auth.login'))

        # Stocker l'email dans la session si la connexion est réussie
        session['user_email'] = email  
        return redirect(url_for('activities.view_activities'))  # Utilisez le bon nom d'endpoint

    return render_template('connexion.html')  # Changement ici

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Récupérer les données du formulaire
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        age = request.form.get('age')
        email = request.form.get('email')
        password = request.form.get('password')  # Ajout du mot de passe
        role_id = request.form.get('role')

        # Simuler la création d'un utilisateur
        user_storage[email] = {
            'first_name': first_name,
            'last_name': last_name,
            'age': age,
            'role_id': role_id,
            'password': password  # Stocker le mot de passe
        }
        # Redirection vers la page de connexion après l'inscription
        flash('Inscription réussie, vous pouvez vous connecter.', 'success')
        return redirect(url_for('auth.login'))

    roles = Role.query.all()  # Remplir la liste des rôles depuis la base de données
    return render_template('enregistrer.html', roles=roles)  # Changement ici

@auth_bp.route('/login', methods=['POST'])
def do_login():
    email = request.form['email']
    password = request.form['password']  # Simplification, pas de vérification de mot de passe

    if email in user_storage:  # Vérifier si l'utilisateur existe
        session['user_email'] = email  # Stocker l'email dans la session
        return redirect(url_for('activities.activities'))  # Redirection vers les activités après connexion

    return redirect(url_for('auth.login'))  # Retour à la page de connexion si échec