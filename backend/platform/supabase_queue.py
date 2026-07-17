"""Not yet wired into the running app — see PRODUCTION_BLUEPRINT.md.
Server-only Supabase Queue adapter using pgmq read and archive semantics."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Mapping, Sequence

from backend.platform.contracts import QueueMessage


class SupabaseJobQueue:
    def __init__(self, connection_pool: Any, queue_name: str = "analysis_jobs") -> None:
        self._pool = connection_pool
        self._queue_name = queue_name

    @classmethod
    def from_database_url(cls, database_url: str) -> "SupabaseJobQueue":
        from psycopg_pool import ConnectionPool

        return cls(ConnectionPool(database_url, min_size=1, max_size=5, open=True))

    def enqueue(self, payload: Mapping[str, Any], delay_seconds: int = 0) -> int:
        with self._pool.connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "select * from pgmq.send(%s, %s::jsonb, %s)",
                (self._queue_name, json.dumps(dict(payload)), delay_seconds),
            )
            row = cursor.fetchone()
            if not row:
                raise RuntimeError("queue did not return a message id")
            return int(row[0])

    def read(self, visibility_seconds: int, batch_size: int = 1) -> Sequence[QueueMessage]:
        with self._pool.connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "select msg_id, read_ct, enqueued_at, vt, message from pgmq.read(%s, %s, %s)",
                (self._queue_name, visibility_seconds, batch_size),
            )
            rows = cursor.fetchall()
        return [
            QueueMessage(
                message_id=int(row[0]),
                read_count=int(row[1]),
                enqueued_at=row[2] if isinstance(row[2], datetime) else datetime.fromisoformat(str(row[2])),
                visible_at=row[3] if isinstance(row[3], datetime) else datetime.fromisoformat(str(row[3])),
                payload=row[4] if isinstance(row[4], Mapping) else json.loads(row[4]),
            )
            for row in rows
        ]

    def archive(self, message_id: int) -> bool:
        with self._pool.connection() as connection, connection.cursor() as cursor:
            cursor.execute("select pgmq.archive(%s, %s)", (self._queue_name, message_id))
            row = cursor.fetchone()
            return bool(row and row[0])
