# Goal

Find the lowest Amtrak fare in a date range, then report one winning trip.

This file is for you, the person building the agent. It is the spec and the answer key. The model does not open it. When you write the system prompt in `agent.py`, copy only the rules the model must follow: the route, the dates, the departure window, Coach Saver/Value/Flex, the tie rule, and the output fields. Leave the worked example and the five test cases here. Those are how you check the agent's answer. Prices below are invented so the tool can be built and tested before any live search. Change the route, dates, and numbers to match the trip you care about.

## Input

| Field | Sample value | Notes |
|---|---|---|
| Origin | `MET` | Metropark Station |
| Destination | `WAS` | Washington Union Station |
| First date | `2026-11-16` | Monday |
| Last date | `2026-11-20` | Friday. Every date in this range is checked. |
| Adults | `1` | |
| Departure window | `09:00`–`15:00` | Local departure time. A 9:40 departure counts. A 15:05 departure does not. |
| Fare buckets | Saver, Value, Flex | Coach only. These three compete with each other. |
| Target price | `$50` | Used later for an alert. The search still returns the lowest fare when nothing is under this price. |

## Output

One trip:

- date
- train number
- departure time
- arrival time
- fare bucket
- price in dollars
- one-line reason

When two trips have the same price, the earlier departure wins. If those also match, the earlier date wins.

When a date has no trip inside the departure window and fare buckets, skip that date.

When every date has no eligible trip, the result is: no fare found.

## Worked example

Eligible Coach trips from Metropark for one adult. Each departure is inside 09:00–15:00.

| Date | Train | Depart | Arrive | Bucket | Price |
|---|---|---|---|---|---|
| 2026-11-16 | 93 | 09:20 | 12:35 | Saver | 79 |
| 2026-11-16 | 175 | 11:05 | 14:22 | Value | 89 |
| 2026-11-17 | 175 | 09:40 | 12:55 | Value | 65 |
| 2026-11-17 | 141 | 13:10 | 16:28 | Flex | 65 |
| 2026-11-18 | 195 | 10:15 | 13:40 | Value | 120 |
| 2026-11-18 | 87 | 15:00 | 18:12 | Flex | 110 |
| 2026-11-19 | 175 | 09:40 | 12:55 | Saver | 55 |
| 2026-11-20 | 93 | 12:30 | 15:48 | Value | 42 |
| 2026-11-20 | 175 | 09:40 | 12:55 | Flex | 71 |

Train 99 on 2026-11-16 departs at 15:05 and costs $19. That trip is outside the window, so it is excluded even though it is cheaper than every row above. Train 87 at 15:00 on 2026-11-18 stays in, because the window runs through 15:00.

Expected winner:

```text
date:    2026-11-20
train:   93
depart:  12:30
arrive:  15:48
bucket:  Value
price:   42
reason:  Lowest eligible fare from MET to WAS in 2026-11-16 through 2026-11-20.
```

Nov 20 is the last day and holds the cheapest fare, so a search that stops early fails this example. Nov 17 is a price tie at $65; train 175 wins that tie because 09:40 is earlier than 13:10. It is not the overall winner.

## Tool

`search_fares(origin, destination, date, adults)` returns one date:

```json
{
  "date": "2026-11-20",
  "trips": [
    {
      "train": "93",
      "depart": "12:30",
      "arrive": "15:48",
      "bucket": "Value",
      "price": 42.00
    }
  ]
}
```

A date with no trips returns `"trips": []`. The same keys are used on every call.

The model gets prices only from this tool. It does not invent fares.

## Loop

| Part | Role |
|---|---|
| Model | Chooses the next date to search, then chooses the winner. |
| Tool | Returns fares for one date. |
| Loop | Runs the tool and sends the JSON back to the model. |

Stop when the model returns a final answer in the output shape above, or after 15 steps.

Each step is logged as one line: step number, tool name, date requested, and the lowest price returned.

## Done when

A plain loop (`baseline.py`) and the agent both produce the winner above for this example. Then both pass these cases:

1. This example. The winner is train 93 on 2026-11-20 at $42.
2. The cheapest trip is on the first day.
3. Two eligible trips share the lowest price. The earlier departure wins.
4. One date returns no trips. That date is skipped.
5. Every date returns no trips. The result is no fare found.

A case fails when the winner differs, a date is missing from the trace, or the reported price never appeared in a tool result.

## Later

These are out of scope until the five cases pass:

- Replace fixture files with a live search of amtrak.com.
- Save each search in SQLite.
- Alert when a fare is under the $50 target, or lower than the last saved price for the same train and date.
- Run the check once or twice a day.
