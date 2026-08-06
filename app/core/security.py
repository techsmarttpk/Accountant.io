"""Authentication for first-party clients (the Telegram bot, future web app).

Scope note: this repository does not yet implement end-user OAuth/JWT login
because the only current client is the Telegram bot, whose users are
identified by their Telegram user id (see `app.schemas.user`). What this
module protects is service-to-service trust — the bot must prove it's an
authorized caller of the backend, via a shared secret in the
`X-Internal-Api-Key` header, checked with a constant-time comparison.

Adding real per-human-user auth (JWT/OAuth2) for a future web frontend is a
matter of adding a new dependency here (e.g. `get_current_user`) without
touching this one.
"""

import hmac

from fastapi import Depends, Header

from app.core.config import Settings, get_settings
from app.core.exceptions import UnauthorizedError


def verify_internal_api_key(
    x_internal_api_key: str = Header(default=""),
    settings: Settings = Depends(get_settings),
) -> None:
    expected = settings.internal_api_key.get_secret_value()
    if not x_internal_api_key or not hmac.compare_digest(x_internal_api_key, expected):
        raise UnauthorizedError("Missing or invalid internal API key.")
