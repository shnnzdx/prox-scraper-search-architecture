<<<<<<< HEAD
# Runbook: Scraper & Search Infrastructure Operations
=======
# Runbook
>>>>>>> 475eb6b (Initial Track A prototype submission)

## Purpose

This runbook is the operational guide for deploying, debugging, and monitoring the scraper and search infrastructure. It is written for an early-stage grocery search system where the Search API must stay responsive even when retailer scraping is slow, expensive, or partially failing.

This document covers:

- deployment checks,
- local and production verification,
- monitoring dashboards,
- incident response,
- rollback,
- and post-incident review.

## System Components Covered

The runbook assumes the architecture contains the following components:

- Search API
- Redis / ElastiCache for hot cache, dedupe locks, rate-limit counters, and freshness markers
- OpenSearch for user-facing product search
- Postgres for normalized product records and job metadata
- S3 for raw scrape outputs
- SQS queues per retailer or job type
- Worker services for retailer fetch, parse, normalize, and index-update tasks
- Dead-letter queues for failed jobs
- Secrets Manager for production secrets
- CloudWatch or an equivalent logging and metrics system

The exact cloud provider can change, but the operational model should remain the same: keep search fast, isolate retailer failures, avoid duplicate scraping, and control cost.

---

## Deployment Runbook

### 1. Pre-Deploy Checklist

Before deploying a new version, verify:

- all required environment variables are defined,
- production secrets are stored in the secret manager, not committed to the repo,
- `.env` is excluded from version control,
- `.env.example` is up to date for local development,
- database migrations have been reviewed,
- queue names and dead-letter queue names are correct,
- retailer concurrency limits are configured,
- circuit breakers are initially closed unless a retailer is already degraded,
- cache TTL settings are intentional,
- worker retry limits are configured,
- dashboards and alerts exist for the changed components,
- and rollback steps are known.

### 2. Safe Deployment Order

Use this order to reduce risk:

1. Deploy database migrations that are backward-compatible.
2. Deploy worker code with support for both old and new job payloads.
3. Deploy Search API code.
4. Enable new queues, retailer adapters, or refresh logic behind a feature flag.
5. Gradually increase traffic or job volume.
6. Watch latency, queue depth, failure rate, retry volume, and cost indicators.

Do not deploy an API change that depends on worker behavior unless the worker version is already available.

### 3. Local Prototype Verification

For the local prototype, run these smoke tests before considering the implementation complete:

1. Submit a search request for a common query such as `milk`.
2. Confirm the first request checks cache, queries indexed data, and enqueues refresh only if needed.
3. Submit the same request again.
4. Confirm the second request uses cache or suppresses duplicate refresh through the job key.
5. Trigger a mock retailer failure.
6. Confirm retry with exponential backoff occurs.
7. Confirm the job is written to a mock dead-letter list or `failed_jobs.json` after retry exhaustion.
8. Confirm logs include query, retailer, job key, attempt count, status, and duration.

### 4. Production Smoke Tests

After deployment, verify:

- `/health` returns healthy for the Search API,
- Redis is reachable,
- OpenSearch queries complete within expected latency,
- a known cached query returns quickly,
- a cache miss creates only one refresh job,
- retailer queues receive jobs,
- workers consume jobs successfully,
- failed jobs route to the correct dead-letter queue,
- raw output is written to S3,
- normalized records are written to the database,
- and the search index receives updates.

### 5. Rollback Plan

Rollback should be safe and fast.

If the Search API deployment causes user-facing errors:

1. Roll back the API to the previous stable version.
2. Keep workers running if they remain compatible with existing job payloads.
3. Disable new feature flags.
4. Serve cached or stale-labeled results while the issue is investigated.

If a worker deployment causes scrape failures:

1. Stop or scale down the affected worker version.
2. Keep the Search API online.
3. Pause only the affected retailer queue or job type.
4. Serve stale-labeled results for the impacted retailer.
5. Re-drive failed jobs only after the parser or worker fix is validated.

If a schema migration causes issues:

1. Stop new writes if data corruption is possible.
2. Roll back application code first if the migration is backward-compatible.
3. Restore from backup only if necessary.
4. Record affected job IDs and product records for later repair.

---

## Monitoring Dashboards

<<<<<<< HEAD
In a production version, the team should maintain dashboards for the following areas.
=======
Operators should maintain dashboards for the following areas.
>>>>>>> 475eb6b (Initial Track A prototype submission)

### Search API

Track:

- request count,
- p50 / p95 / p99 latency,
- error rate,
- timeout rate,
- cache hit rate,
- stale response rate,
- and percentage of requests that trigger refresh jobs.

### Cache and Freshness

Track:

- Redis hit rate,
- Redis memory usage,
- dedupe lock creation rate,
- duplicate-job suppression rate,
- result freshness age by data type,
- negative-cache hit rate,
- and TTL expiration patterns.

### OpenSearch

Track:

- query latency,
- query error rate,
- indexing latency,
- index size,
- rejected requests,
- and slow queries.

### Queue and Worker Health

Track per retailer:

- queue depth,
- oldest message age,
- worker success rate,
- worker failure rate,
- average job duration,
- retry count,
- dead-letter queue growth,
- timeout rate,
- and concurrency usage.

### Cost and Capacity

Track:

- scrape jobs per day,
- browser-based jobs per day,
- proxy usage,
- retries per retailer,
- failed job volume,
- S3 raw storage growth,
- worker compute usage,
- and estimated cost per retailer.

---

## Alerting Policy

Alerts should be actionable and tied to user impact, reliability, or cost.

Recommended alerts:

| Signal | Example Threshold | First Response |
|---|---:|---|
| API p95 latency | above target for 15 minutes | check cache hit rate and OpenSearch latency |
| API error rate | above 2% for 10 minutes | inspect API logs and recent deploys |
| Retailer failure rate | above 50% for 10 minutes | open retailer circuit breaker |
| Queue oldest message age | above freshness SLA | inspect worker health and backlog |
| DLQ growth | sustained for 10 minutes | pause affected job type and inspect failures |
| Duplicate suppression drops | sudden sharp drop | inspect dedupe key and lock TTL |
| Retry volume spikes | 2x normal baseline | check retailer outage or parser breakage |
| Daily scrape count | exceeds forecast | enforce scrape cap and review cache behavior |
| Proxy spend estimate | exceeds threshold | disable long-tail refresh and browser fallback |

Alerts should avoid paging for every individual scrape failure. Retailer scraping is expected to be partially unreliable. Page only when failures are sustained, expensive, or user-visible.

---

## Debugging Playbooks

## Incident 1: Search Latency Is High

### Symptoms

- p95 or p99 search latency increases.
- API timeouts rise.
- User requests appear to hang.
- Search results take longer even for common queries.

### Checks

1. Check Redis cache hit rate.
2. Check OpenSearch p95 latency.
3. Confirm the API is not waiting for scraping to finish.
4. Confirm stale-while-revalidate behavior is enabled.
5. Check recent API deploys or query-ranking changes.
6. Check whether cache TTL was shortened too aggressively.

### Likely Causes

- cache miss spike,
- degraded OpenSearch cluster,
- bad query expansion logic,
- excessive filtering or sorting,
- Redis connection issues,
- or accidental synchronous scraping behavior.

### Immediate Actions

- disable synchronous refresh paths,
- return stale-labeled results where possible,
- temporarily reduce expensive query features,
- increase cache TTL for safe result types,
- and roll back the API if the issue came from a recent deploy.

---

## Incident 2: Queue Depth Is Rising

### Symptoms

- retailer queue backlog grows continuously,
- oldest message age increases,
- freshness age increases,
- refresh jobs lag behind demand.

### Checks

1. Identify which retailer queue is growing.
2. Compare enqueue rate against worker completion rate.
3. Check worker errors, timeouts, and retry storms.
4. Verify concurrency settings for the affected retailer.
5. Check whether dedupe locks are failing.
6. Check whether a preload job unexpectedly created too much work.

### Likely Causes

- retailer site slowdown,
- parser breakage,
- concurrency set too low,
- worker deployment issue,
- duplicate jobs bypassing dedupe,
- or a preload job producing too many refresh tasks.

### Immediate Actions

- throttle enqueue volume,
- pause long-tail on-demand refresh,
- increase worker capacity only if the retailer path is healthy,
- open the circuit breaker if the retailer is failing,
- and serve stale-labeled results until the backlog is controlled.

---

## Incident 3: Failure Rate Spikes for One Retailer

### Symptoms

- retailer-specific worker errors rise quickly,
- retry count spikes,
- DLQ starts growing,
- freshness for that retailer gets older.

### Checks

1. Inspect recent worker logs for parsing failures, timeout errors, access-denied patterns, or login/session errors.
2. Compare failure rate over the last 5 to 10 minutes against normal baseline.
3. Validate circuit breaker behavior.
4. Confirm whether the retailer adapter recently changed.
5. Inspect raw payloads from S3 to identify markup or response changes.
6. Check whether proxy or credentials changed.

### Likely Causes

- retailer markup change,
- blocked or rate-limited requests,
- expired credentials,
- parser bug,
- retailer outage,
- or proxy degradation.

### Immediate Actions

- open the circuit breaker for that retailer,
- stop on-demand refresh jobs for that retailer,
- keep serving stale cached results if available,
- prevent retry storms by lowering retry limits,
- and notify the team.

### Follow-Up

- patch the parser or adapter,
- validate with a small controlled replay,
- reprocess failed jobs from DLQ only after validation,
- and update tests with the failure case.

---

## Incident 4: Duplicate Jobs Are Being Created

### Symptoms

- the same logical retailer/query/store refresh appears multiple times,
- scrape spend rises without freshness gains,
- worker fleets look busy without improving user results,
- duplicate suppression rate drops.

### Checks

1. Verify job key construction.
2. Check lock TTL and pending-job registry behavior.
3. Confirm normalization of query, ZIP code, store ID, and retailer ID.
4. Confirm retry jobs are not being counted as new jobs.
5. Check whether different code paths construct different job keys.
6. Check whether lock expiration is shorter than job completion time.

### Likely Causes

- inconsistent query normalization,
- freshness bucket too granular,
- lock TTL too short,
- missing retailer or store identifier in the job key,
- queue retry behavior mistaken for new work,
- or a bug in the pending-job registry.

### Immediate Actions

- tighten the dedupe key,
- increase lock TTL to match the freshness window,
- make workers idempotent,
- pause affected long-tail refresh jobs,
- and review duplicate examples before re-enabling full volume.

---

## Incident 5: Cost Spikes Unexpectedly

### Symptoms

- proxy or compute usage jumps,
- browser-based jobs increase,
- daily scrape count exceeds forecast,
- budget alerts fire,
- scrape volume rises without better freshness.

### Checks

1. Check duplicate suppression rate.
2. Check retry volume by retailer.
3. Check whether browser-based jobs increased.
4. Check whether preload scope expanded without review.
5. Check whether a retailer outage is causing repeated expensive retries.
6. Compare top scrape-producing queries against top user queries.

### Likely Causes

- duplicate work,
- retry storm,
- runaway long-tail refresh,
- accidentally low TTL,
- browser fallback overuse,
- or a bad preload configuration.

### Immediate Actions

- cap daily scrape volume,
- reduce browser-only fallbacks,
- lower retry ceilings,
- pause low-value long-tail refresh,
- increase TTL for low-risk data,
- and keep only high-demand refresh jobs active until cost stabilizes.

---

## Incident 6: Freshness Complaints Increase

### Symptoms

- support reports outdated prices,
- freshness age metrics drift upward,
- search results are fast but older than expected,
- users see stale price or deal labels frequently.

### Checks

1. Check freshness age by data type.
2. Confirm scheduled preload jobs are running.
3. Check queue backlog for price-refresh jobs.
4. Confirm TTL policy has not been set too aggressively.
5. Check whether circuit breakers are open for major retailers.
6. Check whether high-demand items are included in preload.

### Likely Causes

- preload failure,
- queue backlog,
- under-provisioned workers,
- too many long-tail jobs crowding out high-value refresh,
- or a retailer-specific outage.

### Immediate Actions

- prioritize price and promotion refresh jobs,
- pause low-value refresh jobs,
- raise refresh frequency for high-demand items,
- keep stable metadata on longer TTLs,
- and clearly label stale results.

---

## Incident 7: Search Results Look Incorrect

### Symptoms

- wrong products appear for a query,
- price sorting looks incorrect,
- products appear under the wrong retailer or ZIP code,
- duplicate product rows appear.

### Checks

1. Inspect normalized product records.
2. Compare raw scrape output against normalized output.
3. Check product matching and deduplication logic.
4. Check index-update events.
5. Confirm store ID and ZIP code mapping.
6. Check whether stale indexed documents were not removed.

### Likely Causes

- normalization bug,
- product matching bug,
- stale index documents,
- incorrect store metadata,
- parser extracting the wrong fields,
- or duplicate product IDs.

### Immediate Actions

- stop indexing from the affected worker if corruption is ongoing,
- keep raw scrape outputs,
- fix normalization or product matching logic,
- reprocess affected raw payloads,
- and rebuild the affected index partition if needed.

---

## Incident 8: Secrets or Credentials Fail

### Symptoms

- workers receive authentication errors,
- proxy requests fail,
- database connection errors occur,
- multiple retailers fail at the same time.

### Checks

1. Confirm the secret exists in the secret manager.
2. Confirm the deployed service has permission to read it.
3. Check whether the secret was rotated recently.
4. Check whether environment variables reference the correct secret name.
5. Confirm local `.env` values are not being used in production.

### Immediate Actions

- roll back the secret reference if it changed,
- rotate compromised or expired credentials,
- restart affected workers after secret update,
- and verify with one controlled job before re-enabling full traffic.

---

## Degraded Mode Policy

When a dependency is unhealthy, prefer degraded service over total failure.

Acceptable degraded modes:

- return stale-but-labeled results,
- return partial retailer coverage,
- temporarily disable one retailer,
- pause long-tail refresh,
- use cached weekly deals only,
- or show freshness timestamps.

Unacceptable degraded modes:

- block user requests until scraping finishes,
- retry indefinitely,
- allow one retailer outage to consume all worker capacity,
- silently show stale data without freshness labeling,
- or bypass cost guardrails to catch up quickly.

---

## Dead-Letter Queue Handling

Failed jobs should not be ignored.

For DLQ review:

1. Group failed jobs by retailer, error type, and adapter version.
2. Identify whether the failure is transient, parser-related, credential-related, or data-related.
3. Fix the root cause before replaying.
4. Replay a small sample first.
5. Replay the full batch only after the sample succeeds.
6. Keep records of replayed job IDs and outcomes.

Do not replay a large DLQ batch while the original failure is still active.

---

## Recovery Principles

- Prefer degraded service over total failure.
- Serve stale-but-labeled results before blocking users.
- Localize retailer incidents instead of pausing the whole platform.
- Avoid retry storms during external instability.
- Keep enough raw data and job metadata to replay safely.
- Roll back risky changes before adding new complexity.
- Restore user-facing search first, then freshness.

---

## Escalation Thresholds

Escalate when:

- API p95 latency exceeds target for 15 minutes,
- API error rate stays above 2% for 10 minutes,
- retailer failure rate exceeds 50% over 10 minutes,
- DLQ growth is sustained,
- queue oldest message age exceeds freshness SLA,
- duplicate suppression unexpectedly drops,
- or cost guardrails are breached.

---

## Post-Incident Review

After stabilization, capture:

- incident start and end time,
- root cause,
- affected retailer or component,
- user impact,
- wasted scrape volume,
- freshness impact,
- cost impact,
- mitigations,
- follow-up fixes,
- and owner for each action item.

Each incident should end with one concrete prevention change, not just a summary.
<<<<<<< HEAD

=======
>>>>>>> 475eb6b (Initial Track A prototype submission)
