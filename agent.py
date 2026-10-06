import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from tools import price_trip

load_dotenv(Path(__file__).resolve().parent / ".env")

MODEL = os.environ.get("OPENAI_MODEL", "gpt-6-luna")
MAX_STEPS = 15

SYSTEM_PROMPT = """
You find the cheapest 2-day round trip from MET (Metropark) to WAS
(Washington Union Station) and back, for 1 adult, by calling the price_trip tool.
Use only trains and prices that tool returns. Do not invent fares, and do not
add prices yourself. Use the total the tool returns.

Call price_trip once for every departure date from 2026-11-16 through 2026-11-20.
The tool sets the return to the next day, picks the train each way, and returns
the total.

The lowest total wins. On a tie, choose the trip whose outbound train departs
earlier. If those also match, choose the earlier departure date.
Skip a departure date whose total is null.
If every total is null, reply with exactly: no trip found

After every departure date has been priced, reply with exactly these lines:
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
reason:      Lowest 2-day trip from MET to WAS departing 2026-11-16 through 2026-11-20.
""".strip()

USER_REQUEST = "Find the cheapest 2-day round trip."


def trace(where: str, message: str) -> None:
    # print(f"[trace] agent.{where}: {message}")
    pass

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "price_trip",
            "description": (
                "Price one 2-day MET to WAS round trip. The return is the next day. "
                "Returns the cheapest eligible coach train each way and the total. "
                "A missing leg is null, and then total is null."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "depart_date": {
                        "type": "string",
                        "description": "Outbound date in YYYY-MM-DD form.",
                    },
                },
                "required": ["depart_date"],
                "additionalProperties": False,
            },
        },
    }
]


def returned_total(result: dict) -> str:
    total = result.get("total")
    if total is None:
        trace("returned_total", "total is none")
        return "none"
    trace("returned_total", f"total={total:g}")
    return f"{total:g}"


def call_price_trip(arguments: dict) -> dict:
    trace("call_price_trip", f"depart_date={arguments['depart_date']}")
    return price_trip(depart_date=arguments["depart_date"])


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
            if tool_call.function.name != "price_trip":
                trace("main", f"unknown tool {tool_call.function.name}")
                result = {"error": f"unknown tool: {tool_call.function.name}"}
            else:
                result = call_price_trip(arguments)
            print(
                f"step {step}: {tool_call.function.name} "
                f"depart_date={arguments.get('depart_date', '?')} "
                f"total={returned_total(result)}"
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )
            trace("main", f"appended the tool result for {arguments.get('depart_date', '?')}")

    trace("main", "reached the step limit")
    print("stopped: step limit")


if __name__ == "__main__":
    main()
