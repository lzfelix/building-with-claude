# Teaching Assistant

`src/teaching_assistant.py` turns a markdown file into an interactive quiz session. Drop your own notes into `resources/teaching-assistant/study-notes.md` and the script handles the rest: it extracts topics, lets you pick which ones to cover, then quizzes you with adaptive difficulty and a personalised section report at the end of each topic.

## How it works

The script runs as a linear workflow with five stages:

1. **Load and cache** — the study notes are read from disk and placed into the system prompt as a `cache_control`-marked block. Every subsequent API call in the session reuses that cached prefix, so you pay for the notes tokens only once regardless of how long the session runs.

2. **Topic extraction** — a single non-streaming call asks the model to list the main topics it finds in the notes. The response is parsed into a numbered list that the user can filter before the quiz begins.

3. **Topic loop** — for each selected topic, a fresh conversation is started (no cross-topic history) and the model is asked `QUESTIONS_PER_TOPIC` questions in sequence.

4. **Producer-grader per question** — each question turn is split into two calls: a streaming call that produces the question, and a non-streaming call that grades the answer. The grader returns one of three verdicts — `CORRECT` (1 pt), `PARTIAL` (0.5 pt), or `INCORRECT` (0 pt) — followed by one-sentence feedback. Partial credit is given when the answer is on the right track but missing specifics.

5. **Section report** — after all questions for a topic are answered, the model streams a personalised summary: which concepts landed, where the student fell short, and targeted review suggestions. If the score exceeds 80 % the suggestions are omitted.

### Selective memory

Each question text is appended to `TopicState.asked_questions` (capped at 120 chars) and injected into the next question request. This stops the model from re-asking the same concept within a topic without requiring any external state beyond a plain Python list.

### Adaptive difficulty

Difficulty starts at `medium` and shifts after each answer based on the running score for that topic: above 70 % it steps up, below 40 % it steps down. The current level is passed in the user message header so the model knows what register to pitch the question at.

### Prompt structure

The system prompt is a two-block list. The instructions block comes first (not cached); the notes block comes second and carries `cache_control: ephemeral`. This ordering ensures the large notes corpus is what gets cached while the instructions remain editable without invalidating the cache entry.

## Components

| Feature | Where it appears |
|---|---|
| Prompt caching | Study notes block with `cache_control: ephemeral` |
| Multi-turn chat | Per-topic conversation list, reset between topics |
| Message streaming | Question output and section report streamed to stdout |
| Linear workflow | Load → extract topics → select → quiz loop → summary |
| Producer-grader | `ask_question` produces, `evaluate_answer` grades |
| Selective memory | `TopicState.asked_questions` prevents concept repetition |

## Illustration

```
Analyzing study notes...

Topics found in study notes:
  1. Variables and Data Types
  2. Control Flow
  3. Functions
  4. Lists and Dictionaries

Enter topic numbers to study (comma-separated), or press Enter for all: 2

Let's study 1 topic(s): Control Flow
(Type 'exit' at any time to end the session)


──────────────────────────────────────────────────
Topic: Control Flow
──────────────────────────────────────────────────

Q1/5 [medium]: How does indentation function in Python's control flow structures, and what role does it play in defining code blocks?
Your answer: indentation is the delimiter for code bocks.

  → PARTIAL: You're right that indentation defines code blocks, but your answer is missing some
    specifics — the notes state that indentation should be 4 spaces or 1 tab, and it's worth noting
    that this replaces the use of braces ({}) that other languages use to delimit blocks.


Q2/5 [medium]: How does the `break` statement differ from the `continue` statement when used inside a loop?
Your answer: break means 'leave the loop'. Continue means 'skip to the next iteration'

  → CORRECT: That's exactly right — `break` exits the loop entirely while `continue` skips the rest
    of the current iteration and moves on to the next one.


Q3/5 [hard]: Given that a `while` loop and a `for` loop with `range()` can often achieve the same
result, compare the two approaches and explain in what situation you would prefer one over the other.
Your answer: while is better used when the stop condition is unclear beforehand. for is better when
we want to iterate over a collection linearly or perform an action a fixed number of times

  → CORRECT: Excellent answer — you've correctly identified that `while` loops are better suited for
    conditions that aren't known in advance, while `for` loops are ideal for iterating over iterables
    or when the number of iterations is predetermined.


Q4/5 [hard]: Given the following code, predict what will be printed and explain why the `elif` and
`else` branches are never reached: ...
Your answer: It will be printed "greater". elif and else never will be reached because the code flows
through the first matching branch

  → CORRECT: Exactly right — Python evaluates if/elif/else branches in order and executes only the
    first matching condition, so since x > 5 is True, the remaining branches are skipped entirely.


Q5/5 [hard]: Given the following code, predict the output and explain how `break` interacts with the
`for` loop and `range()`: ...
Your answer: 0 1 2 3 4. Break will move code execution to outside the innermost loop. Range will
create a linear sequence from 0 to 9, which will govern the for iterations.

  → CORRECT: Perfect answer — you correctly identified the output as 0 through 4, and accurately
    explained that `break` exits the innermost loop immediately when i == 5.


==================================================
Section report: Control Flow  |  Score: 4.5/5 (90%)
──────────────────────────────────────────────────
The student demonstrated strong understanding of loop control with `break` and `continue`,
`if/elif/else` branching logic, and the interaction between `for` loops, `range()`, and `break`.
They also showed excellent ability to reason about when to use `while` vs `for` loops. The only area
where the student fell slightly short was in describing indentation, where they captured the core
concept but omitted the specific details about 4 spaces or 1 tab and the contrast with brace-based
languages. Overall, a very strong performance across all difficulty levels.
==================================================

##################################################
Session complete! Final summary:
  Control Flow: 4.5/5 (90%)

Overall: 4.5/5 (90%)
##################################################
```

## Improvements

**Structured grading output.** The evaluator currently relies on the model starting its response with `CORRECT`, `PARTIAL`, or `INCORRECT`. This works well in practice but is fragile if the model adds a preamble. Switching to a tool call with a fixed schema (`verdict`, `feedback`) would make parsing deterministic.

**Persistent sessions.** The session state lives in memory only. Serialising `TopicState` to a file would let the user resume a session later or compare results across multiple attempts on the same notes.

**Configurable question count.** `QUESTIONS_PER_TOPIC` is a module-level constant. Exposing it as a CLI argument (`argparse`) or an interactive prompt at session start would make the script more flexible without changing the code.

**Richer difficulty rubric.** The current rubric gives the model three levels with brief descriptions. Adding one or two example questions per level would give the model a clearer target, especially for non-technical subject matter where "synthesis" questions are less obvious.

**Overall summary report.** The final summary is a plain score table. Applying the same producer pattern used for section reports — asking the model to synthesise a short overall assessment — would make the end-of-session feedback as useful as the per-topic one.
