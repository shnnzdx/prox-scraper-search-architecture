import json
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_event(event: str, **fields: Any) -> None:
    payload = {
        "ts": utc_now_iso(),
        "event": event,
    }
    payload.update(fields)
    print(json.dumps(payload, ensure_ascii=True))

