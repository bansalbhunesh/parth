"""Not yet wired into the running app — see PRODUCTION_BLUEPRINT.md.
Authorized private-storage URL issuance for organization/case object paths."""

from __future__ import annotations

import re
import uuid
from pathlib import PurePosixPath
from typing import Any, Protocol

_SAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]+")


class StorageAuthorizationError(PermissionError):
    """The caller is not allowed to access the requested organization path."""


class StorageSigningError(RuntimeError):
    """The storage service did not return a usable signed URL."""


class MembershipAuthorizer(Protocol):
    def can_read(self, organization_id: str, case_id: str, user_id: str) -> bool: ...

    def can_write(self, organization_id: str, case_id: str, user_id: str) -> bool: ...


class PostgresMembershipAuthorizer:
    def __init__(self, connection_pool: Any) -> None:
        self._pool = connection_pool

    def _has_role(
        self,
        organization_id: str,
        case_id: str,
        user_id: str,
        roles: tuple[str, ...] | None,
    ) -> bool:
        query = (
            "select 1 from public.organization_memberships membership "
            "join public.cases case_record on case_record.organization_id = membership.organization_id "
            "where membership.organization_id = %s::uuid and case_record.id = %s::uuid "
            "and membership.user_id = %s::uuid and case_record.deleted_at is null"
        )
        params: list[Any] = [organization_id, case_id, user_id]
        if roles:
            query += " and membership.role = any(%s::public.organization_role[])"
            params.append(list(roles))
        with self._pool.connection() as connection, connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone() is not None

    def can_read(self, organization_id: str, case_id: str, user_id: str) -> bool:
        return self._has_role(organization_id, case_id, user_id, None)

    def can_write(self, organization_id: str, case_id: str, user_id: str) -> bool:
        return self._has_role(organization_id, case_id, user_id, ("owner", "engineer"))


def _uuid_text(value: str, field: str) -> str:
    try:
        return str(uuid.UUID(value))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError(f"{field} must be a UUID") from exc


def _filename(value: str) -> str:
    name = PurePosixPath(value.replace("\\", "/")).name
    name = _SAFE_FILENAME.sub("-", name).strip(".-")
    if not name:
        raise ValueError("filename must contain a safe character")
    return name[:160]


class SupabaseDocumentStorage:
    def __init__(self, storage_client: Any, authorizer: MembershipAuthorizer, bucket: str = "case-documents") -> None:
        self._bucket = storage_client.from_(bucket)
        self._authorizer = authorizer

    @staticmethod
    def object_path(organization_id: str, case_id: str, filename: str) -> str:
        organization = _uuid_text(organization_id, "organization_id")
        case = _uuid_text(case_id, "case_id")
        return f"{organization}/{case}/{uuid.uuid4()}/{_filename(filename)}"

    def signed_upload_url(
        self,
        organization_id: str,
        case_id: str,
        user_id: str,
        filename: str,
    ) -> dict[str, str]:
        if not self._authorizer.can_write(organization_id, case_id, user_id):
            raise StorageAuthorizationError("storage write is not authorized")
        path = self.object_path(organization_id, case_id, filename)
        signed = self._bucket.create_signed_upload_url(path)
        token = signed.get("token") if isinstance(signed, dict) else None
        signed_url = signed.get("signed_url") or signed.get("signedURL") if isinstance(signed, dict) else None
        if not isinstance(token, str) or not token or not isinstance(signed_url, str) or not signed_url:
            raise StorageSigningError("storage did not return an upload token and URL")
        return {"path": path, "token": token, "signed_url": signed_url}

    def signed_download_url(
        self,
        organization_id: str,
        case_id: str,
        user_id: str,
        object_name: str,
        expires_in: int = 300,
    ) -> str:
        organization = _uuid_text(organization_id, "organization_id")
        case = _uuid_text(case_id, "case_id")
        expected = f"{organization}/{case}/"
        if not object_name.startswith(expected) or ".." in PurePosixPath(object_name).parts:
            raise StorageAuthorizationError("object path is outside the authorized case")
        if not 30 <= expires_in <= 900:
            raise ValueError("expires_in must be between 30 and 900 seconds")
        if not self._authorizer.can_read(organization_id, case_id, user_id):
            raise StorageAuthorizationError("storage read is not authorized")
        signed = self._bucket.create_signed_url(object_name, expires_in)
        url = signed.get("signed_url") or signed.get("signedURL") if isinstance(signed, dict) else None
        if not isinstance(url, str) or not url:
            raise StorageSigningError("storage did not return a signed download URL")
        return url
