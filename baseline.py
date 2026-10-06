from datetime import date, timedelta

from tools import DESTINATION, ORIGIN, price_trip

FIRST_DATE = date(2026, 11, 16)
LAST_DATE = date(2026, 11, 20)


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


def beats(candidate: dict, current_best: dict) -> bool:
    """True when candidate should replace the current best trip."""
    candidate_key = (
        candidate["total"],
        candidate["outbound"]["depart"],
        candidate["depart_date"],
    )
    best_key = (
        current_best["total"],
        current_best["outbound"]["depart"],
        current_best["depart_date"],
    )
    wins = candidate_key < best_key
    trace(
        "beats",
        f"{candidate['depart_date']} at {candidate['total']:g} "
        f"against {current_best['depart_date']} at {current_best['total']:g} -> {wins}",
    )
    return wins


def find_cheapest_trip() -> dict | None:
    trace("find_cheapest_trip", "start")
    best = None
    for day in each_date(FIRST_DATE, LAST_DATE):
        trip = price_trip(day.isoformat())
        if trip["total"] is None:
            trace("find_cheapest_trip", f"skipping {day.isoformat()}, a leg is missing")
            continue
        if best is None or beats(trip, best):
            best = trip
            trace(
                "find_cheapest_trip",
                f"new best departs {best['depart_date']} at {best['total']:g}",
            )
    if best is None:
        trace("find_cheapest_trip", "no complete trip")
    return best


def main() -> None:
    trace("main", "start")
    best = find_cheapest_trip()
    if best is None:
        trace("main", "printing no trip found")
        print("no trip found")
        return
    out = best["outbound"]
    ret = best["return_trip"]
    trace("main", f"printing trip departing {best['depart_date']} at {best['total']:g}")
    print(f"depart_date: {best['depart_date']}")
    print(f"out_train:   {out['train']}")
    print(f"out_depart:  {out['depart']}")
    print(f"out_arrive:  {out['arrive']}")
    print(f"out_bucket:  {out['bucket']}")
    print(f"out_price:   {out['price']:g}")
    print(f"return_date: {best['return_date']}")
    print(f"ret_train:   {ret['train']}")
    print(f"ret_depart:  {ret['depart']}")
    print(f"ret_arrive:  {ret['arrive']}")
    print(f"ret_bucket:  {ret['bucket']}")
    print(f"ret_price:   {ret['price']:g}")
    print(f"total:       {best['total']:g}")
    print(
        "reason:      "
        f"Lowest 2-day trip from {ORIGIN} to {DESTINATION} departing "
        f"{FIRST_DATE.isoformat()} through {LAST_DATE.isoformat()}."
    )


if __name__ == "__main__":
    main()
