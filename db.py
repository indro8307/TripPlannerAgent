import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "trips.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS fares (
    id          INTEGER PRIMARY KEY,
    dataset     TEXT NOT NULL,
    origin      TEXT NOT NULL,
    destination TEXT NOT NULL,
    date        TEXT NOT NULL,
    train       TEXT NOT NULL,
    depart      TEXT NOT NULL,
    arrive      TEXT NOT NULL,
    bucket      TEXT NOT NULL,
    price       REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_fares_lookup
    ON fares (dataset, origin, destination, date);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # rows behave like dicts
    return conn