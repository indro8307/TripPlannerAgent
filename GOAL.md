# Goal

Find the cheapest 2-day round trip from Metropark to Washington in a date range, then report that trip.

Trip length is configurable. `days` is how many days later the return is. The default is `days=1`: leave Metropark on day D and return from Washington the next day. The user can ask for a longer stay in the prompt. The cost is the outbound fare plus the return fare. Hotel rates come later. Prices below are invented sample data. The worked example uses the default `days=1`.

This file is for you, the person building the agent. It is the spec and the answer key. The model does not open it.

## Input


| Field            | Sample value       | Notes                                                                                                  |
| ---------------- | ------------------ | ------------------------------------------------------------------------------------------------------ |
| Origin           | `MET`              | Metropark Station. Outbound only.                                                                      |
| Destination      | `WAS`              | Washington Union Station. The return is `WAS` to `MET`.                                                |
| First departure  | `2026-11-16`       | Monday. Comes from the user request (`TRIP_FIRST_DATE` / `--first`).                                   |
| Last departure   | `2026-11-20`       | Friday. Comes from the user request (`TRIP_LAST_DATE` / `--last`). Every date in this range is priced. |
| Adults           | `1`                |                                                                                                        |
| `days`           | `1` (default)      | Days from outbound to return. `1` means the next night. The user can ask for a longer trip.            |
| Departure window | `09:00`–`15:00`    | Local departure time, both directions. A 09:40 departure counts. A 15:05 departure does not.           |
| Fare buckets     | Saver, Value, Flex | Coach only. These three compete with each other.                                                       |




## Output

One round trip:

- departure date
- outbound train number, departure time, arrival time, fare bucket, and price
- return date
- return train number, departure time, arrival time, fare bucket, and price
- total in dollars
- one-line reason

The lowest total wins. When two departure dates have the same total, the earlier outbound departure wins. If those also match, the earlier departure date wins.

On one leg, the same rule picks the train: lowest price, then earlier departure.

Skip a departure date when that day has no eligible outbound trip, or the next day has no eligible return trip.

When no departure date has both legs, the result is: no trip found.

## Worked example

Eligible Coach trips for one adult. Each departure is inside 09:00–15:00.

Metropark to Washington:


| Date       | Train | Depart | Arrive | Bucket | Price |
| ---------- | ----- | ------ | ------ | ------ | ----- |
| 2026-11-16 | 93    | 09:20  | 12:35  | Saver  | 79    |
| 2026-11-16 | 175   | 11:05  | 14:22  | Value  | 89    |
| 2026-11-17 | 175   | 09:40  | 12:55  | Value  | 65    |
| 2026-11-17 | 141   | 13:10  | 16:28  | Flex   | 65    |
| 2026-11-18 | 195   | 10:15  | 13:40  | Value  | 120   |
| 2026-11-18 | 87    | 15:00  | 18:12  | Flex   | 110   |
| 2026-11-19 | 175   | 09:40  | 12:55  | Saver  | 55    |
| 2026-11-20 | 93    | 12:30  | 15:48  | Value  | 42    |
| 2026-11-20 | 175   | 09:40  | 12:55  | Flex   | 71    |


Train 99 on 2026-11-16 departs at 15:05 and costs $19. That trip is outside the window, so it is excluded. Train 87 at 15:00 on 2026-11-18 stays in, because the window runs through 15:00. On Nov 17 the two $65 fares tie; train 175 wins that leg because 09:40 is earlier than 13:10.

Washington to Metropark:


| Date       | Train | Depart | Arrive | Bucket | Price |
| ---------- | ----- | ------ | ------ | ------ | ----- |
| 2026-11-16 | 94    | 09:15  | 12:40  | Saver  | 72    |
| 2026-11-16 | 176   | 11:30  | 14:48  | Value  | 84    |
| 2026-11-17 | 174   | 09:50  | 13:05  | Value  | 58    |
| 2026-11-17 | 140   | 13:20  | 16:40  | Flex   | 58    |
| 2026-11-18 | 194   | 10:05  | 13:28  | Value  | 115   |
| 2026-11-18 | 88    | 15:00  | 18:18  | Flex   | 98    |
| 2026-11-19 | 174   | 09:55  | 13:10  | Saver  | 48    |
| 2026-11-20 | 176   | 09:45  | 13:02  | Flex   | 67    |
| 2026-11-20 | 94    | 12:15  | 15:32  | Value  | 39    |


Train 86 on 2026-11-16 departs at 15:10 and costs $22. That trip is outside the window. On Nov 17 the two $58 fares tie; train 174 wins that leg because 09:50 is earlier than 13:20.

Each row below is one departure from a single `price_trip` call with `days=1`. The return is the next day. The fare on each leg is the cheapest eligible train from the tables above.


| Departure  | Return     | Outbound   | Return train | Total |
| ---------- | ---------- | ---------- | ------------ | ----- |
| 2026-11-16 | 2026-11-17 | 93 at $79  | 174 at $58   | 137   |
| 2026-11-17 | 2026-11-18 | 175 at $65 | 88 at $98    | 163   |
| 2026-11-18 | 2026-11-19 | 87 at $110 | 174 at $48   | 158   |
| 2026-11-19 | 2026-11-20 | 175 at $55 | 94 at $39    | 94    |
| 2026-11-20 | 2026-11-21 | 93 at $42  | none         | skip  |


Nov 20 has the cheapest one-way fare, at $42, and no return fixture for Nov 21, so that departure is skipped. The cheapest complete trip leaves on Nov 19.

Expected winner:

```text
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

A search that stops at the first complete trip reports Nov 16 at $137 and fails this example.

## Tools

`search_fares(origin, destination, date, adults)` reads one fixture file and returns every saved trip for that date, including trips outside the rules. `price_trip` calls it. The model does not.

`price_trip(first_date, last_date, days)` prices every departure from `first_date` through `last_date`. `days` is how many days later the return is. `days=1` means the next day. For each departure, the tool chooses the cheapest eligible train in each direction and adds the two fares.

```json
{
  "first_date": "2026-11-16",
  "last_date": "2026-11-20",
  "days": 1,
  "trips": [
    {
      "depart_date": "2026-11-19",
      "return_date": "2026-11-20",
      "outbound": {
        "date": "2026-11-19",
        "train": "175",
        "depart": "09:40",
        "arrive": "12:55",
        "bucket": "Saver",
        "price": 55.00
      },
      "return_trip": {
        "date": "2026-11-20",
        "train": "94",
        "depart": "12:15",
        "arrive": "15:32",
        "bucket": "Value",
        "price": 39.00
      },
      "total": 94.00
    }
  ]
}
```

A missing leg is `null`, and `total` is `null`. The model uses these totals. It does not invent fares or add the prices itself.

Fixture files are `met_was_YYYY-MM-DD.json` and `was_met_YYYY-MM-DD.json`.

## Loop


| Part  | Role                                                                                                                 |
| ----- | -------------------------------------------------------------------------------------------------------------------- |
| Model | Reads first date, last date, and days from the user request, calls `price_trip` once, then chooses the lowest total. |
| Tool  | `price_trip` returns the cheapest round trip for every departure date.                                               |
| Loop  | Runs the tool and sends the JSON back to the model.                                                                  |


Call `price_trip` once with the first date, last date, and days from the user request. If the user does not say how long the trip is, use `days=1`. Stop when the model returns a final answer in the output shape above, or after 15 steps.

Each step is logged as one line: step number, tool name, first date, last date, days, and the totals returned.

## Done when

A plain loop (`baseline.py`) and the agent both produce the winner above for this example. Then both pass these cases:

1. This example. The winner departs 2026-11-19 and returns 2026-11-20 at a total of $94.
2. The cheapest one-way day is not a complete trip. Nov 20 outbound is $42 and is skipped.
3. A tie on one leg uses the earlier departure. The Nov 17 outbound is train 175, so that round trip totals $163 and is not the winner.
4. A departure with no return trips is skipped.
5. When no departure date has both legs, the result is no trip found.
6. Two departure dates tie on total. The trip whose outbound train departs earlier wins, even though it is the later date. This is the one rule the model applies itself, not `price_trip`.

A case fails when the winner differs, a departure date is missing from the trace, or a reported price never appeared in a tool result.

Each case has its own folder. Set `FIXTURE_CASE` to the folder name before running `baseline.py` or `agent.py`.


| Case | Folder           | Expected winner                                                                                                                                    |
| ---- | ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `fixtures/case1` | Nov 19 → Nov 20, trains 175 and 94, $94. A copy of the main fixtures.                                                                              |
| 2    | `fixtures/case2` | Nov 17 → Nov 18, trains 175 and 194, $110. Nov 16 has a $25 outbound, but its only return on Nov 17 leaves at 16:10, so that departure is skipped. |
| 3    | `fixtures/case3` | Nov 18 → Nov 19, trains 175 and 174, $95. Each leg has two $50 or $45 trains; the earlier one wins.                                                |
| 4    | `fixtures/case4` | Nov 18 → Nov 19, trains 195 and 174, $120. Nov 18 returns no trips, so the $40 departure on Nov 17 is skipped.                                     |
| 5    | `fixtures/case5` | no trip found. Every return file is empty.                                                                                                         |
| 6    | `fixtures/case6` | Nov 19 → Nov 20, trains 175 and 94, $100. Nov 17 also totals $100, but its outbound leaves at 13:10 and Nov 19's leaves at 09:40.                  |


`python run_cases.py` runs every case through `baseline.py` and `agent.py`, each in its own process, and prints pass or fail. Add `--baseline-only` to skip the model.

## Order to build it in

1. Return fares only (WAS→MET fixtures, cheapest round trip), plus test cases.
2. Move all data into SQLite, with tools that query it.
3. Add hotels and the combined `find_cheapest_trips` tool.
4. Accept flexible natural-language requests and clarifying questions.
5. Optionally, a simple UI.

