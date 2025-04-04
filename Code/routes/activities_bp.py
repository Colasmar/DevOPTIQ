from flask import Blueprint

# Blueprint principal pour /activities
activities_bp = Blueprint(
    'activities',
    __name__,
    url_prefix='/activities',
    template_folder='templates'
)
