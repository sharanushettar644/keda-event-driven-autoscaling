"""Message format shared by the producer and the consumer.

Kept free of RabbitMQ code so it can be unit-tested without a broker.
"""

import json
import time
from collections.abc import Callable, Iterator
from dataclasses import asdict, dataclass

MAX_WORK_MS = 60_000


class InvalidMessage(ValueError):
    """Raised for payloads that can never be processed (poison messages)."""


@dataclass(frozen=True)
class Job:
    id: int
    work_ms: int

    def to_bytes(self) -> bytes:
        return json.dumps(asdict(self)).encode()


def build_jobs(count: int, work_ms: int, start_id: int = 1) -> Iterator[Job]:
    """Yield `count` jobs, each simulating `work_ms` of processing."""
    if count < 0:
        raise ValueError("count must be >= 0")
    if not 0 <= work_ms <= MAX_WORK_MS:
        raise ValueError(f"work_ms must be between 0 and {MAX_WORK_MS}")
    for i in range(start_id, start_id + count):
        yield Job(id=i, work_ms=work_ms)


def parse_job(body: bytes) -> Job:
    """Decode and validate a message body."""
    try:
        data = json.loads(body)
        job = Job(id=int(data["id"]), work_ms=int(data["work_ms"]))
    except (ValueError, KeyError, TypeError) as exc:
        raise InvalidMessage(f"malformed message: {body[:100]!r}") from exc
    if not 0 <= job.work_ms <= MAX_WORK_MS:
        raise InvalidMessage(f"work_ms out of range: {job.work_ms}")
    return job


def process(body: bytes, sleep: Callable[[float], None] = time.sleep) -> Job:
    """Handle one message. The sleep stands in for real work (an API call,
    an image resize, a report...). Raises InvalidMessage for poison messages."""
    job = parse_job(body)
    sleep(job.work_ms / 1000)
    return job
