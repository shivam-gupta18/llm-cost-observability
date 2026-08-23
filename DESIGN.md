# Design Document — LLM Cost & Latency Observability

## Problem

Most portfolio "AI projects" demonstrate that you can call an LLM API.
They don't demonstrate that you can run one the way a team would actually
trust in production: predictable cost, visibility into failures, and a
circuit breaker so a bug or traffic spike can't turn into a surprise
bill.

## Goals

- Track exactly what an LLM call costs, in real time, without needing to
  spend real money to prove the tracking works.
- Make an explicit, inspectable cost/quality tradeoff decision per
  request instead of defaulting every call to the most capable (and most
  expensive) model.
- Fail safe: retry transient errors, hard-stop before a budget is blown.
- Run on infrastructure that costs nothing.

## Architecture

```
                    +-------------+
   POST /ask  ----->|   FastAPI   |
                    |   app.py    |
                    +------+------+
                           |
                 1. check_budget()   (budget_guard.py)
                           |
                 2. choose_model()   (router.py)
                           |
                           v
                  +-------------------+
                  |   llm_client.py    |---- call_with_backoff (retry.py)
                  |  (Gemini wrapper)  |---- @track decorator (decorator.py)
                  +---------+---------+
                           |
              +------------+-------------+
              v                          v
       storage.py (SQLite)       Prometheus metrics (/metrics)
              |                          |
              v                          v
   /dashboard (FastAPI + Chart.js)  Grafana (optional, local Docker)
```

## Components, and the reasoning behind each

### 1. Cost calculation, not cost billing (`pricing.py`, `decorator.py`)

The system never asks a billing API "what did that cost." It multiplies
the token counts every LLM response already returns by a hardcoded rate
table. The cost is derived from usage, not fetched separately — and it's also *why* this project can be demonstrated at zero real spend: the calculation is accurate whether the
call happened on a free tier or a paid one.

**Tradeoff:** the rate table goes stale. Gemini alone shipped several
price changes across 2026. In a real system this table would be a config
file pulled from a small internal service on a schedule, not a constant
in the codebase. That refresh mechanism is deliberately out of scope
here, but worth naming as the next step.

### 2. Complexity-based routing (`router.py`)

A simple, readable heuristic (prompt length + keyword cues) decides
between a cheap/fast model and a more capable one. It is explicitly
*not* a learned classifier — the goal isn't routing accuracy, it's
demonstrating that the system makes a cost decision on purpose, logs the
decision, and that decision is auditable afterward. A more sophisticated
version could use a small, cheap model to classify complexity before
routing.

### 3. Budget guard as a circuit breaker (`budget_guard.py`)

This borrows directly from the circuit-breaker pattern used for flaky
downstream services: instead of retrying (or in this case, spending)
forever, the system trips once cumulative cost crosses a threshold and
refuses further calls until the cap is raised.

### 4. Retry with exponential backoff (`retry.py`)

The same pattern used to stabilize retries for internal service-to-
service calls, applied here to a 429 or transient failure from the model
API instead of an internal dependency.

### 5. Local-only infrastructure (SQLite, Docker Prometheus/Grafana)

No cloud resource is provisioned to run this. SQLite replaces Postgres;
local Prometheus/Grafana in Docker Compose replaces CloudWatch/managed
Grafana.

### 6. FastAPI as the web layer (`app.py`)

Request validation runs through Pydantic models (`AskRequest`,
`AskResponse`), so a malformed request fails with a clear, structured
error before it reaches any business logic — no unhandled `KeyError`,
no silent empty string. FastAPI also generates interactive API
documentation automatically at `/docs`, which doubles as a live
reference for anyone exploring the service.

None of the observability code (`router.py`, `decorator.py`,
`budget_guard.py`, `storage.py`, `retry.py`) imports the web framework
directly — `app.py` is the only file that does. That separation means
the API layer could be swapped without touching how cost, routing, or
retries work.

## Known limitations (worth being upfront about)

- The budget guard is single-process and file-based (SQLite) — it won't
  hold under concurrent traffic from multiple app instances. A real
  version would use a shared counter.
- The routing heuristic is intentionally simple and unvalidated against
  real quality outcomes — it demonstrates the pattern, not a tuned
  policy.
- The pricing table requires manual updates. See the tradeoff note above.

## Possible next steps

- Swap SQLite for Postgres and the local Prometheus/Grafana stack for a
  managed one, to make this deployable for real.
- Add a scheduled job that re-fetches current model pricing instead of a
  hardcoded table.
- Extend routing with a cheap classifier model instead of a
  keyword/length heuristic.
- Add per-tenant budget caps instead of one global cap, mirroring
  tenant-isolation patterns from other backend work.
