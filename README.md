# Amtrak fare agent

A learning project: an AI agent that finds the cheapest Amtrak coach fare from Metropark (`MET`) to Washington (`WAS`), using sample data.

## How it works

The OpenAI model named in `.env` (by default `gpt-6-luna`) reads the rules and decides which date to search. The only tool is `search_fares`, which reads a JSON fixture for one date and returns the trips. The loop in `agent.py` runs the tool, sends the JSON back to the model, and stops when the model answers or after 15 steps.

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

Request: "Find the lowest eligible fare."

```text
date:    2026-11-20
train:   93
depart:  12:30
arrive:  15:48
bucket:  Value
price:   42
reason:  Lowest eligible fare from MET to WAS in 2026-11-16 through 2026-11-20.
```

## Testing

`baseline.py` is the answer key. It applies the same rules without a model. Compare its output with `python agent.py` for the cases in [GOAL.md](GOAL.md).

Select a case folder before either command:

```text
$env:FIXTURE_CASE = "case1"
python baseline.py
```

`case1` through `case5` live under `fixtures/`. Clear the setting with `Remove-Item Env:FIXTURE_CASE` to use the original fixture files again.
