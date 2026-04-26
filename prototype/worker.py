import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from prototype.cache import TTLCache, normalize_query
from prototype.job_queue import JobQueue
from prototype.logger import log_event
from prototype.models import Job
from prototype.retailers import ALL_RETAILERS, build_adapters

PROTOTYPE_DIR = Path(__file__).resolve().parent
DATA_DIR = PROTOTYPE_DIR / "data"
INDEX_PATH = DATA_DIR / "mock_index.json"
FAILED_JOBS_PATH = DATA_DIR / "failed_jobs.json"

INDEX_FRESH_SECONDS = 86400
RETRY_BACKOFF_SECONDS = [0.05, 0.15, 0.35]
PER_RETAILER_RUN_LIMIT = {"walmart": 4, "target": 3, "kroger": 2}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_iso(value: str | None) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed


def ensure_data_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not INDEX_PATH.exists():
        INDEX_PATH.write_text("{}", encoding="utf-8")
    if not FAILED_JOBS_PATH.exists():
        FAILED_JOBS_PATH.write_text("[]", encoding="utf-8")


def load_index() -> dict:
    ensure_data_files()
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def save_index(index_data: dict) -> None:
    INDEX_PATH.write_text(json.dumps(index_data, indent=2), encoding="utf-8")


def load_failed_jobs() -> list[dict]:
    ensure_data_files()
    return json.loads(FAILED_JOBS_PATH.read_text(encoding="utf-8"))


def append_failed_job(job: Job, error: str) -> None:
    failed = load_failed_jobs()
    failed.append(
        {
            **job.model_dump(mode="json"),
            "error": error,
            "failed_at": utc_now_iso(),
        }
    )
    FAILED_JOBS_PATH.write_text(json.dumps(failed, indent=2), encoding="utf-8")


def index_lookup(query: str, zip_code: str) -> dict | None:
    index_data = load_index()
    key = f"{zip_code}:{normalize_query(query)}"
    return index_data.get(key)


def is_fresh(entry: dict) -> bool:
    updated_at = parse_iso(entry.get("updated_at"))
    if not updated_at:
        return False
    return datetime.now(timezone.utc) - updated_at <= timedelta(seconds=INDEX_FRESH_SECONDS)


def merge_index_results(query: str, zip_code: str, retailer_id: str, results: list[dict]) -> None:
    key = f"{zip_code}:{normalize_query(query)}"
    index_data = load_index()
    existing = index_data.get(
        key,
        {
            "query": normalize_query(query),
            "zip_code": zip_code,
            "updated_at": utc_now_iso(),
            "results": [],
        },
    )

    old = [r for r in existing.get("results", []) if r.get("retailer_id") != retailer_id]
    existing["results"] = old + results
    existing["updated_at"] = utc_now_iso()
    index_data[key] = existing
    save_index(index_data)


class WorkerEngine:
    def __init__(self, queue: JobQueue, cache: TTLCache) -> None:
        self.queue = queue
        self.cache = cache
        self.adapters = build_adapters()

    def run_once(self) -> dict:
        processed = 0
        succeeded = 0
        failed = 0
        per_retailer_count = {r: 0 for r in ALL_RETAILERS}
        max_iterations = self.queue.pending_size()
        iterations = 0

        while self.queue.pending_size() > 0 and iterations < max_iterations:
            iterations += 1
            job = self.queue.pop_next()
            if not job:
                break
            if per_retailer_count.get(job.retailer_id, 0) >= PER_RETAILER_RUN_LIMIT.get(job.retailer_id, 1):
                self.queue.requeue(job)
                continue

            per_retailer_count[job.retailer_id] = per_retailer_count.get(job.retailer_id, 0) + 1
            processed += 1
            ok = self._process_single_job(job)
            if ok:
                succeeded += 1
            else:
                failed += 1

        return {
            "processed": processed,
            "succeeded": succeeded,
            "failed": failed,
            "pending": self.queue.pending_size(),
        }

    def _process_single_job(self, job: Job) -> bool:
        start = time.perf_counter()
        log_event(
            "worker_job_started",
            job_id=job.job_id,
            job_key=job.job_key,
            retailer_id=job.retailer_id,
            query=job.query,
            zip_code=job.zip_code,
            retry_count=job.retry_count,
            status=job.status,
        )

        adapter = self.adapters[job.retailer_id]
        attempts = len(RETRY_BACKOFF_SECONDS) + 1
        for attempt in range(attempts):
            try:
                results = adapter.search(job.query, job.zip_code)
                merge_index_results(job.query, job.zip_code, job.retailer_id, results)
                # Invalidate stale API cache for this query/ZIP after successful index refresh.
                self.cache.delete(f"{job.zip_code}:{normalize_query(job.query)}")
                job.status = "succeeded"
                self.queue.update(job)
                log_event(
                    "worker_job_succeeded",
                    job_id=job.job_id,
                    job_key=job.job_key,
                    retailer_id=job.retailer_id,
                    query=job.query,
                    zip_code=job.zip_code,
                    duration_ms=int((time.perf_counter() - start) * 1000),
                    status=job.status,
                )
                return True
            except Exception as exc:  # noqa: BLE001
                job.retry_count += 1
                will_retry = attempt < len(RETRY_BACKOFF_SECONDS)
                log_event(
                    "worker_job_failed",
                    job_id=job.job_id,
                    job_key=job.job_key,
                    retailer_id=job.retailer_id,
                    query=job.query,
                    zip_code=job.zip_code,
                    retry_count=job.retry_count,
                    error=str(exc),
                    will_retry=will_retry,
                )
                if attempt < len(RETRY_BACKOFF_SECONDS):
                    backoff = RETRY_BACKOFF_SECONDS[attempt]
                    log_event(
                        "worker_retrying",
                        job_id=job.job_id,
                        job_key=job.job_key,
                        retailer_id=job.retailer_id,
                        query=job.query,
                        zip_code=job.zip_code,
                        retry_count=job.retry_count,
                        error=str(exc),
                    )
                    time.sleep(backoff)
                    continue

                job.status = "failed"
                self.queue.update(job)
                append_failed_job(job, str(exc))
                log_event(
                    "job_dead_lettered",
                    job_id=job.job_id,
                    job_key=job.job_key,
                    retailer_id=job.retailer_id,
                    query=job.query,
                    zip_code=job.zip_code,
                    retry_count=job.retry_count,
                    error=str(exc),
                    duration_ms=int((time.perf_counter() - start) * 1000),
                    status=job.status,
                )
                return False

        return False
