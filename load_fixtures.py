import json
from pathlib import Path

from db import SCHEMA, connect

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def datasets():
    #yield "main", FIXTURES
    for folder in sorted(FIXTURES.glob("case*")):
        yield folder.name, folder


def main() -> None:
    conn = connect()
    conn.executescript("DROP TABLE IF EXISTS fares;" + SCHEMA)   # rebuild from scratch
    count = 0
    for name, folder in datasets():
        for path in sorted(folder.glob("*.json")):
            origin, destination, _ = path.stem.split("_")   # met_was_2026-11-16
            data = json.loads(path.read_text(encoding="utf-8"))
            for trip in data["trips"]:
                conn.execute(
                    "INSERT INTO fares (dataset, origin, destination, date, train,"
                    " depart, arrive, bucket, price) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (name, origin.upper(), destination.upper(), data["date"],
                     trip["train"], trip["depart"], trip["arrive"], trip["bucket"], trip["price"]),
                )
                count += 1
    conn.commit()
    conn.close()
    print(f"loaded {count} fares into {len(list(datasets()))} datasets")


if __name__ == "__main__":
    main()