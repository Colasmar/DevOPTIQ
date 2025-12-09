from flask import Blueprint, render_template
from Code.models.models import Activities

ui_bp = Blueprint('ui', __name__, url_prefix='/ui')

@ui_bp.route('/activities', methods=['GET'])
def activities():
    # MODIFIÉ: Filtrer par entité active
    activities = Activities.for_active_entity().all()
    return render_template('ui/activities.html', activities=activities)
