"""Fail-closed platform configuration with safe local defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

Environment = Literal["local", "test", "staging", "production"]
AuthBackend = Literal["demo", "supabase"]
CaseBackend = Literal["sqlite", "postgres"]
QueueBackend = Literal["memory", "supabase"]
CacheBackend = Literal["memory", "redis"]


class PlatformConfigurationError(RuntimeError):
    """Raised before serving traffic when a deployment configuration is unsafe."""


def _missing_settings(settings: "PlatformSettings") -> list[str]:
    requirements = (
        (settings.auth_backend == "supabase", settings.supabase_url, "SUPABASE_URL"),
        (
            settings.case_backend == "postgres" or settings.queue_backend == "supabase",
            settings.database_url,
            "DATABASE_URL",
        ),
        (settings.cache_backend == "redis", settings.redis_url, "PRAMAAN_REDIS_URL"),
        (
            settings.environment == "production" and settings.case_backend == "postgres",
            settings.supabase_service_role_key,
            "SUPABASE_SERVICE_ROLE_KEY",
        ),
    )
    return [name for required, value, name in requirements if required and not value]


def _unsafe_production_backends(settings: "PlatformSettings") -> list[str]:
    expected = {
        "PRAMAAN_AUTH_BACKEND": (settings.auth_backend, "supabase"),
        "PRAMAAN_CASE_BACKEND": (settings.case_backend, "postgres"),
        "PRAMAAN_QUEUE_BACKEND": (settings.queue_backend, "supabase"),
        "PRAMAAN_CACHE_BACKEND": (settings.cache_backend, "redis"),
    }
    return [name for name, (active, required) in expected.items() if active != required]


def _validate_retention(settings: "PlatformSettings") -> None:
    if not 1 <= settings.raw_upload_retention_days <= 3650:
        raise PlatformConfigurationError("PRAMAAN_RAW_UPLOAD_RETENTION_DAYS must be between 1 and 3650")
    if not 30 <= settings.audit_retention_days <= 3650:
        raise PlatformConfigurationError("PRAMAAN_AUDIT_RETENTION_DAYS must be between 30 and 3650")


def _choice(name: str, default: str, allowed: set[str]) -> str:
    value = os.getenv(name, default).strip().lower()
    if value not in allowed:
        choices = ", ".join(sorted(allowed))
        raise PlatformConfigurationError(f"{name} must be one of: {choices}")
    return value


def _integer(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise PlatformConfigurationError(f"{name} must be an integer") from exc


@dataclass(frozen=True, slots=True)
class PlatformSettings:
    environment: Environment
    auth_backend: AuthBackend
    case_backend: CaseBackend
    queue_backend: QueueBackend
    cache_backend: CacheBackend
    database_url: str | None
    redis_url: str | None
    supabase_url: str | None
    supabase_jwt_audience: str
    supabase_service_role_key: str | None = None
    storage_bucket: str = "case-documents"
    raw_upload_retention_days: int = 30
    audit_retention_days: int = 365

    @classmethod
    def from_env(cls) -> "PlatformSettings":
        settings = cls(
            environment=_choice("PRAMAAN_ENV", "local", {"local", "test", "staging", "production"}),  # type: ignore[arg-type]
            auth_backend=_choice("PRAMAAN_AUTH_BACKEND", "demo", {"demo", "supabase"}),  # type: ignore[arg-type]
            case_backend=_choice("PRAMAAN_CASE_BACKEND", "sqlite", {"sqlite", "postgres"}),  # type: ignore[arg-type]
            queue_backend=_choice("PRAMAAN_QUEUE_BACKEND", "memory", {"memory", "supabase"}),  # type: ignore[arg-type]
            cache_backend=_choice("PRAMAAN_CACHE_BACKEND", "memory", {"memory", "redis"}),  # type: ignore[arg-type]
            database_url=os.getenv("DATABASE_URL") or None,
            redis_url=os.getenv("PRAMAAN_REDIS_URL") or None,
            supabase_url=(os.getenv("SUPABASE_URL") or "").rstrip("/") or None,
            supabase_jwt_audience=os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated").strip(),
            supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY") or None,
            storage_bucket=os.getenv("PRAMAAN_STORAGE_BUCKET", "case-documents").strip(),
            raw_upload_retention_days=_integer("PRAMAAN_RAW_UPLOAD_RETENTION_DAYS", 30),
            audit_retention_days=_integer("PRAMAAN_AUDIT_RETENTION_DAYS", 365),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        missing = _missing_settings(self)
        if missing:
            raise PlatformConfigurationError(f"missing required platform settings: {', '.join(sorted(set(missing)))}")

        if self.environment == "production":
            unsafe = _unsafe_production_backends(self)
            if unsafe:
                raise PlatformConfigurationError(
                    "production refuses local-only backends: " + ", ".join(unsafe)
                )
        _validate_retention(self)


@lru_cache(maxsize=1)
def get_platform_settings() -> PlatformSettings:
    return PlatformSettings.from_env()


def reset_platform_settings() -> None:
    get_platform_settings.cache_clear()
