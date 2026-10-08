import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

import config
from tools import price_trip

load_dotenv(Path(__file__).resolve().parent / ".env")

MODEL = os.environ.get("OPENAI_MODEL", "gpt-6-luna")
MAX_STEPS = 15

SYSTEM_PROMPT = """
You find the cheapest round trip from MET (Metropark) to WAS
(Washington Union Station) and back, for 1 adult, by calling the price_trip tool.
Use only trains and prices that tool returns. Do not invent fares, and do not
add prices yourself. Use the totals the tool returns.

Read first_date, last_date, and days from the user message.
first_date and last_date are outbound dates in YYYY-MM-DD form.
days is how many days later the return is. days=1 means the return is the next
day. If the user does not say how long the trip is, use days=1.
Call price_trip once with those three values. Do not invent dates.

The lowest total wins. On a tie, choose the trip whose outbound train departs
earlier. If those also match, choose the earlier departure date.
Skip a departure date whose total is null.
If every total is null, reply with exactly: no trip found

After the tool returns, reply with exactly these lines:
depart_date: YYYY-MM-DD
out_train:   NUMBER
out_depart:  HH:MM
out_arrive:  HH:MM
out_bucket:  Saver, Value, or Flex
out_price:   NUMBER
return_date: YYYY-MM-DD
ret_train:   NUMBER
ret_depart:  HH:MM
ret_arrive:  HH:MM
ret_bucket:  Saver, Value, or Flex
ret_price:   NUMBER
total:       NUMBER
reason:      Lowest round trip from MET to WAS for the dates and duration the user asked for.
""".strip()


def trace(where: str, message: str) -> None:
    # print(f"[trace] agent.{where}: {message}")
    pass

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "price_trip",
            "description": (
                "Price MET to WAS round trips for every departure from first_date "
                "through last_date. days is how many days later the return is; "
                "days=1 means the next day and is the default. Each trip is the "
                "cheapest eligible coach train each way plus the total. A missing "
                "leg is null, and then total is null."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "first_date": {
                        "type": "string",
                        "description": "First outbound date in YYYY-MM-DD form.",
                    },
                    "last_date": {
                        "type": "string",
                        "description": "Last outbound date in YYYY-MM-DD form.",
                    },
                    "days": {
                        "type": "integer",
                        "description": (
                            "Days from outbound to return. 1 means the next day. "
                            "Omit to use 1."
                        ),
                    },
                },
                "required": ["first_date", "last_date"],
                "additionalProperties": False,
            },
        },
    }
]


def returned_totals(result: dict) -> str:
    if result.get("error"):
        return "error"
    trips = result.get("trips") or []
    parts = []
    for trip in trips:
        total = trip.get("total")
        total_text = "none" if total is None else f"{total:g}"
        parts.append(f"{trip.get('depart_date', '?')}={total_text}")
    summary = ",".join(parts) if parts else "none"
    trace("returned_totals", summary)
    return summary


def call_price_trip(arguments: dict) -> dict:
    try:
        first_date = arguments["first_date"]
        last_date = arguments["last_date"]
    except KeyError as exc:
        return {"error": f"missing argument: {exc.args[0]}"}
    days = arguments.get("days")
    if days is None:
        days = config.DEFAULT_DAYS
    trace("call_price_trip", f"first_date={first_date} last_date={last_date} days={days}")
    return price_trip(first_date=first_date, last_date=last_date, days=days)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find the cheapest MET–WAS round trip with the configured dates."
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
    parser.add_argument(
        "--prompt",
        help=(
            "User request sent to the model. Use this to ask for a longer trip "
            "in plain language. Overrides --first, --last, and --days."
        ),
    )
    return parser.parse_args()


def request_text(args: argparse.Namespace) -> str:
    if args.prompt:
        return args.prompt
    return config.user_request(args.first_date, args.last_date, args.days)


def main() -> None:
    trace("main", "start")
    args = parse_args()
    request = request_text(args)
    if not os.environ.get("OPENAI_API_KEY"):
        trace("main", "OPENAI_API_KEY is missing")
        print("Set OPENAI_API_KEY in .env, then run this file again.")
        return

    trace("main", f"model={MODEL}, conversation has the rules and the user request")
    client = OpenAI()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": request},
    ]

    for step in range(1, MAX_STEPS + 1):
        trace("main", f"step {step}: sending the conversation to the model")
        # gpt-6-luna can call tools in Chat Completions only with reasoning off.
        extra = {"reasoning_effort": "none"} if MODEL.startswith("gpt-6") else {}
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            **extra,
        )
        message = response.choices[0].message
        if not message.tool_calls:
            trace("main", "model returned a final answer")
            print(message.content)
            return

        trace("main", f"model requested {len(message.tool_calls)} tool call(s)")
        messages.append(message)
        for tool_call in message.tool_calls:
            arguments = json.loads(tool_call.function.arguments)
            trace("main", f"tool name={tool_call.function.name} arguments={arguments}")
            if tool_call.function.name != "price_trip":
                trace("main", f"unknown tool {tool_call.function.name}")
                result = {"error": f"unknown tool: {tool_call.function.name}"}
            else:
                result = call_price_trip(arguments)
            print(
                f"step {step}: {tool_call.function.name} "
                f"first_date={arguments.get('first_date', '?')} "
                f"last_date={arguments.get('last_date', '?')} "
                f"days={arguments.get('days', config.DEFAULT_DAYS)} "
                f"totals={returned_totals(result)}"
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )
            trace(
                "main",
                f"appended the tool result for {arguments.get('first_date', '?')} "
                f"through {arguments.get('last_date', '?')}",
            )

    trace("main", "reached the step limit")
    print("stopped: step limit")


if __name__ == "__main__":
    main()
