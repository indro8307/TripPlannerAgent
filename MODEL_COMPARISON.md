# Llama 3.1 8B vs Qwen3 8B in a small tool-using agent

I compared two open-source models of the same size on a small AI agent I built as a learning project. This post covers how I tested them, what the results were, and the surprises along the way, including two "model failures" that turned out to be my own bugs.

---

## The agent being tested

The agent finds the cheapest 2-day round trip by train from Metropark (MET) to Washington (WAS) over a range of departure dates. It uses invented sample fares stored in JSON files.

The work is split between code and model:

- **The tool**, `price_trip(first_date, last_date, days)`, prices every departure date in the range. For each date it picks the cheapest eligible train in each direction and adds the two fares. If either leg is missing, that date's total is `null`.
- **The model** reads the tool's results, skips dates with a `null` total, picks the lowest total, applies a tie rule, and writes the answer in a fixed 13-line format. If no date has a complete trip, it must reply exactly `no trip found`.

So the model's job is small but real: compare a handful of totals, handle missing data, apply a tie rule, and copy the details accurately.

## How I tested

**Six test cases**, each with its own fixture folder and a known correct answer:

| Case | What it tests |
|---|---|
| 1 | The main example |
| 2 | The cheapest outbound day has no return train, so it must be skipped |
| 3 | Two trains tie on price within one leg |
| 4 | One date has no return trains at all |
| 5 | No date has a complete trip; the answer is `no trip found` |
| 6 | Two dates tie on total; the earlier outbound time of day wins |

**A plain-code baseline**, `baseline.py`, solves every case without a model. `run_cases.py` runs each case through both the baseline and the agent and compares every field of the answer.

**Three runs per configuration**, because a model can pass once by luck. Each run covers all six cases, so one configuration is 18 attempts.

**Setup:** both models ran in [Ollama](https://ollama.com) on a free cloud T4 GPU, called through Ollama's OpenAI-compatible API. The agent code was identical for every model; only three environment variables changed. Times are average seconds per case. The first case of each run is a little slower because it includes loading the model.

## Results

| Model | Thinking | Prompt | Passed | Avg time per case |
|---|---|---|---|---|
| Llama 3.1 8B | n/a | old | 12/18 | not measured |
| Llama 3.1 8B | n/a | new | 11/18 | ~10 s |
| Qwen3 8B | on | old | 15/18 | not measured |
| Qwen3 8B | on | new | **18/18** | ~37 s |
| Qwen3 8B | off | new | 9/18 | ~10 s |

"New prompt" is the clarified tie rule (explained below). "Thinking off" means `reasoning_effort="none"`.

### By case (new prompt)

| Case | Llama 3.1 8B | Qwen3 8B, thinking | Qwen3 8B, no thinking |
|---|---|---|---|
| 1 Main example | 2/3 | 3/3 | 3/3 |
| 2 Skip a date with no return | 1/3 | 3/3 | 3/3 |
| 3 Tie within one leg | 3/3 | 3/3 | 3/3 |
| 4 A date with no returns | 2/3 | 3/3 | 0/3 |
| 5 No valid trip at all | **0/3** | 3/3 | 0/3 |
| 6 Tie between dates | 3/3 | 3/3 | 0/3 |

## How each model failed

The pass rates matter less than *how* each model got things wrong.

**Llama 3.1 8B: making things up.** In case 5 there's no valid trip, and the right answer is `no trip found`. Llama never gave it, in all six runs across both prompts. Instead it reported a trip, often inventing a return train, departure time, or price that existed nowhere in the data, and adding up its own total. One answer was a return on "train 175 at 11:20 for $82"; case 5 has no return trains at all. These answers looked completely believable, which is what makes this the most serious failure in the experiment.

Llama also twice wrote its tool call as plain text instead of actually calling the tool, and occasionally picked a higher total or swapped the outbound and return legs.

**Qwen3 8B without thinking: stopping at the first plausible trip.** It failed cases 4, 5, and 6 in exactly the same way in all three runs, each time reporting the first trip in the list instead of comparing them all. It didn't invent data. It simply didn't do the comparison.

**Qwen3 8B with thinking: no failures.** With the clarified prompt it passed all 18 attempts.

## A "model failure" that was my prompt's fault

My tie rule originally said:

> On a tie, choose the trip whose outbound train departs earlier.

I meant the earlier **time of day**. In case 6, Nov 17 (13:10) and Nov 19 (09:40) both total $100, so Nov 19 should win. But a train leaving Nov 17 at 13:10 really does depart earlier than one leaving Nov 19 at 09:40, because it's two days sooner. Qwen with thinking read my rule literally and chose Nov 17 every time: 0/3.

After I rewrote the rule to say "compare only the time of day (HH:MM), ignoring the date," Qwen passed case 6 every time. The fix helped Llama too, which went from 2/3 to 3/3.

There was also a bug in my test script: `run_cases.py` had the wrong expected winner for case 6, even though my spec and the baseline were right. When the baseline and the answer key disagree, check the key.

## Conclusions

1. **At 8B size, thinking is what made the agent reliable.** With the clarified prompt, Qwen3 8B with thinking passed all 18 attempts and never invented data. Without thinking it passed 9 of 18, no better than Llama.
2. **Reliability cost about 4× the time:** roughly 37 seconds per case with thinking, against 10 without.
3. **Llama 3.1 8B can't be trusted to say "nothing found."** For a planner, an answer that's confidently made up is worse than no answer.
4. **Check your instructions before blaming the model.** When a capable model makes the same "mistake" every time, the prompt may be ambiguous.
5. **Run tests more than once and change one thing at a time.** One run can pass by luck, and two changes at once hide which one mattered.

## What I didn't test

- **GPT**, the model I used during development, wasn't part of these repeated, timed runs.
- **Moving more work into the tool.** If `price_trip` returned only complete trips, already sorted best first, the model would just report the first one, or `no trip found` for an empty list. I expect that would let the fast, non-thinking models pass nearly every case. In other words, you can get reliability from model reasoning (slow) or from better tool design (fast). I've left that for another time.
- **Larger models.** Everything here is 8B parameters, which fits on a free T4 GPU.

## A note on `/no_think`

Before using `reasoning_effort="none"`, I first tried turning off Qwen's thinking by adding `/no_think` to the system prompt. Those runs took about as long as thinking mode (~39 s per case), so the setting most likely wasn't taking effect through Ollama's OpenAI-compatible API. I've left those runs out of the results.

---

*All fares and trips are invented sample data. Result files for every run are in this repository.*
