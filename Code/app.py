import os
from flask import Flask, render_template
from extensions import db
from routes.ui_routes import ui_bp
from models.models import Activity
from routes.activities import activities_bp
from sqlalchemy import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'instance', 'optiq.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
app.register_blueprint(activities_bp)
app.register_blueprint(ui_bp)

@app.route('/')
def hello():
    return 'Hello, Flask!'

@app.route('/ui/activities', methods=['GET'])
def ui_activities():
    return render_template('ui/activities.html')

if __name__ == '__main__':
    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)

    with app.app_context():
        db.create_all()
        try:
            db.session.execute(text('SELECT 1'))
            print("Connexion à la base de données réussie.")
        except Exception as e:
            print(f"Erreur lors de la connexion à la base de données : {e}")

    app.run(debug=True)

