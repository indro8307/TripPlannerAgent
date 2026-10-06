"""Run every fixture case through baseline.py and agent.py and print pass or fail.

tools.py reads FIXTURE_CASE once, when it is imported, so each run gets its own
Python process.

    python run_cases.py                  all cases, baseline and agent
    python run_cases.py --baseline-only  skip the agent (no OpenAI calls)
    python run_cases.py case6            only the named cases
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent

# (depart_date, total) of the expected winner, or None for "no trip found".
EXPECTED = {
    "case1": ("2026-11-19", "94"),
    "case2": ("2026-11-17", "110"),
    "case3": ("2026-11-18", "95"),
    "case4": ("2026-11-18", "120"),
    "case5": None,
    "case6": ("2026-11-17", "100"),
}

DEPARTURE_DATES = [f"2026-11-{day}" for day in range(16, 21)]

FIELDS = [
    "depart_date",
    "out_train",
    "out_depart",
    "out_arrive",
    "out_bucket",
    "out_price",
    "return_date",
    "ret_train",
    "ret_depart",
    "ret_arrive",
    "ret_bucket",
    "ret_price",
    "total",
]

NO_TRIP = "no trip found"


def run(script: str, case: str) -> str:
    env = {**os.environ, "FIXTURE_CASE": case}
    completed = subprocess.run(
        [sys.executable, script],
        cwd=PROJECT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout + completed.stderr


def normalize(value: str) -> str:
    value = value.strip().lstrip("$")
    try:
        return f"{float(value):g}"
    except ValueError:
        return value


def parse_answer(output: str) -> dict | str | None:
    """Return the answer fields, NO_TRIP, or None when no answer was found."""
    fields = {}
    for line in output.splitlines():
        line = line.strip().strip("`")
        if line.lower() == NO_TRIP:
            return NO_TRIP
        key, sep, value = line.partition(":")
        if sep and key.strip() in FIELDS:
            fields[key.strip()] = normalize(value)
    return fields or None


def priced_dates(output: str) -> set[str]:
    dates = set()
    for line in output.splitlines():
        if line.startswith("step ") and "depart_date=" in line:
            dates.add(line.split("depart_date=")[1].split()[0])
    return dates


def check_baseline(case: str, answer) -> list[str]:
    expected = EXPECTED[case]
    if expected is None:
        return [] if answer == NO_TRIP else [f"expected {NO_TRIP}, got {answer}"]
    if not isinstance(answer, dict):
        return [f"expected {expected}, got {answer}"]
    actual = (answer.get("depart_date"), answer.get("total"))
    return [] if actual == expected else [f"expected {expected}, got {actual}"]


def check_agent(baseline_answer, agent_answer, output: str) -> list[str]:
    problems = []
    if agent_answer is None:
        last = output.strip().splitlines()[-1:] or ["no output"]
        problems.append(f"no answer ({last[0]})")
    elif baseline_answer == NO_TRIP or agent_answer == NO_TRIP:
        if agent_answer != baseline_answer:
            problems.append(f"expected {baseline_answer}, got {agent_answer}")
    else:
        for field in FIELDS:
            if agent_answer.get(field) != baseline_answer.get(field):
                problems.append(
                    f"{field}: expected {baseline_answer.get(field)}, "
                    f"got {agent_answer.get(field)}"
                )
    missing = [day for day in DEPARTURE_DATES if day not in priced_dates(output)]
    if missing:
        problems.append(f"dates not priced: {', '.join(missing)}")
    return problems


def report(label: str, problems: list[str]) -> bool:
    if not problems:
        print(f"  {label}: pass")
        return True
    print(f"  {label}: FAIL")
    for problem in problems:
        print(f"    {problem}")
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cases", nargs="*", default=list(EXPECTED))
    parser.add_argument("--baseline-only", action="store_true")
    args = parser.parse_args()

    failures = 0
    for case in args.cases:
        if case not in EXPECTED:
            print(f"{case}: unknown case")
            failures += 1
            continue
        print(case)
        baseline_answer = parse_answer(run("baseline.py", case))
        if not report("baseline", check_baseline(case, baseline_answer)):
            failures += 1
        if args.baseline_only:
            continue
        agent_output = run("agent.py", case)
        agent_answer = parse_answer(agent_output)
        if not report("agent", check_agent(baseline_answer, agent_answer, agent_output)):
            failures += 1

    print("all passed" if failures == 0 else f"{failures} failed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
