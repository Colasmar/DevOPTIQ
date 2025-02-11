from flask import Blueprint, render_template
from Code.models.models import Activities

ui_bp = Blueprint('ui', __name__, url_prefix='/ui')

@ui_bp.route('/activities', methods=['GET'])
def activities():
    # Récupérer toutes les activités depuis la base de données
    activities = Activities.query.all()
    return render_template('ui/activities.html', activities=activities)
