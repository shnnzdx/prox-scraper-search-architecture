from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    zip_code: str = Field(min_length=3, max_length=10)


class SearchResponse(BaseModel):
    query: str
    zip_code: str
    freshness_status: str
    cache_hit: bool
    refresh_enqueued: bool
    dedupe_suppressed_jobs: int
    results: list[dict[str, Any]]
    missing_retailers: list[str]
    message: str


class Job(BaseModel):
    job_id: str
    job_key: str
    retailer_id: str
    query: str
    zip_code: str
    store_id: str
    job_type: str
    status: str
    retry_count: int = 0
    created_at: datetime
    updated_at: datetime

