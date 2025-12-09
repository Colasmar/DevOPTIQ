from flask import jsonify
from .activities_bp import activities_bp
from Code.models.models import Performance

@activities_bp.route("/performance/render/<int:link_id>", methods=["GET"])
def render_performance(link_id):
    """
    Retourne la/les Performance associée(s) à link_id, en JSON,
    si besoin pour recharger partiellement la page.
    """
    performances = Performance.query.filter_by(link_id=link_id).all()
    results = []
    for p in performances:
        results.append({
            "id": p.id,
            "name": p.name,
            "description": p.description
        })
    return jsonify(results), 200
