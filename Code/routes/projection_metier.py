# Code/routes/projection_metier.py
# -*- coding: utf-8 -*-

import base64
import logging
import os
import re
import time
import unicodedata
import difflib
from typing import List, Dict, Any, Optional

import requests
from flask import Blueprint, render_template, jsonify, request

from Code.models.models import (
    User,
    Role, UserRole,
    Activities, activity_roles,
    Competency,
    Savoir, SavoirFaire, Softskill, Aptitude,
)

projection_metier_bp = Blueprint(
    "projection_metier", __name__, url_prefix="/projection_metier"
)

# ============================================================
#  CONFIGURATION & LOGGING
# ============================================================

def _env(name: str, default: str = "") -> str:
    """RÃ©cupÃ¨re une variable d'environnement en nettoyant les espaces."""
    value = os.getenv(name)
    return value.strip() if isinstance(value, str) else default


# Variables d'environnement avec nettoyage automatique
ROME_BASE_URL = _env(
    "ROME_BASE_URL",
    "https://api.francetravail.io/partenaire/rome-fiches-metiers"
).rstrip("/").rstrip(".")  # âš ï¸ IMPORTANT : retire le point final !

ROME_TOKEN_URL = _env(
    "ROME_TOKEN_URL",
    "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire"
)

ROME_CLIENT_ID = _env("ROME_CLIENT_ID", "")
ROME_CLIENT_SECRET = _env("ROME_CLIENT_SECRET", "")
ROME_SCOPE = _env("ROME_SCOPE", "api_rome-fiches-metiersv1")  # âš ï¸ CRITIQUE : scope obligatoire
ROME_TIMEOUT = float(_env("ROME_TIMEOUT", "10"))

# Configuration du logger
logger = logging.getLogger("projection_metier")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s - %(name)s: %(message)s")
    )
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def _mask_secret(secret: str) -> str:
    """Masque un secret pour les logs."""
    if not secret:
        return "VIDE"
    if len(secret) <= 6:
        return "***"
    return secret[:6] + "â€¦"


# Log de la configuration au dÃ©marrage
logger.info("=" * 60)
logger.info("Configuration ROME 4.0")
logger.info("=" * 60)
logger.info("Client ID: %s", _mask_secret(ROME_CLIENT_ID))
logger.info("Client Secret: %s", _mask_secret(ROME_CLIENT_SECRET))
logger.info("Scope: %s", ROME_SCOPE)
logger.info("Base URL: %s", ROME_BASE_URL)
logger.info("Token URL: %s", ROME_TOKEN_URL)
logger.info("Timeout: %s secondes", ROME_TIMEOUT)
logger.info("=" * 60)


# ============================================================
#  GESTION DES TOKENS OAUTH2
# ============================================================

_token_cache: Dict[str, Any] = {
    "access_token": None,
    "expires_at": 0
}


def get_access_token() -> Optional[str]:
    """
    Obtient un token d'accÃ¨s OAuth2 pour l'API ROME.
    
    Returns:
        str: Le token d'accÃ¨s ou None en cas d'Ã©chec
    """
    now = time.time()
    
    # VÃ©rifier le cache
    if (_token_cache["access_token"] and 
        _token_cache["expires_at"] > now + 30):
        logger.debug("Token en cache valide")
        return _token_cache["access_token"]

    # VÃ©rifier les credentials
    if not ROME_CLIENT_ID or not ROME_CLIENT_SECRET:
        logger.error("âŒ ROME_CLIENT_ID ou ROME_CLIENT_SECRET manquant dans le .env")
        logger.error("   VÃ©rifiez que votre fichier .env contient ces variables")
        return None

    if not ROME_SCOPE:
        logger.error("âŒ ROME_SCOPE manquant dans le .env")
        logger.error("   Ajoutez : ROME_SCOPE=api_rome-fiches-metiersv1")
        return None

    logger.info("ðŸ”„ Demande d'un nouveau token OAuth2...")

    # PrÃ©paration des headers de base
    base_headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    # Liste des tentatives
    attempts = []

    # Tentative 1 : Authentification BASIC avec scope dans le body
    try:
        logger.info("ðŸ“¡ Tentative 1 : Mode BASIC + scope dans body")
        
        # Encodage Basic Auth
        credentials = f"{ROME_CLIENT_ID}:{ROME_CLIENT_SECRET}"
        encoded = base64.b64encode(credentials.encode("utf-8")).decode("ascii")
        
        headers = dict(base_headers)
        headers["Authorization"] = f"Basic {encoded}"
        
        data = {
            "grant_type": "client_credentials",
            "scope": ROME_SCOPE  # âš ï¸ CRITIQUE : inclure le scope !
        }
        
        logger.debug("Headers: %s", {k: v if k != "Authorization" else "Basic ***" for k, v in headers.items()})
        logger.debug("Data: %s", data)
        
        response = requests.post(
            ROME_TOKEN_URL,
            data=data,
            headers=headers,
            timeout=ROME_TIMEOUT,
        )
        
        logger.info("ðŸ“¥ RÃ©ponse : HTTP %s", response.status_code)
        
        try:
            json_response = response.json()
            logger.debug("Body: %s", json_response)
        except Exception:
            json_response = {"_raw_text": response.text[:300]}
            logger.debug("Body (non-JSON): %s", response.text[:300])
        
        attempts.append({
            "mode": "basic_with_scope",
            "status": response.status_code,
            "body": json_response,
        })
        
        # SuccÃ¨s ?
        if (response.status_code == 200 and 
            isinstance(json_response, dict) and 
            json_response.get("access_token")):
            
            token = json_response["access_token"]
            expires_in = float(json_response.get("expires_in", 3600))
            
            _token_cache["access_token"] = token
            _token_cache["expires_at"] = now + expires_in
            
            logger.info("âœ… Token obtenu avec succÃ¨s (valide ~%d secondes)", int(expires_in))
            logger.debug("Token: %s", _mask_secret(token))
            
            return token
        
        # Ã‰chec : analyser l'erreur
        if response.status_code == 400:
            error = json_response.get("error", "")
            error_desc = json_response.get("error_description", "")
            logger.warning("âš ï¸  Erreur 400 : %s - %s", error, error_desc)
            
            if "invalid_scope" in error:
                logger.error("âŒ Le scope '%s' n'est pas autorisÃ© pour votre application", ROME_SCOPE)
                logger.error("   VÃ©rifiez sur https://entreprise.francetravail.fr que votre app a accÃ¨s Ã  l'API ROME")
        
    except requests.exceptions.Timeout:
        logger.error("â±ï¸  Timeout lors de la demande de token")
        attempts.append({"mode": "basic_with_scope", "error": "timeout"})
    except Exception as e:
        logger.error("âŒ Exception lors de la demande de token : %s", e)
        attempts.append({"mode": "basic_with_scope", "error": str(e)})

    # Tentative 2 : Credentials dans le body (fallback)
    try:
        logger.info("ðŸ“¡ Tentative 2 : Mode BODY (credentials en POST)")
        
        headers = dict(base_headers)
        data = {
            "grant_type": "client_credentials",
            "client_id": ROME_CLIENT_ID,
            "client_secret": ROME_CLIENT_SECRET,
            "scope": ROME_SCOPE
        }
        
        response = requests.post(
            ROME_TOKEN_URL,
            data=data,
            headers=headers,
            timeout=ROME_TIMEOUT,
        )
        
        logger.info("ðŸ“¥ RÃ©ponse : HTTP %s", response.status_code)
        
        try:
            json_response = response.json()
        except Exception:
            json_response = {"_raw_text": response.text[:300]}
        
        attempts.append({
            "mode": "body_with_scope",
            "status": response.status_code,
            "body": json_response,
        })
        
        if (response.status_code == 200 and 
            isinstance(json_response, dict) and 
            json_response.get("access_token")):
            
            token = json_response["access_token"]
            expires_in = float(json_response.get("expires_in", 3600))
            
            _token_cache["access_token"] = token
            _token_cache["expires_at"] = now + expires_in
            
            logger.info("âœ… Token obtenu avec succÃ¨s (mode body, valide ~%d secondes)", int(expires_in))
            return token
    
    except Exception as e:
        logger.error("âŒ Exception tentative 2 : %s", e)
        attempts.append({"mode": "body_with_scope", "error": str(e)})

    # Toutes les tentatives ont Ã©chouÃ©
    logger.error("=" * 60)
    logger.error("âŒ Ã‰CHEC : Impossible d'obtenir un token ROME")
    logger.error("=" * 60)
    logger.error("DÃ©tail des tentatives :")
    for i, attempt in enumerate(attempts, 1):
        logger.error("  Tentative %d (%s) :", i, attempt.get("mode", "unknown"))
        if "error" in attempt:
            logger.error("    Erreur : %s", attempt["error"])
        elif "status" in attempt:
            logger.error("    HTTP %s", attempt["status"])
            if "body" in attempt:
                logger.error("    Body : %s", attempt["body"])
    logger.error("=" * 60)
    logger.error("ACTIONS Ã€ VÃ‰RIFIER :")
    logger.error("1. Votre fichier .env contient-il ROME_CLIENT_ID et ROME_CLIENT_SECRET ?")
    logger.error("2. Votre fichier .env contient-il ROME_SCOPE=api_rome-fiches-metiersv1 ?")
    logger.error("3. ROME_BASE_URL se termine-t-il par un point '.' ? (Ã  retirer)")
    logger.error("4. Votre app France Travail a-t-elle bien le scope activÃ© ?")
    logger.error("   â†’ VÃ©rifiez sur https://entreprise.francetravail.fr")
    logger.error("=" * 60)
    
    return None


def _get_auth_headers() -> Optional[Dict[str, str]]:
    """
    GÃ©nÃ¨re les headers d'authentification avec le token Bearer.
    
    Returns:
        dict: Headers avec Authorization ou None si pas de token
    """
    token = get_access_token()
    if not token:
        logger.warning("âš ï¸  Impossible de gÃ©nÃ©rer les headers : pas de token")
        return None
    
    return {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }


# ============================================================
#  NORMALISATION & MATCHING DE TEXTE
# ============================================================

_STOPWORDS = {
    "de", "des", "du", "la", "le", "les", "un", "une", "et", "d", "l",
    "au", "aux", "en", "dans", "sur", "pour", "par", "Ã ", "a", "avec",
    "ou", "se", "s", "que", "qui", "qu", "ne", "pas",
}


def _normalize(text: str) -> str:
    """Normalise un texte (minuscules, sans accents, sans ponctuation)."""
    if not text:
        return ""
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"['`\"\u2018\u2019\u201c\u201d_/\-]", " ", text)
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _tokenize(text: str) -> List[str]:
    """Tokenise un texte en retirant les stopwords."""
    normalized = _normalize(text)
    if not normalized:
        return []
    return [token for token in normalized.split(" ") 
            if token and token not in _STOPWORDS]


def _jaccard_similarity(tokens_a: set, tokens_b: set) -> float:
    """Calcule la similaritÃ© de Jaccard entre deux ensembles de tokens."""
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return intersection / union if union > 0 else 0.0


def _text_similarity(text_a: str, text_b: str) -> tuple[float, float]:
    """
    Calcule deux scores de similaritÃ© entre deux textes.
    
    Returns:
        tuple: (ratio_score, jaccard_score)
    """
    norm_a = _normalize(text_a)
    norm_b = _normalize(text_b)
    
    # Score de ratio (SequenceMatcher)
    ratio = difflib.SequenceMatcher(None, norm_a, norm_b).ratio()
    
    # Score de Jaccard
    tokens_a = set(_tokenize(text_a))
    tokens_b = set(_tokenize(text_b))
    jaccard = _jaccard_similarity(tokens_a, tokens_b)
    
    return ratio, jaccard


# Seuils de matching
RATIO_THRESHOLD = 0.82
JACCARD_THRESHOLD = 0.60


# ============================================================
#  EXTRACTION DES COMPÃ‰TENCES UTILISATEUR (OPTION A)
# ============================================================

def _extract_user_competencies(user_id: int) -> List[str]:
    """
    Extrait toutes les compÃ©tences d'un utilisateur depuis la base AFDEC.
    
    Inclut :
    - Les rÃ´les de l'utilisateur
    - Les activitÃ©s liÃ©es aux rÃ´les
    - Les compÃ©tences des activitÃ©s (Competency, Savoir, SavoirFaire, Softskill, Aptitude)
    
    Args:
        user_id: ID de l'utilisateur
        
    Returns:
        Liste de labels de compÃ©tences (nettoyÃ©s)
    """
    labels = []
    
    # RÃ©cupÃ©rer l'utilisateur
    user = User.query.get(user_id)
    if not user:
        logger.warning("âš ï¸  Utilisateur %d introuvable", user_id)
        return []
    
    logger.info("ðŸ“‹ Extraction des compÃ©tences pour %s %s (ID: %d)", 
                user.first_name, user.last_name, user_id)
    
    # 1. RÃ©cupÃ©rer les rÃ´les de l'utilisateur
    roles = (
        Role.query
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user_id)
        .all()
    )
    
    role_ids = [role.id for role in roles]
    logger.info("   â†’ %d rÃ´les trouvÃ©s", len(roles))
    
    # Ajouter les noms des rÃ´les
    for role in roles:
        if role.name:
            labels.append(role.name)
    
    # 2. RÃ©cupÃ©rer les activitÃ©s liÃ©es aux rÃ´les
    if not role_ids:
        logger.info("   â†’ Aucun rÃ´le, pas d'activitÃ©s Ã  extraire")
        return labels
    
    activities = (
        Activities.query
        .join(activity_roles, Activities.id == activity_roles.c.activity_id)
        .filter(activity_roles.c.role_id.in_(role_ids))
        .all()
    )
    
    logger.info("   â†’ %d activitÃ©s trouvÃ©es", len(activities))
    
    # 3. Extraire les compÃ©tences des activitÃ©s
    comp_count = 0
    for activity in activities:
        if activity.name:
            labels.append(activity.name)
        
        # Competency
        for comp in activity.competencies:
            if comp.description:
                labels.append(comp.description)
                comp_count += 1
        
        # Savoir
        for savoir in activity.savoirs:
            if savoir.description:
                labels.append(savoir.description)
                comp_count += 1
        
        # SavoirFaire
        for savoir_faire in activity.savoir_faires:
            if savoir_faire.description:
                labels.append(savoir_faire.description)
                comp_count += 1
        
        # Softskill
        for softskill in activity.softskills:
            if softskill.habilete:
                labels.append(softskill.habilete)
                comp_count += 1
        
        # Aptitude
        for aptitude in activity.aptitudes:
            if aptitude.description:
                labels.append(aptitude.description)
                comp_count += 1
    
    logger.info("   â†’ %d compÃ©tences extraites", comp_count)
    
    # Nettoyage final
    labels = [label.strip() for label in labels if label and label.strip()]
    logger.info("   â†’ Total : %d labels uniques", len(set(labels)))
    
    return labels


# ============================================================
#  APPELS API ROME 4.0
# ============================================================

def rome_search_jobs(query: str) -> List[Dict[str, Any]]:
    """
    Recherche des mÃ©tiers ROME par libellÃ©.
    
    Args:
        query: Terme de recherche
        
    Returns:
        Liste de mÃ©tiers trouvÃ©s
    """
    if not query or not query.strip():
        return []
    
    headers = _get_auth_headers()
    if not headers:
        logger.warning("âš ï¸  rome_search_jobs() : pas de token disponible")
        return []
    
    url = f"{ROME_BASE_URL}/v1/fiches-rome/metier/recherche"
    
    try:
        logger.debug("ðŸ” Recherche ROME : '%s'", query)
        
        response = requests.get(
            url,
            params={"libelle": query},
            headers=headers,
            timeout=ROME_TIMEOUT,
        )
        
        if response.status_code != 200:
            logger.warning("âš ï¸  rome_search_jobs('%s') â†’ HTTP %s", query, response.status_code)
            logger.debug("Body: %s", response.text[:200])
            return []
        
        data = response.json()
        
        if isinstance(data, list):
            logger.debug("   â†’ %d rÃ©sultats", len(data))
            return data
        
        if isinstance(data, dict):
            jobs = data.get("metiers", [])
            logger.debug("   â†’ %d rÃ©sultats", len(jobs))
            return jobs
        
        return []
    
    except requests.exceptions.Timeout:
        logger.error("â±ï¸  Timeout lors de la recherche ROME : '%s'", query)
        return []
    except Exception as e:
        logger.error("âŒ Exception rome_search_jobs('%s') : %s", query, e)
        return []


def rome_get_job_details(code: str) -> Dict[str, Any]:
    """
    RÃ©cupÃ¨re les dÃ©tails d'un mÃ©tier ROME par son code.
    
    Args:
        code: Code ROME (ex: "M1805")
        
    Returns:
        DÃ©tails du mÃ©tier ou dict vide
    """
    if not code or not code.strip():
        return {}
    
    headers = _get_auth_headers()
    if not headers:
        logger.warning("âš ï¸  rome_get_job_details() : pas de token disponible")
        return {}
    
    url = f"{ROME_BASE_URL}/v1/fiches-rome/fiche-metier"
    
    try:
        logger.debug("ðŸ“„ DÃ©tails mÃ©tier : %s", code)
        
        response = requests.get(
            url,
            params={"code": code},
            headers=headers,
            timeout=ROME_TIMEOUT,
        )
        
        if response.status_code != 200:
            logger.warning("âš ï¸  rome_get_job_details('%s') â†’ HTTP %s", code, response.status_code)
            return {}
        
        data = response.json()
        return data if isinstance(data, dict) else {}
    
    except requests.exceptions.Timeout:
        logger.error("â±ï¸  Timeout lors de la rÃ©cupÃ©ration des dÃ©tails : '%s'", code)
        return {}
    except Exception as e:
        logger.error("âŒ Exception rome_get_job_details('%s') : %s", code, e)
        return {}


def _extract_competencies_from_job(job_data: dict) -> List[str]:
    """Extrait les compÃ©tences d'une fiche mÃ©tier ROME."""
    competencies = []
    
    groups = job_data.get("groupesCompetencesMobilisees") or []
    for group in groups:
        if not isinstance(group, dict):
            continue
        
        comps = group.get("competences")
        if not isinstance(comps, list):
            continue
        
        for comp in comps:
            if isinstance(comp, dict):
                label = (comp.get("libelle") or "").strip()
                if label:
                    competencies.append(label)
    
    return competencies


def _extract_job_label(job_data: dict) -> str:
    """Extrait le libellÃ© d'un mÃ©tier."""
    metier = job_data.get("metier") or {}
    return (metier.get("libelle") or "").strip()


def _extract_job_code(job_data: dict) -> str:
    """Extrait le code ROME d'un mÃ©tier."""
    code = (job_data.get("code") or "").strip()
    if not code and isinstance(job_data.get("metier"), dict):
        code = (job_data["metier"].get("code") or "").strip()
    return code


# ============================================================
#  ROUTES FLASK
# ============================================================

@projection_metier_bp.route("/", methods=["GET"])
def index():
    """Page d'accueil de la projection mÃ©tiers."""
    users = User.query.order_by(User.last_name, User.first_name).all()
    return render_template("projection_metier.html", users=users)


@projection_metier_bp.route("/analyze_user/<int:uid>", methods=["GET"])
@projection_metier_bp.route("/analyze/<int:uid>", methods=["GET"])
def analyze_user(uid: int):
    """
    Analyse un utilisateur et retourne les mÃ©tiers ROME compatibles.
    
    Args:
        uid: ID de l'utilisateur
        
    Returns:
        JSON avec mÃ©tiers maÃ®trisables et envisageables
    """
    logger.info("=" * 60)
    logger.info("ðŸš€ Analyse utilisateur : ID %d", uid)
    logger.info("=" * 60)
    
    if uid <= 0:
        logger.error("âŒ ID utilisateur invalide : %d", uid)
        return jsonify({"error": "INVALID_USER_ID"}), 400
    
    # RÃ©cupÃ©rer l'utilisateur
    user = User.query.get_or_404(uid)
    logger.info("ðŸ‘¤ Utilisateur : %s %s", user.first_name, user.last_name)
    
    # Extraire les compÃ©tences
    user_competencies = _extract_user_competencies(uid)
    
    if not user_competencies:
        logger.warning("âš ï¸  Aucune compÃ©tence trouvÃ©e pour l'utilisateur %d", uid)
        return jsonify({
            "full": [],
            "partial": [],
            "page": {
                "full": {"offset": 0, "limit": 0, "total": 0, "has_more": False},
                "partial": {"offset": 0, "limit": 0, "total": 0, "has_more": False},
            },
            "info": {"user": uid, "message": "Aucune compÃ©tence trouvÃ©e"}
        })
    
    # PrÃ©parer les donnÃ©es pour le matching
    user_items = []
    all_user_tokens = set()
    
    for comp in user_competencies:
        normalized = _normalize(comp)
        tokens = set(_tokenize(comp))
        if normalized and tokens:
            user_items.append({
                "raw": comp,
                "normalized": normalized,
                "tokens": tokens
            })
            all_user_tokens |= tokens
    
    logger.info("ðŸ“Š %d compÃ©tences Ã  analyser", len(user_items))
    
    # Rechercher les mÃ©tiers ROME
    logger.info("ðŸ” Recherche de mÃ©tiers ROME...")
    
    rome_jobs_pool = {}
    
    for comp in user_competencies:
        normalized = _normalize(comp)
        if not normalized:
            continue
        
        # Extraire les mots significatifs (>3 caractÃ¨res)
        words = [w for w in normalized.split() if len(w) > 3]
        if not words:
            words = [normalized]
        
        # Rechercher avec chaque mot
        for word in words[:3]:  # Limiter Ã  3 mots pour Ã©viter trop d'appels
            results = rome_search_jobs(word)
            for job in results:
                code = _extract_job_code(job)
                if code and code not in rome_jobs_pool:
                    rome_jobs_pool[code] = job
    
    logger.info("ðŸ“¦ %d mÃ©tiers ROME trouvÃ©s", len(rome_jobs_pool))
    
    # Analyser chaque mÃ©tier
    fully_matching = []
    partially_matching = []
    
    for code, job_summary in rome_jobs_pool.items():
        # RÃ©cupÃ©rer les dÃ©tails complets
        job_details = rome_get_job_details(code)
        if not job_details:
            continue
        
        job_label = _extract_job_label(job_details)
        job_competencies = _extract_competencies_from_job(job_details)
        
        if not job_competencies:
            # MÃ©tier sans compÃ©tences dÃ©finies
            partially_matching.append({
                "code": code,
                "label": job_label,
                "score": 0,
                "owned": [],
                "missing": [],
                "owned_count": 0,
                "missing_count": 0,
                "total": 0,
            })
            continue
        
        # Matching des compÃ©tences
        owned = []
        missing = []
        
        for rome_comp in job_competencies:
            rome_tokens = set(_tokenize(rome_comp))
            
            # VÃ©rifier s'il y a un overlap avec les tokens utilisateur
            if not (rome_tokens & all_user_tokens):
                missing.append(rome_comp)
                continue
            
            # Calculer les scores de similaritÃ©
            best_ratio = 0.0
            best_jaccard = 0.0
            
            for user_item in user_items:
                # VÃ©rifier overlap des tokens
                if not (rome_tokens & user_item["tokens"]):
                    continue
                
                ratio, jaccard = _text_similarity(rome_comp, user_item["raw"])
                if ratio > best_ratio:
                    best_ratio = ratio
                if jaccard > best_jaccard:
                    best_jaccard = jaccard
            
            # DÃ©cider si la compÃ©tence est couverte
            if best_ratio >= RATIO_THRESHOLD or best_jaccard >= JACCARD_THRESHOLD:
                owned.append(rome_comp)
            else:
                missing.append(rome_comp)
        
        # Calculer le score
        total = len(job_competencies)
        owned_count = len(owned)
        score = round((owned_count / total) * 100, 1) if total > 0 else 0.0
        
        job_result = {
            "code": code,
            "label": job_label,
            "score": score,
            "owned": owned,
            "missing": missing,
            "owned_count": owned_count,
            "missing_count": len(missing),
            "total": total,
        }
        
        # Classer le mÃ©tier
        if owned_count == total and total > 0:
            fully_matching.append(job_result)
        elif owned_count > 0:
            partially_matching.append(job_result)
        else:
            partially_matching.append(job_result)
    
    # Trier par score dÃ©croissant
    fully_matching.sort(key=lambda x: x["score"], reverse=True)
    partially_matching.sort(key=lambda x: x["score"], reverse=True)
    
    logger.info("âœ… Analyse terminÃ©e : %d mÃ©tiers maÃ®trisables, %d envisageables",
                len(fully_matching), len(partially_matching))
    
    # Pagination
    full_offset = int(request.args.get("full_offset", 0))
    full_limit = int(request.args.get("full_limit", 30))
    partial_offset = int(request.args.get("partial_offset", 0))
    partial_limit = int(request.args.get("partial_limit", 30))
    
    full_total = len(fully_matching)
    partial_total = len(partially_matching)
    
    full_page = fully_matching[full_offset:full_offset + full_limit] if full_limit else []
    partial_page = partially_matching[partial_offset:partial_offset + partial_limit] if partial_limit else []
    
    return jsonify({
        "full": full_page,
        "partial": partial_page,
        "page": {
            "full": {
                "offset": full_offset,
                "limit": full_limit,
                "total": full_total,
                "has_more": full_offset + full_limit < full_total,
            },
            "partial": {
                "offset": partial_offset,
                "limit": partial_limit,
                "total": partial_total,
                "has_more": partial_offset + partial_limit < partial_total,
            },
        },
        "info": {"user": uid}
    }), 200