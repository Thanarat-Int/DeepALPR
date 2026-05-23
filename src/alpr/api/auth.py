"""Authentication -- login tokens and request identity resolution.

UI clients log in with username/password and receive a bearer token. Machine
integrations may instead present the static X-API-Key. Tokens are held in
memory: fine for this single-process service; a production deployment would
use signed JWTs or a shared session store.
"""
import secrets

# token -> user dict
_SESSIONS: dict[str, dict] = {}


def issue_token(user: dict) -> str:
    token = secrets.token_hex(24)
    _SESSIONS[token] = user
    return token


def revoke_token(token: str | None):
    if token:
        _SESSIONS.pop(token, None)


def identity_from_request(authorization: str | None,
                          x_api_key: str | None,
                          api_key: str) -> dict | None:
    """Resolve the caller's identity from a request, or None if unauthenticated."""
    if authorization and authorization.startswith("Bearer "):
        return _SESSIONS.get(authorization[7:])
    if x_api_key and secrets.compare_digest(x_api_key, api_key):
        return {"username": "service", "display_name": "API Service", "role": "admin"}
    return None
