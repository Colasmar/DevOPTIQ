from flask import Blueprint, render_template
from models.models import Activity

ui_bp = Blueprint('ui', __name__, url_prefix='/ui')

@ui_bp.route('/activities', methods=['GET'])
def activities():
    # Récupérer toutes les activités depuis la base de données
    activities = Activity.query.all()
    return render_template('ui/activities.html', activities=activities)
