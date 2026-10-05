import json
import os
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
