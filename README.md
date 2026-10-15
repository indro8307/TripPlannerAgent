# Trip planner agent

A learning project: an AI agent that finds the cheapest Amtrak round trip from Metropark (`MET`) to Washington (`WAS`) and back, using sample data. The date range and trip length come from the user request. By default the return is the next day (`days=1`).

## How it works

The OpenAI model named in `.env` (by default `gpt-6-luna`) reads the first date, last date, and days from the user message, calls `price_trip(first_date, last_date, days)` once, then picks the trip with the lowest total. If the user does not say how long the trip is, `days` is 1 (return the next day).

Fares live in SQLite (`trips.db`). `python load_fixtures.py` copies JSON from `fixtures/case1` through `fixtures/case6` into a `fares` table (one `dataset` per folder). `search_fares` queries that table. `price_trip` calls `search_fares` for each departure, picks the cheapest eligible coach train each way, and adds the two fares. The loop in `agent.py` runs the tool, sends the JSON back to the model, and stops when the model answers or after 15 steps.

The same agent talks to OpenAI or to a local OpenAI-compatible server such as Ollama. `reasoning_effort` is sent only when the model name starts with `gpt-6`. (When using Qwen3:8b, Reasoning/Thinking is enabled by default)

## How to run

```text
python -m pip install -r requirements.txt
python load_fixtures.py
```

Put your OpenAI key in `.env`:

```text
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-6-luna
```

To use Ollama instead:

```text
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama
OPENAI_MODEL=qwen3:8b
```

Optional trip settings in `.env` (or keep the defaults):

```text
TRIP_FIRST_DATE=2026-11-16
TRIP_LAST_DATE=2026-11-20
TRIP_DAYS=1
```

Then run:

```text
python agent.py
python agent.py --first 2026-11-16 --last 2026-11-20 --days 1
python agent.py --prompt "Find the cheapest 3-night trip from 2026-11-16 through 2026-11-20."
python baseline.py --days 2
```

`--prompt` is the user message sent to the model. Use it to ask for a longer stay in plain language. `--first`, `--last`, and `--days` build a default request from those values.

`trips.db` is generated and is listed in `.gitignore`. Rebuild it after you change a fixture file.

## Example output

Request: "Find the cheapest round trip from MET to WAS. I can leave from 2026-11-16 through 2026-11-20. I want a 1-night trip (return the next day)."

```text
step 1: price_trip first_date=2026-11-16 last_date=2026-11-20 days=1 totals=2026-11-16=137,2026-11-17=163,2026-11-18=158,2026-11-19=94,2026-11-20=none
depart_date: 2026-11-19
out_train:   175
out_depart:  09:40
out_arrive:  12:55
out_bucket:  Saver
out_price:   55
return_date: 2026-11-20
ret_train:   94
ret_depart:  12:15
ret_arrive:  15:32
ret_bucket:  Value
ret_price:   39
total:       94
reason:      Lowest round trip from MET to WAS for the dates and duration the user asked for.
```

## Testing

`baseline.py` is the answer key. It calls `price_trip` once for the date range and picks the winner without a model. The six cases and their expected winners are in [GOAL.md](GOAL.md).

Load the database first, then run every case through both scripts:

```text
python load_fixtures.py
python run_cases.py
python run_cases.py --baseline-only
python run_cases.py case6
```

For each case it checks the baseline against the expected winner, checks that the agent's answer matches the baseline field by field, and checks that the agent priced the full date range. It also prints how many seconds the agent took. Each run is a separate process, because `tools.py` reads `FIXTURE_CASE` once when it is imported.

To run one case by hand, select a dataset before either command:

```text
$env:FIXTURE_CASE = "case1"
python baseline.py
python agent.py
```

`FIXTURE_CASE` is the `dataset` column in `fares` (`case1` through `case6`). `run_cases.py` sets it for you.

`check_price_trip.py` checks `price_trip` against the hand-worked totals in `GOAL.md` on dataset `case1` which is the default. Clear `FIXTURE_CASE` first if you had set it for another case.

```text
python check_price_trip.py
```

## Colab and model comparison

[colab_notebook.ipynb](colab_notebook.ipynb) clones this repo, installs Ollama, loads `trips.db`, and runs `run_cases.py` on a free tier Colab T4 GPU. Point `OPENAI_MODEL` at `qwen3:8b` or `llama3.1:8b`.

Run logs from those experiments are under `results/`. [MODEL_COMPARISON.md](MODEL_COMPARISON.md) compares Llama 3.1 8B and Qwen3 8B on the six cases.
