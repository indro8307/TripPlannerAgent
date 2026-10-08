import argparse

import config
from tools import DESTINATION, ORIGIN, price_trip


def trace(where: str, message: str) -> None:
    # print(f"[trace] baseline.{where}: {message}")
    pass


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


def find_cheapest_trip(first: str, last: str, trip_days: int) -> dict | None:
    trace("find_cheapest_trip", f"first={first} last={last} days={trip_days}")
    result = price_trip(first, last, trip_days)
    best = None
    for trip in result["trips"]:
        if trip["total"] is None:
            trace("find_cheapest_trip", f"skipping {trip['depart_date']}, a leg is missing")
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find the cheapest MET–WAS round trip without a model."
    )
    parser.add_argument(
        "--first",
        dest="first_date",
        help="First outbound date, YYYY-MM-DD. Default comes from TRIP_FIRST_DATE.",
    )
    parser.add_argument(
        "--last",
        dest="last_date",
        help="Last outbound date, YYYY-MM-DD. Default comes from TRIP_LAST_DATE.",
    )
    parser.add_argument(
        "--days",
        type=int,
        help="Days from outbound to return. 1 means the next day. Default 1.",
    )
    return parser.parse_args()


def main() -> None:
    trace("main", "start")
    args = parse_args()
    first = args.first_date or config.first_date()
    last = args.last_date or config.last_date()
    trip_days = config.days() if args.days is None else args.days
    best = find_cheapest_trip(first, last, trip_days)
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
        f"Lowest round trip from {ORIGIN} to {DESTINATION} departing "
        f"{first} through {last}, return {trip_days} day(s) later."
    )


if __name__ == "__main__":
    main()
