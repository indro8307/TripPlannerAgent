# Trip planner agent

A learning project: an AI agent that finds the cheapest 2-day Amtrak round trip from Metropark (`MET`) to Washington (`WAS`) and back, using sample data. A 2-day trip is two days and one night, so the return is the next day.

## How it works

The OpenAI model named in `.env` (by default `gpt-6-luna`) decides which departure dates to price, then picks the trip with the lowest total. Its only tool is `price_trip(depart_date)`. That tool sets the return to the next day, picks the cheapest eligible coach train each way from the JSON fixtures, and adds the two fares. The loop in `agent.py` runs the tool, sends the JSON back to the model, and stops when the model answers or after 15 steps.

## How to run

```text
python -m pip install -r requirements.txt
```

Put your OpenAI key in `.env`:

```text
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-6-luna
```

Then run:

```text
python agent.py
```

## Example output

Request: "Find the cheapest 2-day round trip."

```text
step 1: price_trip depart_date=2026-11-16 total=137
step 1: price_trip depart_date=2026-11-17 total=163
step 1: price_trip depart_date=2026-11-18 total=158
step 1: price_trip depart_date=2026-11-19 total=94
step 1: price_trip depart_date=2026-11-20 total=none
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
reason:      Lowest 2-day trip from MET to WAS departing 2026-11-16 through 2026-11-20.
```

## Testing

`baseline.py` is the answer key. It calls `price_trip` for every departure date and picks the winner without a model. The six cases and their expected winners are in [GOAL.md](GOAL.md).

Run every case through both scripts with one command:

```text
python run_cases.py
python run_cases.py --baseline-only
python run_cases.py case6
```

For each case it checks the baseline against the expected winner, checks that the agent's answer matches the baseline field by field, and checks that the agent priced every departure date. Each run is a separate process, because `tools.py` reads `FIXTURE_CASE` once when it is imported.

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
