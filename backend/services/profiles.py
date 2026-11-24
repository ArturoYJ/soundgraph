import hashlib
import logging
import re
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.errors import ApiError
from backend.schemas import CreatedProfile
from backend.services import sessions
from scripts.storage import DATABASE_ERRORS

log = logging.getLogger("soundgraph.profiles")
ACCESS_PATTERN = re.compile(r"(p-[a-f0-9]{32})\.[A-Za-z0-9_-]{43}")


def sync_graph(sql, graph, profile_id, *, tolerate_failure=False):
    """SQL commits first; a durable flag makes graph retries idempotent."""
    try:
        if not sql.graph_pending(profile_id):
            return False
        graph.ensure_profile(profile_id)
        sql.mark_graph_synced(profile_id)
        return False
    except DATABASE_ERRORS as exc:
        if not tolerate_failure:
            raise
        log.warning("profile_graph_sync_pending type=%s code=%s", type(exc).__name__, getattr(exc, "code", None))
        return True


def create(sql, graph, payload, previous):
    profile_id = f"p-{uuid4().hex}"
    code = profile_id + "." + secrets.token_urlsafe(32)
    token = secrets.token_urlsafe(32)
    profile = sql.create_personal_profile(
        profile_id, payload.displayName, hashlib.sha256(code.encode("ascii")).hexdigest(),
        sessions.hash_cookie(token), datetime.now(timezone.utc) + timedelta(seconds=sessions.TTL),
        sessions.hash_cookie(previous),
    )
    pending = sync_graph(sql, graph, profile_id, tolerate_failure=True)
    return CreatedProfile(**profile.model_dump(), accessCode=code, graphPending=pending), token


def sign_in(sql, graph, credentials, previous):
    match = ACCESS_PATTERN.fullmatch(credentials.code)
    profile = sql.find_personal_profile(
        match[1], hashlib.sha256(credentials.code.encode("ascii")).hexdigest(),
    ) if match else None
    if profile is None:
        raise ApiError(401, "invalid_credentials", "El código personal no es válido.")
    token = secrets.token_urlsafe(32)
    sql.create_session(
        sessions.hash_cookie(token), profile.profileId,
        datetime.now(timezone.utc) + timedelta(seconds=sessions.TTL), sessions.hash_cookie(previous),
    )
    sync_graph(sql, graph, profile.profileId, tolerate_failure=True)
    return profile, token
