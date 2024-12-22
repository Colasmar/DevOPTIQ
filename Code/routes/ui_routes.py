from flask import Blueprint, render_template

ui_bp = Blueprint('ui', __name__, url_prefix='/ui')

@ui_bp.route('/activities', methods=['GET'])
def activities():
    return render_template('ui/activities.html')
