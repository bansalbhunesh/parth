"""Not yet wired into the running app — see PRODUCTION_BLUEPRINT.md.
Visibility-timeout worker semantics with bounded retry and dead-lettering."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Mapping

from backend.platform.contracts import JobQueue, QueueMessage


@dataclass(frozen=True, slots=True)
class WorkerBatchResult:
    completed: int = 0
    retrying: int = 0
    dead_lettered: int = 0


class DurableWorker:
    def __init__(
        self,
        queue: JobQueue,
        dead_letter_queue: JobQueue,
        handler: Callable[[Mapping[str, Any]], None],
        *,
        visibility_seconds: int = 120,
        max_attempts: int = 5,
    ) -> None:
        if visibility_seconds < 1 or max_attempts < 1:
            raise ValueError("worker bounds must be positive")
        self._queue = queue
        self._dead_letter_queue = dead_letter_queue
        self._handler = handler
        self._visibility_seconds = visibility_seconds
        self._max_attempts = max_attempts

    def _dead_letter(self, message: QueueMessage) -> None:
        self._dead_letter_queue.enqueue(
            {
                "source_message_id": message.message_id,
                "read_count": message.read_count,
                "payload": dict(message.payload),
            }
        )
        if not self._queue.archive(message.message_id):
            raise RuntimeError("failed to archive dead-lettered message")

    def run_once(self, batch_size: int = 10) -> WorkerBatchResult:
        completed = retrying = dead_lettered = 0
        messages = self._queue.read(self._visibility_seconds, batch_size)
        for message in messages:
            try:
                self._handler(message.payload)
            except Exception:
                if message.read_count >= self._max_attempts:
                    self._dead_letter(message)
                    dead_lettered += 1
                else:
                    # Do not archive: visibility expiry makes the durable queue
                    # retry this message without losing it.
                    retrying += 1
                continue
            if not self._queue.archive(message.message_id):
                raise RuntimeError("failed to archive completed message")
            completed += 1
        return WorkerBatchResult(completed, retrying, dead_lettered)
