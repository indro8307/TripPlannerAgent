from datetime import date, timedelta

from tools import search_fares

ORIGIN = "MET"
DESTINATION = "WAS"
FIRST_DATE = date(2026, 11, 16)
LAST_DATE = date(2026, 11, 20)
ADULTS = 1
EARLIEST_DEPARTURE = "09:00"
LATEST_DEPARTURE = "15:00"
COACH_BUCKETS = {"Saver", "Value", "Flex"}


def trace(where: str, message: str) -> None:
    # print(f"[trace] baseline.{where}: {message}")
    pass


def each_date(first: date, last: date):
    trace("each_date", f"from {first.isoformat()} through {last.isoformat()}")
    current = first
    while current <= last:
        trace("each_date", f"yielding {current.isoformat()}")
        yield current
        current += timedelta(days=1)
    trace("each_date", "finished")


def is_eligible(trip: dict) -> bool:
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


def beats(candidate: dict, current_best: dict) -> bool:
    """True when candidate should replace the current best trip."""
    candidate_key = (candidate["price"], candidate["depart"], candidate["date"])
    best_key = (current_best["price"], current_best["depart"], current_best["date"])
    wins = candidate_key < best_key
    trace(
        "beats",
        f"train {candidate['train']} on {candidate['date']} at {candidate['price']:g} "
        f"against train {current_best['train']} on {current_best['date']} "
        f"at {current_best['price']:g} -> {wins}",
    )
    return wins


def find_lowest_fare() -> dict | None:
    trace("find_lowest_fare", "start")
    best = None
    for day in each_date(FIRST_DATE, LAST_DATE):
        trace("find_lowest_fare", f"searching {day.isoformat()}")
        result = search_fares(ORIGIN, DESTINATION, day.isoformat(), ADULTS)
        for trip in result["trips"]:
            if not is_eligible(trip):
                trace("find_lowest_fare", f"skipping train {trip['train']}")
                continue
            candidate = {**trip, "date": result["date"]}
            if best is None or beats(candidate, best):
                best = candidate
                trace(
                    "find_lowest_fare",
                    f"new best is train {best['train']} on {best['date']} at {best['price']:g}",
                )
    if best is None:
        trace("find_lowest_fare", "no eligible trip")
    return best


def main() -> None:
    trace("main", "start")
    best = find_lowest_fare()
    if best is None:
        trace("main", "printing no fare found")
        print("no fare found")
        return
    trace("main", f"printing train {best['train']} on {best['date']} at {best['price']:g}")
    print(f"date:    {best['date']}")
    print(f"train:   {best['train']}")
    print(f"depart:  {best['depart']}")
    print(f"arrive:  {best['arrive']}")
    print(f"bucket:  {best['bucket']}")
    print(f"price:   {best['price']:g}")
    print(
        "reason:  "
        f"Lowest eligible fare from {ORIGIN} to {DESTINATION} "
        f"in {FIRST_DATE.isoformat()} through {LAST_DATE.isoformat()}."
    )


if __name__ == "__main__":
    main()
