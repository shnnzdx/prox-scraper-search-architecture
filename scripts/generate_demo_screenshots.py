import json
import os
import subprocess
import sys
import textwrap
import time
from html import escape
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"
SCREENSHOT_DIR = DOCS_DIR / "screenshots"
REPORT_PATH = SCREENSHOT_DIR / "demo_report.html"
INDEX_PATH = REPO_ROOT / "prototype" / "data" / "mock_index.json"
FAILED_JOBS_PATH = REPO_ROOT / "prototype" / "data" / "failed_jobs.json"
BASE_URL = "http://127.0.0.1:8000"

SCREENSHOTS = [
    ("01_repo_overview.png", "#repo-overview"),
    ("02_api_endpoints.png", "#api-endpoints"),
    ("03_first_search_cache_miss.png", "#first-search"),
    ("04_repeat_search_cache_hit.png", "#repeat-search"),
    ("05_jobs_enqueued.png", "#jobs-enqueued"),
    ("06_worker_run.png", "#worker-run"),
    ("07_fresh_results_after_worker.png", "#fresh-results"),
    ("08_failed_jobs.png", "#failed-jobs"),
    ("09_health.png", "#health-check"),
]

ENDPOINTS = [
    {"method": "POST", "path": "/search", "purpose": "Search request with cache-first behavior"},
    {"method": "GET", "path": "/jobs", "purpose": "Inspect queued and processed refresh jobs"},
    {"method": "POST", "path": "/worker/run-once", "purpose": "Process queued mock retailer jobs"},
    {"method": "GET", "path": "/failed-jobs", "purpose": "Mock dead-letter queue inspection"},
    {"method": "GET", "path": "/health", "purpose": "Basic service health and queue/cache counters"},
]


def reset_demo_data() -> None:
    INDEX_PATH.write_text("{}\n", encoding="utf-8")
    FAILED_JOBS_PATH.write_text("[]\n", encoding="utf-8")


def call(method: str, path: str, payload: dict | None = None) -> dict:
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
    with urlopen(req) as resp:  # nosec B310
        return json.loads(resp.read().decode("utf-8"))


def wait_for_api(timeout_seconds: float = 20.0) -> None:
    deadline = time.time() + timeout_seconds
    last_error = None
    while time.time() < deadline:
        try:
            call("GET", "/health")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(0.25)
    raise RuntimeError(f"API did not become ready in time: {last_error}") from last_error


def build_html(results: dict[str, dict]) -> str:
    sections = [
        {
            "id": "repo-overview",
            "eyebrow": "Repository Overview",
            "title": "README / repo overview",
            "caption": "Architecture-first Track A submission with a local runnable prototype using mock retailer adapters.",
            "payload": {
                "project": "Prox Track A Prototype",
                "track": "Scraper & Search Infrastructure Architecture",
                "prototype_mode": "Local mock adapters only",
                "non_goals": [
                    "No live retailer scraping",
                    "No cloud runtime dependencies in the prototype",
                    "No browser automation in the business logic",
                ],
                "linked_docs": [
                    "docs/architecture.md",
                    "docs/runbook.md",
                    "docs/scale_reliability_cost.md",
                    "docs/demo_screenshots.md",
                ],
            },
        },
        {
            "id": "api-endpoints",
            "eyebrow": "Local API Surface",
            "title": "API endpoints available",
            "caption": "Endpoints exposed by the FastAPI prototype for the deterministic local demo flow.",
            "payload": {"base_url": BASE_URL, "endpoints": ENDPOINTS},
        },
        {
            "id": "first-search",
            "eyebrow": "Step 1",
            "title": "First search: cache miss + refresh enqueued",
            "caption": "Initial request starts from an empty index and enqueues background refresh jobs.",
            "payload": results["first_search"],
        },
        {
            "id": "repeat-search",
            "eyebrow": "Step 2",
            "title": "Repeated search: cache hit / dedupe behavior",
            "caption": "The second request reuses the cached stale response and avoids claiming a new enqueue.",
            "payload": results["repeat_search"],
        },
        {
            "id": "jobs-enqueued",
            "eyebrow": "Step 3",
            "title": "Queued jobs",
            "caption": "Queued mock refresh jobs before the worker runs.",
            "payload": results["jobs"],
        },
        {
            "id": "worker-run",
            "eyebrow": "Step 4",
            "title": "Worker processed jobs",
            "caption": "The local worker processes queued retailer jobs and writes mock index data.",
            "payload": results["worker_run"],
        },
        {
            "id": "fresh-results",
            "eyebrow": "Step 5",
            "title": "Search after worker: fresh indexed mock results",
            "caption": "After the worker run, the next search returns fresh results from the updated local index.",
            "payload": results["post_worker_search"],
        },
        {
            "id": "failed-jobs",
            "eyebrow": "Step 6",
            "title": "Failed jobs / mock DLQ",
            "caption": "The mock dead-letter endpoint remains local and empty for this deterministic success-path demo.",
            "payload": results["failed_jobs"],
        },
        {
            "id": "health-check",
            "eyebrow": "Step 7",
            "title": "Health check",
            "caption": "Basic counters from the local prototype after the demo sequence completes.",
            "payload": results["health"],
        },
    ]

    cards = []
    for section in sections:
        pretty = escape(json.dumps(section["payload"], indent=2))
        cards.append(
            f"""
            <section class="card" id="{section['id']}">
              <div class="eyebrow">{escape(section['eyebrow'])}</div>
              <h2>{escape(section['title'])}</h2>
              <p class="caption">{escape(section['caption'])}</p>
              <pre><code>{pretty}</code></pre>
            </section>
            """
        )

    return textwrap.dedent(
        f"""\
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>Prox Track A Demo Report</title>
          <style>
            :root {{
              --bg: #f5f1e8;
              --paper: #fffdf8;
              --ink: #18202a;
              --muted: #5f6b76;
              --line: #d7cdbd;
              --accent: #0f766e;
              --accent-soft: #d9f0ec;
              --shadow: 0 18px 40px rgba(24, 32, 42, 0.08);
            }}
            * {{ box-sizing: border-box; }}
            body {{
              margin: 0;
              font-family: Georgia, "Times New Roman", serif;
              color: var(--ink);
              background:
                radial-gradient(circle at top left, #f8e7d5 0, transparent 35%),
                linear-gradient(180deg, #f7f4ee 0%, var(--bg) 100%);
            }}
            .page {{
              max-width: 1100px;
              margin: 0 auto;
              padding: 48px 28px 72px;
            }}
            .hero {{
              background: linear-gradient(135deg, rgba(15,118,110,0.95), rgba(21,94,117,0.92));
              color: #f7fbfb;
              border-radius: 28px;
              padding: 40px 42px;
              box-shadow: var(--shadow);
              position: relative;
              overflow: hidden;
            }}
            .hero::after {{
              content: "";
              position: absolute;
              inset: auto -120px -120px auto;
              width: 320px;
              height: 320px;
              border-radius: 50%;
              background: rgba(255,255,255,0.08);
            }}
            .hero h1 {{
              margin: 0 0 12px;
              font-size: 40px;
              line-height: 1.05;
            }}
            .hero p {{
              margin: 0;
              max-width: 760px;
              font-size: 18px;
              line-height: 1.55;
            }}
            .meta {{
              display: flex;
              flex-wrap: wrap;
              gap: 12px;
              margin-top: 22px;
            }}
            .pill {{
              border: 1px solid rgba(255,255,255,0.25);
              border-radius: 999px;
              padding: 9px 14px;
              font-size: 13px;
              letter-spacing: 0.04em;
              text-transform: uppercase;
              background: rgba(255,255,255,0.08);
            }}
            .grid {{
              display: grid;
              grid-template-columns: 1fr;
              gap: 22px;
              margin-top: 26px;
            }}
            .card {{
              background: var(--paper);
              border: 1px solid var(--line);
              border-radius: 24px;
              padding: 26px 28px 28px;
              box-shadow: var(--shadow);
            }}
            .eyebrow {{
              color: var(--accent);
              font-size: 13px;
              text-transform: uppercase;
              letter-spacing: 0.12em;
              font-weight: 700;
              margin-bottom: 10px;
            }}
            h2 {{
              margin: 0 0 10px;
              font-size: 30px;
              line-height: 1.12;
            }}
            .caption {{
              margin: 0 0 18px;
              color: var(--muted);
              font-size: 16px;
              line-height: 1.55;
            }}
            pre {{
              margin: 0;
              padding: 18px 20px;
              border-radius: 18px;
              background: #161c24;
              color: #edf2f7;
              overflow: auto;
              font: 14px/1.55 Consolas, "Courier New", monospace;
              border: 1px solid #28303a;
            }}
            .footer {{
              margin-top: 28px;
              color: var(--muted);
              font-size: 14px;
              line-height: 1.5;
              text-align: center;
            }}
          </style>
        </head>
        <body>
          <main class="page">
            <section class="hero">
              <h1>Prox Track A Demo Evidence</h1>
              <p>
                Deterministic local prototype run using mock retailer adapters only.
                No live scraping, no cloud runtime services, and no business-logic redesign.
              </p>
              <div class="meta">
                <div class="pill">Mock Retailer Adapters</div>
                <div class="pill">Cache-First Search</div>
                <div class="pill">Queued Refresh Jobs</div>
                <div class="pill">Freshness After Worker Run</div>
              </div>
            </section>
            <div class="grid">
              {''.join(cards)}
            </div>
            <p class="footer">
              Generated locally from the Track A prototype with deterministic reset data and a fixed random seed.
            </p>
          </main>
        </body>
        </html>
        """
    )


def generate_report(results: dict[str, dict]) -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(build_html(results), encoding="utf-8")


def run_demo_sequence() -> dict[str, dict]:
    first_search = call("POST", "/search", {"query": "milk", "zip_code": "90210"})
    repeat_search = call("POST", "/search", {"query": "milk", "zip_code": "90210"})
    jobs = call("GET", "/jobs")
    worker_run = call("POST", "/worker/run-once")
    post_worker_search = call("POST", "/search", {"query": "milk", "zip_code": "90210"})
    failed_jobs = call("GET", "/failed-jobs")
    health = call("GET", "/health")
    return {
        "first_search": first_search,
        "repeat_search": repeat_search,
        "jobs": jobs,
        "worker_run": worker_run,
        "post_worker_search": post_worker_search,
        "failed_jobs": failed_jobs,
        "health": health,
    }


def start_server() -> subprocess.Popen[str]:
    command = [
        sys.executable,
        "-c",
        (
            "import random; random.seed(0); "
            "import uvicorn; "
            "uvicorn.run('prototype.app:app', host='127.0.0.1', port=8000, log_level='warning')"
        ),
    ]
    return subprocess.Popen(
        command,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )


def stop_server(process: subprocess.Popen[str]) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)


def capture_screenshots() -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1180}, device_scale_factor=1.4)
        page.goto(REPORT_PATH.resolve().as_uri(), wait_until="networkidle")

        for filename, selector in SCREENSHOTS:
            locator = page.locator(selector)
            locator.scroll_into_view_if_needed()
            locator.screenshot(path=str(SCREENSHOT_DIR / filename))

        browser.close()


def print_summary(results: dict[str, dict]) -> None:
    summary = {
        "report": str(REPORT_PATH.relative_to(REPO_ROOT)),
        "screenshots": [name for name, _ in SCREENSHOTS],
        "first_search_status": results["first_search"]["freshness_status"],
        "repeat_search_cache_hit": results["repeat_search"]["cache_hit"],
        "worker_processed": results["worker_run"]["processed"],
        "post_worker_status": results["post_worker_search"]["freshness_status"],
    }
    print(json.dumps(summary, indent=2))


def main() -> None:
    reset_demo_data()
    process = start_server()
    try:
        wait_for_api()
        results = run_demo_sequence()
        generate_report(results)
        capture_screenshots()
        print_summary(results)
    except URLError as exc:
        raise RuntimeError("Failed to reach local API during screenshot generation.") from exc
    finally:
        stop_server(process)
        reset_demo_data()


if __name__ == "__main__":
    main()
