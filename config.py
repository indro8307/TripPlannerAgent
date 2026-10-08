"""Shared trip settings. Override with env vars or command-line flags.

TRIP_FIRST_DATE  first outbound date, YYYY-MM-DD (default 2026-11-16)
TRIP_LAST_DATE   last outbound date, YYYY-MM-DD (default 2026-11-20)
TRIP_DAYS        days from outbound to return. 1 means the next day (default 1)
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

DEFAULT_FIRST_DATE = "2026-11-16"
DEFAULT_LAST_DATE = "2026-11-20"
DEFAULT_DAYS = 1


def first_date() -> str:
    return os.environ.get("TRIP_FIRST_DATE", DEFAULT_FIRST_DATE)


def last_date() -> str:
    return os.environ.get("TRIP_LAST_DATE", DEFAULT_LAST_DATE)


def days() -> int:
    raw = os.environ.get("TRIP_DAYS", str(DEFAULT_DAYS))
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_DAYS
    return value if value >= 1 else DEFAULT_DAYS


def duration_phrase(trip_days: int) -> str:
    if trip_days == 1:
        return "a 1-night trip (return the next day)"
    return f"a {trip_days}-night trip (return {trip_days} days later)"


def user_request(
    first: str | None = None,
    last: str | None = None,
    trip_days: int | None = None,
) -> str:
    first = first or first_date()
    last = last or last_date()
    trip_days = days() if trip_days is None else trip_days
    return (
        f"Find the cheapest round trip from MET to WAS. "
        f"I can leave from {first} through {last}. "
        f"I want {duration_phrase(trip_days)}."
    )
