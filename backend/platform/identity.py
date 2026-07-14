"""Supabase JWT verification using asymmetric signing keys and strict claims."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from fastapi import HTTPException, Request, status

from backend.platform.config import PlatformSettings, get_platform_settings
from backend.platform.contracts import Principal

_BEARER = re.compile(r"^Bearer\s+([^\s]+)$", re.IGNORECASE)


class IdentityVerificationError(ValueError):
    """A presented access token could not be trusted."""


@dataclass(slots=True)
class SupabaseIdentityProvider:
    issuer: str
    audience: str
    _client: Any

    @classmethod
    def from_settings(cls, settings: PlatformSettings) -> "SupabaseIdentityProvider":
        if not settings.supabase_url:
            raise IdentityVerificationError("SUPABASE_URL is required")
        try:
            from jwt import PyJWKClient
        except ImportError as exc:  # pragma: no cover - deployment packaging guard
            raise IdentityVerificationError("PyJWT[crypto] is required for Supabase authentication") from exc
        issuer = f"{settings.supabase_url}/auth/v1"
        return cls(
            issuer=issuer,
            audience=settings.supabase_jwt_audience,
            _client=PyJWKClient(f"{issuer}/.well-known/jwks.json", cache_keys=True, lifespan=600),
        )

    def verify(self, token: str) -> Principal:
        try:
            import jwt

            signing_key = self._client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256", "RS256"],
                audience=self.audience,
                issuer=self.issuer,
                options={"require": ["exp", "iat", "sub"]},
            )
        except Exception as exc:
            raise IdentityVerificationError("access token verification failed") from exc

        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise IdentityVerificationError("access token has no subject")
        if claims.get("role") != "authenticated":
            raise IdentityVerificationError("access token is not an authenticated-user token")
        return Principal(
            subject=subject,
            session_id=claims.get("session_id") if isinstance(claims.get("session_id"), str) else None,
            assurance_level=claims.get("aal") if isinstance(claims.get("aal"), str) else None,
            is_anonymous=claims.get("is_anonymous") is True,
        )


def bearer_token(request: Request) -> str:
    match = _BEARER.fullmatch(request.headers.get("Authorization", "").strip())
    if not match:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A bearer access token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return match.group(1)


def require_supabase_identity(request: Request) -> Principal:
    settings = get_platform_settings()
    if settings.auth_backend != "supabase":
        raise HTTPException(status_code=503, detail="Supabase authentication is not configured.")
    try:
        principal = get_identity_provider().verify(bearer_token(request))
    except IdentityVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The access token is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    if principal.is_anonymous:
        raise HTTPException(status_code=403, detail="A permanent user account is required.")
    request.state.principal = principal
    return principal


@lru_cache(maxsize=1)
def get_identity_provider() -> SupabaseIdentityProvider:
    return SupabaseIdentityProvider.from_settings(get_platform_settings())


def reset_identity_provider() -> None:
    get_identity_provider.cache_clear()
