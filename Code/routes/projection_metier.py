# -*- coding: utf-8 -*-
"""
Projection métiers via ROME 4.0 (France Travail) — produit 'rome-fiches-metiers'
- OAuth2 Client Credentials (token FT partenaire) avec essais robustes (Basic vs Body + variations de scope)
- Appel direct de l’endpoint : GET /v1/fiches-rome/fiche-metier
- Matching compétences: normalisation + fuzzy (difflib + Jaccard) optimisé par filtrage token
- Pagination côté serveur : offset/limit pour 'full' (maîtrisables) et 'partial' (envisageables)
"""

import base64
import logging
import os
import re
import time
import unicodedata
import difflib
from typing import Any, Dict, List, Optional, Tuple

import requests
from flask import Blueprint, render_template, jsonify, request

# ⚠️ Import via 'Code.' pour éviter les doubles imports SQLAlchemy
from Code.models.models import (
    User, CompetencyEvaluation, Competency, Savoir, SavoirFaire, Softskill
)

projection_metier_bp = Blueprint("projection_metier", __name__, url_prefix="/projection_metier")

# ------------------------------
# Config + helpers
# ------------------------------
def _env(name: str, default: str = "") -> str:
    v = os.getenv(name)
    return v.strip() if isinstance(v, str) else default

# Base URL PRODUIT
ROME_BASE_URL = _env("ROME_BASE_URL", "https://api.francetravail.io/partenaire/rome-fiches-metiers").rstrip("/")

# Endpoint "lister les fiches métier"
FICHES_LIST_PATH = "/v1/fiches-rome/fiche-metier"

# Token endpoint FT (partenaire)
ROME_TOKEN_URL     = _env("ROME_TOKEN_URL", "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire")

# Identifiants (recommandé: variables d’environnement)
ROME_CLIENT_ID     = _env("ROME_CLIENT_ID", "PAR_afdeccompetencies_dbe5f0b1a9e88e793bae776171bb20e78d9f5f67691ce3fee4d31d439580a522")
ROME_CLIENT_SECRET = _env("ROME_CLIENT_SECRET", "8d1d87ed9ce5349f3ea27fc5b54cda91a97f102d1445c6441ca6db19f01e13f5")

# Scope explicite (si la fiche produit l’exige)
ROME_SCOPE         = _env("ROME_SCOPE", "")

try:
    ROME_TIMEOUT = float(_env("ROME_TIMEOUT", "10"))
except Exception:
    ROME_TIMEOUT = 10.0

LOG_LEVEL = getattr(logging, _env("PROJECTION_METIER_LOG_LEVEL", "INFO").upper(), logging.INFO)
logger = logging.getLogger("projection_metier")
logger.setLevel(LOG_LEVEL)
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s - %(name)s: %(message)s"))
    h.setLevel(LOG_LEVEL)
    logger.addHandler(h)

def _mask(s: Optional[str]) -> str:
    if not s:
        return ""
    return (s[:6] + "…") if len(s) > 6 else "***"

# ------------------------------
# OAuth2: essais multiples + debug (silencieux côté front)
# ------------------------------
_token_cache = {"access_token": None, "expires_at": 0.0}
_last_oauth_debug: Dict[str, Any] = {}

def _token_request(credential_mode: str, scope: Optional[str]):
    data = {"grant_type": "client_credentials"}
    if scope:
        data["scope"] = scope
    headers = {"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}

    if credential_mode == "basic":
        raw = f"{ROME_CLIENT_ID}:{ROME_CLIENT_SECRET}".encode("utf-8")
        headers["Authorization"] = "Basic " + base64.b64encode(raw).decode("ascii")
    else:
        data["client_id"] = ROME_CLIENT_ID
        data["client_secret"] = ROME_CLIENT_SECRET

    dbg: Dict[str, Any] = {"mode": credential_mode, "scope": scope}
    try:
        resp = requests.post(ROME_TOKEN_URL, data=data, headers=headers, timeout=ROME_TIMEOUT)
        dbg["http_status"] = resp.status_code
        try:
            body = resp.json()
        except Exception:
            body = {"_text": (resp.text or "")[:800]}

        body_preview = {}
        if isinstance(body, dict):
            for k, v in body.items():
                if k in ("access_token", "refresh_token"):
                    body_preview[k] = "<masked>"
                else:
                    body_preview[k] = v
        dbg["body_preview"] = body_preview

        if 200 <= resp.status_code < 300:
            token = body.get("access_token") if isinstance(body, dict) else None
            expires_in = float(body.get("expires_in") or 1800) if isinstance(body, dict) else 1800.0
            if not token:
                dbg["error"] = "NO_ACCESS_TOKEN_IN_RESPONSE"
                return False, dbg
            dbg["ok"] = True
            dbg["expires_in"] = int(expires_in)
            dbg["access_token_masked"] = "<masked>"
            return True, {"token": token, "expires_in": expires_in, "debug": dbg}
        else:
            dbg["error"] = body.get("error") if isinstance(body, dict) else "HTTP_ERROR"
            dbg["error_description"] = body.get("error_description") if isinstance(body, dict) else None
            return False, dbg
    except requests.RequestException as e:
        dbg["exception"] = str(e)
        return False, dbg

def get_access_token(force: bool = False) -> str:
    global _last_oauth_debug
    now = time.time()
    if not force and _token_cache["access_token"] and _token_cache["expires_at"] - 60 > now:
        return _token_cache["access_token"]

    cid = ROME_CLIENT_ID
    scopes_to_try: List[Optional[str]] = []
    if ROME_SCOPE:
        scopes_to_try.append(ROME_SCOPE)
    scopes_to_try.extend([
        None, f"application_{cid}",
        f"application_{cid} api_rome-fiches-metiersv1",
        f"application_{cid} nomenclatureRome",
        f"application_{cid} api_rome-fiches-metiersv1 nomenclatureRome",
        "api_rome-fiches-metiersv1", "nomenclatureRome",
        "api_rome-fiches-metiers", "api_rome_fiches_metiers",
    ])
    seen = set()
    scopes_to_try = [s for s in scopes_to_try if (s not in seen) and (seen.add(s) or True)]

    attempts: List[Dict[str, Any]] = []
    for mode in ("body", "basic"):
        for scope in scopes_to_try:
            logger.info("OAuth2: POST token (mode=%s, scope=%s, client_id=%s)", mode, scope or "(none)", _mask(ROME_CLIENT_ID))
            ok, result = _token_request(mode, scope)
            attempts.append(result if isinstance(result, dict) else {"result": str(result)})
            if ok:
                token = result["token"]
                expires_in = result.get("expires_in", 1800.0)
                _token_cache["access_token"] = token
                _token_cache["expires_at"] = now + float(expires_in)
                _last_oauth_debug = {"success": result.get("debug", {}), "attempts": attempts}
                logger.info("OAuth2: token obtenu (~%ss)", int(expires_in))
                return token
    _last_oauth_debug = {"success": None, "attempts": attempts}
    raise RuntimeError("OAuth2 échoué (400/401/403).")

def _auth_headers() -> Dict[str, str]:
    return {
        "Accept": "application/json",
        "Authorization": f"Bearer {get_access_token()}",
        "X-Client-Id": ROME_CLIENT_ID,
    }

# ------------------------------
# Normalisation & matching
# ------------------------------
_STOPWORDS_FR = {
    "de","des","du","la","le","les","un","une","et","d","l","au","aux","en","dans","sur","pour","par","à","a","avec","ou","se","s","que","qui","qu","ne","pas"
}

def _normalize_text(s: str) -> str:
    if not s:
        return ""
    s = s.lower().strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[’'‐–—\-_/]", " ", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _tokenize(s: str) -> List[str]:
    s = _normalize_text(s)
    if not s: return []
    return [t for t in s.split(" ") if t and t not in _STOPWORDS_FR]

def _jaccard(a: List[str], b: List[str]) -> float:
    if not a or not b:
        return 0.0
    sa, sb = set(a), set(b)
    inter = len(sa & sb)
    uni = len(sa | sb)
    return inter / uni if uni else 0.0

def _similarity(a: str, b: str) -> Tuple[float, float]:
    na, nb = _normalize_text(a), _normalize_text(b)
    ratio = difflib.SequenceMatcher(None, na, nb).ratio()
    jac = _jaccard(_tokenize(na), _tokenize(nb))
    return ratio, jac

RATIO_THR = 0.82
JACCARD_THR = 0.60

# ------------------------------
# Extraction des compétences & scoring
# ------------------------------
def _user_comp_labels(user_id: int) -> List[str]:
    """Libellés des éléments notés green/orange (competencies/savoirs/savoir_faires/softskills)."""
    keep = {"green", "orange"}
    labels: List[str] = []
    q = (CompetencyEvaluation.query
         .filter_by(user_id=user_id)
         .filter(CompetencyEvaluation.note.in_(keep)))
    for e in q.all():
        label = None
        if e.item_type == "competencies":
            obj = Competency.query.get(e.item_id); label = getattr(obj, "description", None)
        elif e.item_type == "savoirs":
            obj = Savoir.query.get(e.item_id); label = getattr(obj, "description", None)
        elif e.item_type == "savoir_faires":
            obj = SavoirFaire.query.get(e.item_id); label = getattr(obj, "description", None)
        elif e.item_type == "softskills":
            obj = Softskill.query.get(e.item_id); label = getattr(obj, "habilete", None)
        if label:
            labels.append(label.strip())
    return labels

def _extract_list_from_payload(payload: Any) -> List[dict]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("fiches", "fichesMetiers", "results", "data", "items", "content"):
            v = payload.get(key)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
    return []

def _extract_label_from_fiche(f: dict) -> str:
    metier = f.get("metier") or {}
    return (metier.get("libelle") or "").strip()

def _extract_code_from_fiche(f: dict) -> str:
    code = (f.get("code") or "").strip()
    if not code and isinstance(f.get("metier"), dict):
        code = (f["metier"].get("code") or "").strip()
    return code

def _extract_competences_from_fiche(f: dict) -> List[str]:
    comps: List[str] = []
    groups = f.get("groupesCompetencesMobilisees") or f.get("groupescompetencesmobilisees") or []
    if isinstance(groups, list):
        for g in groups:
            arr = g.get("competences") if isinstance(g, dict) else None
            if isinstance(arr, list):
                for c in arr:
                    if isinstance(c, dict):
                        lib = (c.get("libelle") or c.get("label") or "").strip()
                        if lib:
                            comps.append(lib)
    return comps

# ------------------------------
# Appel endpoint "Lister les fiches métier"
# ------------------------------
def list_fiches(headers: dict):
    url = f"{ROME_BASE_URL}{FICHES_LIST_PATH}"
    champs_full = "code,metier(libelle,code),groupescompetencesmobilisees(competences(libelle,code))"
    params = {"champs": champs_full}
    r = requests.get(url, headers=headers, params=params, timeout=ROME_TIMEOUT)
    if r.status_code in (401, 403):
        return "", [], {"auth_error": True, "status": r.status_code}
    if r.status_code == 404:
        return "", [], {"not_found": True, "status": 404}
    payload = r.json() if 200 <= r.status_code < 300 else []
    return url, _extract_list_from_payload(payload), {"status": r.status_code}

# ------------------------------
# Routes
# ------------------------------
@projection_metier_bp.route("/", methods=["GET"])
def index():
    users = User.query.order_by(User.last_name, User.first_name).all()
    return render_template("projection_metier.html", users=users)

@projection_metier_bp.route("/analyze_user/<int:user_id>", methods=["GET"])
def analyze_user(user_id: int):
    if user_id <= 0:
        return jsonify({"error": "INVALID_USER_ID", "message": "Sélectionne d'abord un collaborateur."}), 400

    _ = User.query.get_or_404(user_id)

    # Pagination demandée
    def _arg_int(name: str, default: int, min_v: int, max_v: int) -> int:
        try:
            v = int(request.args.get(name, default))
        except Exception:
            v = default
        v = max(min_v, min(v, max_v))
        return v

    full_offset   = _arg_int("full_offset",    0, 0, 10_000)
    full_limit    = _arg_int("full_limit",    30, 0, 200)
    partial_offset= _arg_int("partial_offset", 0, 0, 10_000)
    partial_limit = _arg_int("partial_limit", 30, 0, 200)

    # OAuth2
    try:
        headers = _auth_headers()
    except RuntimeError as e:
        return jsonify({"full": [], "partial": [], "info": {"warning": "OAUTH_ERROR", "message": str(e)}}), 200

    # Endpoint
    url_used, fiches, debug_ep = list_fiches(headers)
    if debug_ep.get("auth_error"):
        return jsonify({"full": [], "partial": [], "info": {"warning": "ROME_API_UNAUTHORIZED"}}), 200
    if debug_ep.get("not_found"):
        return jsonify({"full": [], "partial": [], "info": {"warning": "ROME_API_NOT_FOUND"}}), 200

    # --- Matching optimisé ---
    user_raw_labels = _user_comp_labels(user_id)
    # Prépare structures normalisées/tokens
    user_items = []
    user_token_union = set()
    for raw in user_raw_labels:
        n = _normalize_text(raw)
        toks = set(_tokenize(raw))
        if n:
            user_items.append({"raw": raw, "norm": n, "tokens": toks})
            user_token_union |= toks

    full: List[Dict[str, Any]] = []
    partial: List[Dict[str, Any]] = []

    for f in fiches:
        code = _extract_code_from_fiche(f)
        label = _extract_label_from_fiche(f)
        rome_comps = _extract_competences_from_fiche(f)

        if not rome_comps:
            # Pas d'infos → fiche listée à 0% côté "envisageables"
            partial.append({"code": code, "label": label, "score": 0, "owned": [], "missing": []})
            continue

        owned_pairs: List[Tuple[str, str]] = []
        missing: List[str] = []

        for rc in rome_comps:
            rc_tokens = set(_tokenize(rc))
            # Filtre rapide : si aucun token en commun, on évite difflib (très coûteux)
            if not (rc_tokens & user_token_union):
                missing.append(rc)
                continue

            best_match = None
            best_ratio = 0.0
            best_jacc  = 0.0

            # On ne compare qu'aux libellés qui partagent au moins un token
            for u in user_items:
                if not (rc_tokens & u["tokens"]):
                    continue
                ratio, jac = _similarity(rc, u["raw"])
                if ratio > best_ratio or (abs(ratio - best_ratio) < 1e-6 and jac > best_jacc):
                    best_ratio, best_jacc = ratio, jac
                    best_match = u["raw"]

            if (best_ratio >= RATIO_THR) or (best_jacc >= JACCARD_THR):
                owned_pairs.append((rc, best_match or ""))
            else:
                missing.append(rc)

        total = len(rome_comps)
        owned_count = len(owned_pairs)
        score = round((owned_count / total) * 100, 1) if total else 0.0

        item = {
            "code": code,
            "label": label,
            "score": score,
            "owned": [p[0] for p in owned_pairs],     # compétences ROME couvertes
            "missing": missing,                       # compétences ROME à développer
            "owned_count": owned_count,
            "missing_count": len(missing),
            "total": total
        }

        if total > 0 and owned_count == total:
            full.append(item)      # 100%
        else:
            partial.append(item)   # 0–99%

    # Tri par score décroissant
    full.sort(key=lambda x: (-x["score"], x["label"]))
    partial.sort(key=lambda x: (-x["score"], x["label"]))

    # Pagination serveur
    full_slice   = full[full_offset: full_offset + full_limit]   if full_limit   > 0 else []
    partial_slice= partial[partial_offset: partial_offset + partial_limit] if partial_limit > 0 else []

    return jsonify({
        "full": full_slice,
        "partial": partial_slice,
        "page": {
            "full": {
                "offset": full_offset, "limit": full_limit, "returned": len(full_slice),
                "total": len(full), "has_more": (full_offset + len(full_slice)) < len(full)
            },
            "partial": {
                "offset": partial_offset, "limit": partial_limit, "returned": len(partial_slice),
                "total": len(partial), "has_more": (partial_offset + len(partial_slice)) < len(partial)
            }
        },
        "info": {"used_endpoint": url_used}
    }), 200
