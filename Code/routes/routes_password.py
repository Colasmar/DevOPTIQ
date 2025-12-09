from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_mail import Message
from werkzeug.security import generate_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import current_app
from Code.models.models import User
from Code.extensions import mail, db

auth_password_bp = Blueprint('auth_password', __name__)

# Route pour demander une réinitialisation de mot de passe
@auth_password_bp.route('/forgot_password', methods=['POST'])
def forgot_password():
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()

    if not user:
        flash('Aucun compte n’est lié à cette adresse email.', 'error')
        return redirect(url_for('auth.login'))

    # Générer un token sécurisé
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    token = serializer.dumps(email, salt='password-reset-salt')

    reset_link = url_for('auth_password.reset_password', token=token, _external=True)

    # Envoyer l'email
    msg = Message("Réinitialisation du mot de passe",
                  recipients=[email])
    msg.body = f"Bonjour,\n\nCliquez sur ce lien pour réinitialiser votre mot de passe :\n{reset_link}\n\nCe lien est valable 1 heure."
    # Forcer l'encodage en UTF-8
    msg.charset = 'utf-8'

    mail.send(msg)

    flash('Un email de réinitialisation a été envoyé si l’adresse est correcte.', 'success')
    return redirect(url_for('auth.login'))

# Route pour réinitialiser le mot de passe via le lien
@auth_password_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except SignatureExpired:
        flash('Le lien a expiré.', 'error')
        return redirect(url_for('auth.login'))
    except BadSignature:
        flash('Lien invalide.', 'error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        new_password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            flash('Mot de passe réinitialisé avec succès.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Utilisateur introuvable.', 'error')
            return redirect(url_for('auth.login'))

    return render_template('reset_password.html')