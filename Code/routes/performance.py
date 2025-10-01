# Code/routes/performance.py
from flask import Blueprint, jsonify
from sqlalchemy import or_
from Code.extensions import db
from Code.models.models import Performance, Link

performance_bp = Blueprint("performance", __name__, url_prefix="/performance")


def _render_fragment(perf: Performance) -> str:
    """Construit un petit fragment HTML stylable par CSS."""
    if not perf:
        return "<div class='perf-subtitle'>Performance générale</div>" \
               "<div class='perf-general-fragment perf-box'><em>Aucune performance générale définie pour cette activité.</em></div>"
    name = (perf.name or "Performance").strip()
    desc = (perf.description or "").strip().replace("\n", "<br>")
    return (
        "<div class='perf-subtitle'>Performance générale</div>"
        "<div class='perf-general-fragment perf-box'>"
        f"  <div class='perf-general-title'><strong>{name}</strong></div>"
        f"  <div class='perf-general-desc'>{desc}</div>"
        "</div>"
    )


@performance_bp.route("/render/<int:link_id>", methods=["GET"])
def render_by_link(link_id):
    """
    Rendu HTML d'une performance à partir d'un link_id direct.
    """
    perf = Performance.query.filter_by(link_id=link_id).first()
    return _render_fragment(perf)


@performance_bp.route("/render_activity/<int:activity_id>", methods=["GET"])
def render_by_activity(activity_id):
    """
    Fallback : trouve une Performance liée à l'activité via Link
    (source_activity_id OU target_activity_id) et renvoie un fragment HTML.
    """
    # On récupère un Link attaché à l'activité côté source OU côté target et qui dispose d'une performance
    link = (
        db.session.query(Link)
        .join(Performance, Performance.link_id == Link.id)
        .filter(
            or_(
                Link.source_activity_id == activity_id,
                Link.target_activity_id == activity_id
            )
        )
        .first()
    )
    perf = link.performance if link and getattr(link, "performance", None) else None
    return _render_fragment(perf)
