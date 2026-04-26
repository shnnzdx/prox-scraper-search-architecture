import hashlib
import time


def freshness_bucket(epoch_seconds: float | None = None, bucket_seconds: int = 300) -> str:
    ts = epoch_seconds if epoch_seconds is not None else time.time()
    return str(int(ts // bucket_seconds))


def make_job_key(
    retailer_id: str,
    store_id: str,
    zip_code: str,
    normalized_query: str,
    job_type: str,
    fresh_bucket: str,
) -> str:
    raw = f"{retailer_id}|{store_id}|{zip_code}|{normalized_query}|{job_type}|{fresh_bucket}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class DedupeRegistry:
    def __init__(self, lock_ttl_seconds: int = 120) -> None:
        self.lock_ttl_seconds = lock_ttl_seconds
        self._locks: dict[str, float] = {}

    def acquire(self, job_key: str) -> bool:
        self.purge_expired()
        now = time.time()
        expires = self._locks.get(job_key)
        if expires and expires > now:
            return False
        self._locks[job_key] = now + self.lock_ttl_seconds
        return True

    def purge_expired(self) -> None:
        now = time.time()
        dead = [k for k, exp in self._locks.items() if exp <= now]
        for key in dead:
            self._locks.pop(key, None)
