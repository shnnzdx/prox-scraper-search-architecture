import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from prototype.cache import TTLCache, cache_key, normalize_query
from prototype.dedupe import DedupeRegistry, freshness_bucket, make_job_key
from prototype.job_queue import JobQueue
from prototype.logger import log_event, utc_now_iso
from prototype.models import SearchRequest, SearchResponse
from prototype.retailers import ALL_RETAILERS
from prototype.worker import (
    FAILED_JOBS_PATH,
    INDEX_FRESH_SECONDS,
    WorkerEngine,
    ensure_data_files,
    index_lookup,
    is_fresh,
)

app = FastAPI(title="Track A Prototype API", version="0.1.0")

<<<<<<< HEAD
=======
STORE_PREFIX = {"walmart": "wm", "target": "tg", "kroger": "kg"}

>>>>>>> 475eb6b (Initial Track A prototype submission)
queue = JobQueue()
cache = TTLCache(default_ttl_seconds=45)
dedupe = DedupeRegistry(lock_ttl_seconds=120)
worker = WorkerEngine(queue=queue, cache=cache)


def read_failed_jobs() -> list[dict]:
    ensure_data_files()
    return json.loads(Path(FAILED_JOBS_PATH).read_text(encoding="utf-8"))


def build_response_from_entry(
    query: str,
    zip_code: str,
    *,
    entry: dict | None,
    cache_hit: bool,
    refresh_enqueued: bool,
    dedupe_suppressed_jobs: int,
    message: str,
) -> SearchResponse:
    if not entry:
        return SearchResponse(
            query=normalize_query(query),
            zip_code=zip_code,
            freshness_status="unavailable",
            cache_hit=cache_hit,
            refresh_enqueued=refresh_enqueued,
            dedupe_suppressed_jobs=dedupe_suppressed_jobs,
            results=[],
            missing_retailers=ALL_RETAILERS,
            message=message,
        )

    existing_retailers = sorted({r.get("retailer_id", "") for r in entry.get("results", []) if r.get("retailer_id")})
    missing = [r for r in ALL_RETAILERS if r not in existing_retailers]
    fresh = is_fresh(entry)
    if fresh and not missing:
        freshness_status = "fresh"
    elif entry.get("results"):
        freshness_status = "partial" if missing else "stale"
    else:
        freshness_status = "unavailable"

    return SearchResponse(
        query=normalize_query(query),
        zip_code=zip_code,
        freshness_status=freshness_status,
        cache_hit=cache_hit,
        refresh_enqueued=refresh_enqueued,
        dedupe_suppressed_jobs=dedupe_suppressed_jobs,
        results=entry.get("results", []),
        missing_retailers=missing,
        message=message,
    )


def enqueue_refresh_jobs(query: str, zip_code: str, retailers: list[str]) -> tuple[int, int]:
    enqueued = 0
    suppressed = 0
    normalized_query = normalize_query(query)
    bucket = freshness_bucket()
    for retailer_id in retailers:
<<<<<<< HEAD
        store_id = f"{retailer_id[:2]}-{zip_code}"
=======
        store_id = f"{STORE_PREFIX.get(retailer_id, retailer_id[:2])}-{zip_code}"
>>>>>>> 475eb6b (Initial Track A prototype submission)
        job_key = make_job_key(
            retailer_id=retailer_id,
            store_id=store_id,
            zip_code=zip_code,
            normalized_query=normalized_query,
            job_type="refresh",
            fresh_bucket=bucket,
        )
        if not dedupe.acquire(job_key):
            suppressed += 1
            log_event(
                "dedupe_suppressed",
                job_key=job_key,
                retailer_id=retailer_id,
                query=normalized_query,
                zip_code=zip_code,
            )
            continue

        queue.enqueue(
            job_key=job_key,
            retailer_id=retailer_id,
            query=normalized_query,
            zip_code=zip_code,
            store_id=store_id,
            job_type="refresh",
        )
        enqueued += 1
        log_event(
            "refresh_enqueued",
            job_key=job_key,
            retailer_id=retailer_id,
            query=normalized_query,
            zip_code=zip_code,
        )
    return enqueued, suppressed


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest) -> SearchResponse:
    request_id = f"req-{utc_now_iso()}"
    normalized_query = normalize_query(req.query)
    key = cache_key(normalized_query, req.zip_code)
    log_event("request_received", request_id=request_id, query=normalized_query, zip_code=req.zip_code)

    cached = cache.get(key)
    if cached:
        log_event("cache_hit", request_id=request_id, query=normalized_query, zip_code=req.zip_code)
        if isinstance(cached, dict) and "freshness_status" in cached:
            cached_payload = dict(cached)
            cached_payload["cache_hit"] = True
            cached_payload["refresh_enqueued"] = False
            cached_payload["dedupe_suppressed_jobs"] = 0
            cached_payload["message"] = "Served from cache; no new refresh job enqueued."
            return SearchResponse(**cached_payload)
        # Backward-compatible fallback if cache contains index entry shape.
        return build_response_from_entry(
            normalized_query,
            req.zip_code,
            entry=cached,
            cache_hit=True,
            refresh_enqueued=False,
            dedupe_suppressed_jobs=0,
            message="Served from cache; no new refresh job enqueued.",
        )

    log_event("cache_miss", request_id=request_id, query=normalized_query, zip_code=req.zip_code)
    entry = index_lookup(normalized_query, req.zip_code)
    if entry:
        log_event("index_hit", request_id=request_id, query=normalized_query, zip_code=req.zip_code)
    else:
        log_event("index_miss", request_id=request_id, query=normalized_query, zip_code=req.zip_code)

    target_retailers = ALL_RETAILERS
    if entry and entry.get("results"):
        existing = {r.get("retailer_id") for r in entry.get("results", [])}
        missing = [r for r in ALL_RETAILERS if r not in existing]
        if is_fresh(entry) and not missing:
            response = build_response_from_entry(
                normalized_query,
                req.zip_code,
                entry=entry,
                cache_hit=False,
                refresh_enqueued=False,
                dedupe_suppressed_jobs=0,
                message="Served from fresh index.",
            )
            cache.set(key, response.model_dump(), ttl_seconds=45)
            return response
        target_retailers = missing if missing else ALL_RETAILERS

    enq_count, suppressed = enqueue_refresh_jobs(normalized_query, req.zip_code, target_retailers)
    refresh_enqueued = enq_count > 0
    response = build_response_from_entry(
        normalized_query,
        req.zip_code,
        entry=entry,
        cache_hit=False,
        refresh_enqueued=refresh_enqueued,
        dedupe_suppressed_jobs=suppressed,
        message="Returned best available data; refresh enqueued." if refresh_enqueued else "Refresh deduplicated.",
    )
    # Keep stale/partial response cached briefly to reduce repeated misses.
    cache.set(key, response.model_dump(), ttl_seconds=20)
    return response


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "queue_pending": queue.pending_size(),
        "cache_size": cache.size(),
        "index_fresh_seconds": INDEX_FRESH_SECONDS,
    }


@app.get("/jobs")
def jobs() -> dict[str, Any]:
    return {"count": len(queue.list_jobs()), "jobs": queue.list_jobs()}


@app.get("/failed-jobs")
def failed_jobs() -> dict[str, Any]:
    items = read_failed_jobs()
    return {"count": len(items), "failed_jobs": items}


@app.post("/worker/run-once")
def worker_run_once() -> dict[str, Any]:
    stats = worker.run_once()
    return {"status": "ok", **stats}
