from flask import Blueprint, render_template, request, jsonify
import requests
from Code.models.models import User, CompetencyEvaluation, Competency, Savoir, SavoirFaire, Softskill

projection_metier_bp = Blueprint('projection_metier', __name__, url_prefix='/projection_metier')

API_BASE_URL = "https://api.rome.beta.gouv.fr/metiers"

@projection_metier_bp.route('/')
def projection_page():
    users = User.query.order_by(User.last_name).all()
    return render_template('projection_metier.html', users=users)

@projection_metier_bp.route('/analyze_user/<int:user_id>', methods=['GET'])
def analyze_user(user_id):
    user = User.query.get_or_404(user_id)

    # Récupérer les compétences évaluées vertes ou oranges
    evals = CompetencyEvaluation.query.filter_by(user_id=user_id).filter(CompetencyEvaluation.note.in_(['green', 'orange'])).all()
    user_comp_desc = set()

    for e in evals:
        if e.item_type == 'competencies':
            comp = Competency.query.get(e.item_id)
        elif e.item_type == 'savoirs':
            comp = Savoir.query.get(e.item_id)
        elif e.item_type == 'savoir_faires':
            comp = SavoirFaire.query.get(e.item_id)
        elif e.item_type == 'softskills':
            comp = Softskill.query.get(e.item_id)
        else:
            comp = None
        if comp and hasattr(comp, 'description'):
            user_comp_desc.add(comp.description.strip().lower())

    headers = {"Accept": "application/json"}
    params = {"query": "", "limit": 20}
    response = requests.get(API_BASE_URL, headers=headers, params=params)
    metiers = response.json().get("results", []) if response.ok else []

    results = []
    for m in metiers:
        code = m["code"]
        libelle = m["label"]
        try:
            comp_url = f"{API_BASE_URL}/{code}/competences"
            comp_resp = requests.get(comp_url, headers=headers).json()
            metier_comps = {c["libelle"].strip().lower() for c in comp_resp.get("competences", [])}

            match = user_comp_desc & metier_comps
            full_match = metier_comps.issubset(user_comp_desc)
            partial = len(match) > 0 and not full_match

            results.append({
                "code": code,
                "libelle": libelle,
                "match_count": len(match),
                "total_required": len(metier_comps),
                "full_match": full_match,
                "partial_match": partial,
                "missing": list(metier_comps - user_comp_desc)
            })
        except Exception:
            continue

    full = [r for r in results if r["full_match"]]
    partial = [r for r in results if r["partial_match"]]

    return jsonify({
        "full": full,
        "partial": partial
    })
