# Code/routes/performance.py

from flask import Blueprint, jsonify, request
from sqlalchemy import or_
from Code.extensions import db
from Code.models.models import Performance, Link

performance_bp = Blueprint("performance", __name__, url_prefix="/performance")


# =====================================================
#  UTILITAIRE : construit le fragment HTML
# =====================================================
def _render_fragment(perf: Performance) -> str:
    """Construit un fragment HTML stylable et fonctionnel."""
    if not perf:
        return (
            "<div class='perf-general-fragment perf-box'>"
            "<em>Aucune performance générale définie pour cette activité.</em>"
            "</div>"
        )

    name = perf.name or ""
    desc = (perf.description or "").replace("\n", "<br>")

    html = f"""
    <div id="perf-display-{perf.id}" class="perf-container" data-linkid="{perf.link_id}">
        <div class='perf-general-fragment perf-box'>
            
            <div class='perf-general-title'>{name}</div>
            <div class='perf-general-desc'>{desc}</div>

            <div class='perf-actions' style="margin-top:8px;">
                <button class="perf-btn perf-btn-edit"
                        onclick="showEditPerfForm({perf.id}, `{name}`)">
                    <i class="fa-solid fa-pencil"></i>
                </button>
                <button class="perf-btn perf-btn-delete"
                        onclick="deletePerformance({perf.id})">
                    <i class="fa-solid fa-trash"></i>
                </button>
            </div>

            <!-- Formulaire édition -->
            <div id="perf-edit-form-{perf.id}" class="perf-edit-form" style="display:none;">
                <input id="perf-edit-input-{perf.id}" type="text" value="{name}" />
                <button onclick="submitEditPerf({perf.id})">Enregistrer</button>
                <button onclick="hideEditPerfForm({perf.id})">Annuler</button>
            </div>
        </div>
    </div>
    """

    return html




# =====================================================
#  RENDU HTML
# =====================================================
@performance_bp.route("/render/<int:link_id>", methods=["GET"])
def render_by_link(link_id):
    """Retourne la performance associée à un link_id."""
    perf = Performance.query.filter_by(link_id=link_id).first()
    return _render_fragment(perf)


@performance_bp.route("/render_activity/<int:activity_id>", methods=["GET"])
def render_by_activity(activity_id):
    """
    Fallback : trouve la Performance liée à une activité
    via Link.source_activity_id ou Link.target_activity_id.
    """
    link = (
        db.session.query(Link)
        .join(Performance, Performance.link_id == Link.id)
        .filter(
            or_(
                Link.source_activity_id == activity_id,
                Link.target_activity_id == activity_id,
            )
        )
        .first()
    )

    perf = getattr(link, "performance", None) if link else None
    return _render_fragment(perf)


# =====================================================
#  AJOUT : POST /performance/add
# =====================================================
@performance_bp.route("/add", methods=["POST"])
def add_performance():
    data = request.get_json() or {}

    link_id = data.get("link_id")
    name = (data.get("name") or "").strip()
    desc = (data.get("description") or "").strip()

    if not link_id or not name:
        return jsonify({"error": "link_id et name sont obligatoires"}), 400

    perf = Performance(link_id=link_id, name=name, description=desc)
    db.session.add(perf)
    db.session.commit()

    return jsonify({"message": "Performance créée", "id": perf.id}), 200


# =====================================================
#  MODIFICATION : PUT /performance/<id>
# =====================================================
@performance_bp.route("/<int:perf_id>", methods=["PUT"])
def update_performance(perf_id):
    perf = Performance.query.get(perf_id)
    if not perf:
        return jsonify({"error": "Performance introuvable"}), 404

    data = request.get_json() or {}

    name = data.get("name")
    desc = data.get("description")

    if name is not None:
        perf.name = name.strip()
    if desc is not None:
        perf.description = desc.strip()

    db.session.commit()

    return jsonify({"message": "Performance mise à jour"}), 200


# =====================================================
#  SUPPRESSION : DELETE /performance/<id>
# =====================================================
@performance_bp.route("/<int:perf_id>", methods=["DELETE"])
def delete_performance(perf_id):
    perf = Performance.query.get(perf_id)
    if not perf:
        return jsonify({"error": "Performance introuvable"}), 404

    db.session.delete(perf)
    db.session.commit()

    return jsonify({"message": "Performance supprimée"}), 200