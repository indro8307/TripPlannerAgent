"""Check price_trip against the hand-worked totals in GOAL.md.

Run with FIXTURE_CASE unset, so the main sample fixtures are used.
"""

import config
from tools import price_trip

EXPECTED = {
    "2026-11-16": ("2026-11-17", "93", "174", 137),
    "2026-11-17": ("2026-11-18", "175", "88", 163),
    "2026-11-18": ("2026-11-19", "87", "174", 158),
    "2026-11-19": ("2026-11-20", "175", "94", 94),
    "2026-11-20": ("2026-11-21", "93", None, None),
}


def leg_train(leg: dict | None) -> str | None:
    return None if leg is None else leg["train"]


def main() -> None:
    result = price_trip(
        config.DEFAULT_FIRST_DATE, config.DEFAULT_LAST_DATE, config.DEFAULT_DAYS
    )
    if "error" in result:
        print(f"FAIL  {result['error']}")
        return
    trips = {trip["depart_date"]: trip for trip in result["trips"]}
    failures = 0
    for depart_date, expected in EXPECTED.items():
        trip = trips.get(depart_date)
        if trip is None:
            failures += 1
            print(f"FAIL  {depart_date}: missing from result")
            continue
        actual = (
            trip["return_date"],
            leg_train(trip["outbound"]),
            leg_train(trip["return_trip"]),
            trip["total"],
        )
        if actual == expected:
            print(f"ok    {depart_date}")
        else:
            failures += 1
            print(f"FAIL  {depart_date}: expected {expected}, got {actual}")
    extra = set(trips) - set(EXPECTED)
    if extra:
        failures += 1
        print(f"FAIL  unexpected departures: {sorted(extra)}")
    print("all passed" if failures == 0 else f"{failures} failed")


if __name__ == "__main__":
    main()
