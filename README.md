# Trip planner agent

A learning project: an AI agent that finds the cheapest Amtrak round trip from Metropark (`MET`) to Washington (`WAS`) and back, using sample data. The date range and trip length come from the user request. By default the return is the next day (`days=1`).

## How it works

The OpenAI model named in `.env` (by default `gpt-6-luna`) reads the first date, last date, and days from the user message, calls `price_trip(first_date, last_date, days)` once, then picks the trip with the lowest total. If the user does not say how long the trip is, `days` is 1 (return the next day). The tool prices every departure from the first date through the last. For each departure it picks the cheapest eligible coach train each way from the JSON fixtures and adds the two fares. The loop in `agent.py` runs the tool, sends the JSON back to the model, and stops when the model answers or after 15 steps.

## How to run

```text
python -m pip install -r requirements.txt
```

Put your OpenAI key in `.env`:

```text
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-6-luna
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

Run every case through both scripts with one command:

```text
python run_cases.py
python run_cases.py --baseline-only
python run_cases.py case6
```

For each case it checks the baseline against the expected winner, checks that the agent's answer matches the baseline field by field, and checks that the agent priced the full date range. Each run is a separate process, because `tools.py` reads `FIXTURE_CASE` once when it is imported.

To run one case by hand, select a case folder before either command:

```text
$env:FIXTURE_CASE = "case1"
python baseline.py
python agent.py
```

`case1` through `case6` live under `fixtures/`. Clear the setting with `Remove-Item Env:FIXTURE_CASE` to use the main fixture files again.

`check_price_trip.py` checks `price_trip` itself against the hand-worked totals in `GOAL.md`. Run it with `FIXTURE_CASE` cleared:

```text
python check_price_trip.py
```
