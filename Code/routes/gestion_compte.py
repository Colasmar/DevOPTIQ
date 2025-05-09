from flask import Blueprint, render_template, request, redirect, url_for
from Code.extensions import db
from Code.models.models import User, Role, UserRole

gestion_compte_bp = Blueprint('gestion_compte', __name__, url_prefix='/comptes')

@gestion_compte_bp.route('/')
def list_users():
    roles = Role.query.all()
    role_users = {
        role.name: User.query.join(UserRole).filter(UserRole.role_id == role.id).all()
        for role in roles
    }
    return render_template('gestion_compte.html', role_users=role_users, roles=roles)

@gestion_compte_bp.route('/create', methods=['POST'])
def create_user():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    age = request.form.get('age')
    email = request.form['email']
    password = request.form['password']  
    role_id = int(request.form['role_id'])
    status = request.form['status']

    user = User(first_name=first_name, last_name=last_name, age=age, email=email, password=password, status=status)
    db.session.add(user)
    db.session.commit()

    user_role = UserRole(user_id=user.id, role_id=role_id)
    db.session.add(user_role)
    db.session.commit()
    
    return redirect(url_for('gestion_compte.list_users'))

@gestion_compte_bp.route('/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    User.query.filter_by(id=user_id).delete()
    db.session.commit()
    return redirect(url_for('gestion_compte.list_users'))



@gestion_compte_bp.route('/update/<int:user_id>', methods=['GET', 'POST'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    roles = Role.query.all()

    if request.method == 'POST':
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.age = request.form.get('age')
        user.email = request.form['email']
        user.status = request.form['status']

        # Mise à jour du rôle
        new_role_id = int(request.form['role_id'])
        user_role = UserRole.query.filter_by(user_id=user.id).first()
        if user_role:
            user_role.role_id = new_role_id
        else:
            db.session.add(UserRole(user_id=user.id, role_id=new_role_id))

        db.session.commit()
        return redirect(url_for('gestion_compte.list_users'))

    current_role = UserRole.query.filter_by(user_id=user.id).first()
    return render_template('edit_user.html', user=user, roles=roles, current_role=current_role)
