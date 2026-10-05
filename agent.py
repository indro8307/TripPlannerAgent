import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from tools import search_fares

load_dotenv(Path(__file__).resolve().parent / ".env")

MODEL = os.environ.get("OPENAI_MODEL", "gpt-6-luna")
MAX_STEPS = 15

SYSTEM_PROMPT = """
You find the lowest Amtrak coach fare by calling the search_fares tool.
Use only prices that tool returns. Do not invent fares.

Search MET (Metropark) to WAS (Washington Union Station) for 1 adult.
Call search_fares once for every date from 2026-11-16 through 2026-11-20.

search_fares returns every saved trip for that date, including trips outside
the rules below. You decide which trips are eligible.

An eligible trip has bucket Saver, Value, or Flex, and depart is from 09:00
through 15:00 inclusive. A 15:05 departure is outside the window.
The lowest price wins. On a price tie, choose the earlier departure.
If the departure times also match, choose the earlier date.
Skip a date that has no eligible trip.
If no date has an eligible trip, reply with exactly: no fare found

After every date has been searched, reply with exactly these lines:
date:    YYYY-MM-DD
train:   NUMBER
depart:  HH:MM
arrive:  HH:MM
bucket:  Saver, Value, or Flex
price:   NUMBER
reason:  Lowest eligible fare from MET to WAS in 2026-11-16 through 2026-11-20.
""".strip()

USER_REQUEST = "Find the lowest eligible fare."


def trace(where: str, message: str) -> None:
    # print(f"[trace] agent.{where}: {message}")
    pass

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_fares",
            "description": (
                "Return saved Amtrak trips for one origin, destination, and date. "
                "Does not filter by departure time or fare bucket."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "Origin station code, such as MET.",
                    },
                    "destination": {
                        "type": "string",
                        "description": "Destination station code, such as WAS.",
                    },
                    "date": {
                        "type": "string",
                        "description": "Travel date in YYYY-MM-DD form.",
                    },
                    "adults": {
                        "type": "integer",
                        "description": "Number of adults.",
                    },
                },
                "required": ["origin", "destination", "date", "adults"],
                "additionalProperties": False,
            },
        },
    }
]


def lowest_returned_price(result: dict) -> str:
    prices = [trip["price"] for trip in result.get("trips", [])]
    if not prices:
        trace("lowest_returned_price", "no trips, lowest is none")
        return "none"
    lowest = f"{min(prices):g}"
    trace("lowest_returned_price", f"prices={prices} lowest={lowest}")
    return lowest


def call_search_fares(arguments: dict) -> dict:
    trace(
        "call_search_fares",
        f"origin={arguments['origin']} destination={arguments['destination']} "
        f"date={arguments['date']} adults={arguments['adults']}",
    )
    return search_fares(
        origin=arguments["origin"],
        destination=arguments["destination"],
        date=arguments["date"],
        adults=arguments["adults"],
    )


def main() -> None:
    trace("main", "start")
    if not os.environ.get("OPENAI_API_KEY"):
        trace("main", "OPENAI_API_KEY is missing")
        print("Set OPENAI_API_KEY in .env, then run this file again.")
        return

    trace("main", f"model={MODEL}, conversation has the rules and the user request")
    client = OpenAI()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_REQUEST},
    ]

    for step in range(1, MAX_STEPS + 1):
        trace("main", f"step {step}: sending the conversation to the model")
        # gpt-6-luna can call tools in Chat Completions only with reasoning off.
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            reasoning_effort="none",
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
            if tool_call.function.name != "search_fares":
                trace("main", f"unknown tool {tool_call.function.name}")
                result = {"error": f"unknown tool: {tool_call.function.name}"}
            else:
                result = call_search_fares(arguments)
            print(
                f"step {step}: {tool_call.function.name} "
                f"date={arguments.get('date', '?')} "
                f"lowest={lowest_returned_price(result)}"
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )
            trace("main", f"appended the tool result for {arguments.get('date', '?')}")

    trace("main", "reached the step limit")
    print("stopped: step limit")


if __name__ == "__main__":
    main()
