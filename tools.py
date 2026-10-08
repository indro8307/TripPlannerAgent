import json
import os
from datetime import date, timedelta
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
case = os.environ.get("FIXTURE_CASE")
if case:
    FIXTURES = FIXTURES / case


def trace(where: str, message: str) -> None:
    # print(f"[trace] tools.{where}: {message}")
    pass


def search_fares(origin: str, destination: str, date: str, adults: int) -> dict:
    """Return saved fares for one origin, destination, and date.

    `adults` is accepted so the tool signature matches GOAL.md. Fixture files
    do not vary by party size yet.
    """
    trace(
        "search_fares",
        f"called with origin={origin} destination={destination} date={date} adults={adults}",
    )
    filename = f"{origin.lower()}_{destination.lower()}_{date}.json"
    path = FIXTURES / filename
    if not path.is_file():
        trace("search_fares", f"no fixture at {path.name}, returning no trips")
        return {"date": date, "trips": []}
    with path.open(encoding="utf-8") as handle:
        result = json.load(handle)
    trace("search_fares", f"loaded {path.name} with {len(result['trips'])} trips")
    return result


ORIGIN = "MET"
DESTINATION = "WAS"
ADULTS = 1
EARLIEST_DEPARTURE = "09:00"
LATEST_DEPARTURE = "15:00"
COACH_BUCKETS = {"Saver", "Value", "Flex"}


def is_eligible(trip: dict) -> bool:
    """A coach trip inside the departure window, matching baseline.py."""
    depart = trip["depart"]
    eligible = (
        trip["bucket"] in COACH_BUCKETS
        and EARLIEST_DEPARTURE <= depart <= LATEST_DEPARTURE
    )
    trace(
        "is_eligible",
        f"train {trip['train']} depart {depart} bucket {trip['bucket']} -> {eligible}",
    )
    return eligible


def cheapest_eligible(origin: str, destination: str, day: str) -> dict | None:
    """Lowest eligible fare for one direction and date.

    On a price tie, the earlier departure wins.
    """
    result = search_fares(origin, destination, day, ADULTS)
    best = None
    for trip in result["trips"]:
        if not is_eligible(trip):
            trace("cheapest_eligible", f"skipping train {trip['train']} on {day}")
            continue
        candidate = {
            "date": result["date"],
            "train": trip["train"],
            "depart": trip["depart"],
            "arrive": trip["arrive"],
            "bucket": trip["bucket"],
            "price": trip["price"],
        }
        if best is None or (candidate["price"], candidate["depart"]) < (
            best["price"],
            best["depart"],
        ):
            best = candidate
            trace(
                "cheapest_eligible",
                f"new best is train {best['train']} on {day} at {best['price']:g}",
            )
    if best is None:
        trace("cheapest_eligible", f"no eligible trip for {origin} to {destination} on {day}")
    return best


def price_one_departure(depart: date, days: int) -> dict:
    """Price one round trip that leaves on depart and returns `days` later.

    `days=1` means the return is the next day. A missing leg leaves total empty.
    """
    depart_date = depart.isoformat()
    return_date = (depart + timedelta(days=days)).isoformat()
    trace("price_one_departure", f"depart_date={depart_date} return_date={return_date}")
    outbound = cheapest_eligible(ORIGIN, DESTINATION, depart_date)
    return_trip = cheapest_eligible(DESTINATION, ORIGIN, return_date)
    if outbound is None or return_trip is None:
        total = None
        trace("price_one_departure", "missing a leg, total is empty")
    else:
        total = outbound["price"] + return_trip["price"]
        trace("price_one_departure", f"total={total:g}")
    return {
        "depart_date": depart_date,
        "return_date": return_date,
        "outbound": outbound,
        "return_trip": return_trip,
        "total": total,
    }


def price_trip(first_date: str, last_date: str, days: int = 1) -> dict:
    """Price the cheapest round trip for every departure from first_date through last_date.

    `days` is how many days later the return is. `days=1` (the default) means
    the next day. Each item in `trips` is one departure: both trains and the
    total, or null total when a leg is missing.
    """
    try:
        first = date.fromisoformat(first_date)
        last = date.fromisoformat(last_date)
    except (TypeError, ValueError):
        trace("price_trip", f"invalid dates first_date={first_date!r} last_date={last_date!r}")
        return {"error": "first_date and last_date must be YYYY-MM-DD"}

    if days is None:
        days = 1
    try:
        days = int(days)
    except (TypeError, ValueError):
        return {"error": "days must be an integer >= 1"}
    if days < 1:
        return {"error": "days must be an integer >= 1"}
    if last < first:
        return {"error": "last_date must be on or after first_date"}

    trips = []
    current = first
    while current <= last:
        trips.append(price_one_departure(current, days))
        current += timedelta(days=1)
    trace("price_trip", f"priced {len(trips)} departures from {first_date} through {last_date}")
    return {
        "first_date": first.isoformat(),
        "last_date": last.isoformat(),
        "days": days,
        "trips": trips,
    }