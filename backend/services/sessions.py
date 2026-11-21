import hashlib
import os
import re
import secrets
from datetime import datetime, timedelta, timezone

from backend.errors import ApiError

COOKIE = "soundgraph_session"
TTL = 8 * 3600
CREDENTIALS = {
    "p-ana-main": "DEMO_CODE_ANA", "p-sofia": "DEMO_CODE_SOFIA",
    "p-new": "DEMO_CODE_NEW", "p-editor": "DEMO_CODE_EDITOR",
}
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_-]{43}")


def configure_codes():
    codes = {profile: os.environ.get(variable, "") for profile, variable in CREDENTIALS.items()}
    if any(len(value) < 24 for value in codes.values()) or len(set(codes.values())) != len(codes):
        raise RuntimeError("Códigos locales ausentes o inválidos. Ejecuta python3 -m scripts.init_env.")
    return codes


def hash_cookie(token):
    if token and TOKEN_PATTERN.fullmatch(token):
        return hashlib.sha256(token.encode("ascii")).hexdigest()
    return None


def sign_in(sql, codes, credentials, previous):
    expected = codes.get(credentials.profileId, "0" * 48)
    matches = secrets.compare_digest(credentials.code.encode("utf-8"), expected.encode("utf-8"))
    profile = sql.find_profile(credentials.profileId) if matches and credentials.profileId in codes else None
    if profile is None:
        raise ApiError(401, "invalid_credentials", "El perfil o el código no son válidos.")
    token = secrets.token_urlsafe(32)
    sql.create_session(hash_cookie(token), profile.profileId,
                       datetime.now(timezone.utc) + timedelta(seconds=TTL), hash_cookie(previous))
    return profile, token


def current_profile(sql, token):
    token_hash = hash_cookie(token)
    profile = sql.find_session(token_hash) if token_hash else None
    if profile is None:
        raise ApiError(401, "session_required", "Tu sesión terminó. Vuelve a entrar.")
    return profile
