from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from prototype.models import Job


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class JobQueue:
    def __init__(self) -> None:
        self._pending: list[str] = []
        self._jobs: dict[str, Job] = {}

    def enqueue(
        self,
        *,
        job_key: str,
        retailer_id: str,
        query: str,
        zip_code: str,
        store_id: str,
        job_type: str = "refresh",
    ) -> Job:
        now = utc_now()
        job = Job(
            job_id=str(uuid4()),
            job_key=job_key,
            retailer_id=retailer_id,
            query=query,
            zip_code=zip_code,
            store_id=store_id,
            job_type=job_type,
            status="queued",
            retry_count=0,
            created_at=now,
            updated_at=now,
        )
        self._jobs[job.job_id] = job
        self._pending.append(job.job_id)
        return job

    def pop_next(self) -> Job | None:
        if not self._pending:
            return None
        job_id = self._pending.pop(0)
        job = self._jobs[job_id]
        job.status = "in_progress"
        job.updated_at = utc_now()
        self._jobs[job_id] = job
        return job

    def requeue(self, job: Job) -> None:
        job.status = "queued"
        job.updated_at = utc_now()
        self._jobs[job.job_id] = job
        self._pending.append(job.job_id)

    def update(self, job: Job) -> None:
        job.updated_at = utc_now()
        self._jobs[job.job_id] = job

    def list_jobs(self) -> list[dict]:
        return [j.model_dump(mode="json") for j in self._jobs.values()]

    def pending_size(self) -> int:
        return len(self._pending)

