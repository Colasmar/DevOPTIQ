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

@auth_bp.route('/logout')
def logout():
    session.pop('user_email', None)
    flash('Déconnexion réussie.', 'success')
    return redirect(url_for('auth.login'))


