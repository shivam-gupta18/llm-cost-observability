# LLM Cost & Latency Observability

A FastAPI service that wraps the Gemini API with cost tracking, latency
monitoring, and complexity-based model routing -- applying the kind of
cost and reliability discipline you'd expect from a production backend
service to LLM calls instead of treating them as a black box.

Runs entirely on Gemini's free tier plus local infrastructure (SQLite,
optional Prometheus/Grafana in Docker), so there's no cloud bill
involved in running it.

## Features

- Routes each prompt to a cheaper or more capable model based on length
  and complexity cues, and logs which one it picked and why
- Tracks latency, token counts, and cost for every call -- cost is
  calculated from token counts against published rates, never pulled
  from a billing API
- Retries transient failures with exponential backoff
- Hard-stops once cumulative estimated spend crosses a configurable
  budget cap
- Local dashboard plus Prometheus-compatible metrics for Grafana

## Architecture

See [DESIGN.md](DESIGN.md) for the full breakdown of components and the
reasoning behind each design decision.

## Setup

1. Get a free API key at [Google AI Studio](https://aistudio.google.com)
   -- no card required. Check the free-tier limits shown there; they
   change often.
2. Clone the repo and set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and add your API key.
4. Run it:
   ```bash
   python app.py
   ```
5. Dashboard: `http://localhost:5000/dashboard`
   Interactive API docs (built into FastAPI): `http://localhost:5000/docs`

## Optional: Prometheus + Grafana

```bash
docker compose up -d
```

Prometheus at `localhost:9090`, Grafana at `localhost:3000`
(`admin`/`admin`) -- add Prometheus at `http://prometheus:9090` as a
data source to see the same metrics as a dashboard.

## Tests

```bash
python -m unittest discover tests
```

## Project structure

```
app.py                       FastAPI app: /ask, /dashboard, /metrics
llm_client.py                Gemini API wrapper
test_ask.py                  Manual test script, no curl needed
observability/
  pricing.py                 Per-model rate table
  decorator.py                Cost/latency tracking + Prometheus metrics
  router.py                   Model selection logic
  budget_guard.py             Spend cap
  retry.py                    Backoff on failure
  storage.py                  SQLite metrics store
dashboard/templates/          Dashboard HTML
docker-compose.yml            Local Prometheus + Grafana
tests/                        Unit tests for router + pricing
DESIGN.md                     Architecture and design decisions
```
