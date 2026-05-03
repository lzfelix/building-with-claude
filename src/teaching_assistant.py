from __future__ import annotations

import sys
from dataclasses import dataclass
from dotenv import load_dotenv
from anthropic import Anthropic
from anthropic.types import MessageParam

from helpers import messages


MODEL = "claude-sonnet-4-6"
QUESTIONS_PER_TOPIC = 5
DIFFICULTY_UP_THRESHOLD = 0.70
DIFFICULTY_DOWN_THRESHOLD = 0.40
DIFFICULTY_LEVELS = ["easy", "medium", "hard"]
STUDY_NOTES_PATH = "./resources/teaching-assistant/study-notes.md"

INSTRUCTIONS = """\
You are a strict teaching assistant. Your only knowledge base for this session is the study \
notes provided below inside <study_notes> tags. You must follow these rules at all times:

1. ONLY ask questions and give feedback that can be directly answered from the study notes.
2. If the student goes off-topic or asks about something not covered in the notes, respond \
   exactly: "That topic is outside our study material. Let's stay focused."
3. When asked to generate a question, produce EXACTLY ONE question and nothing else — no preamble, \
   no explanation, just the question.
4. When asked to evaluate an answer, start your response with CORRECT or INCORRECT (in uppercase), \
   followed by a single sentence of feedback. If incorrect, give a hint rather than the full answer.
5. Adjust question complexity based on the difficulty level stated in each request:
   - easy: definitional recall ("What is...?", "Name...")
   - medium: application and explanation ("How does...?", "Why...?")
   - hard: synthesis and comparison ("Compare...", "Given X, what would happen if...?")
6. Never reveal the answer to a question you just asked before the student has attempted it.\
"""


@dataclass
class TopicState:
    name: str
    difficulty: str = "medium"
    correct: int = 0
    asked: int = 0

    @property
    def score_pct(self) -> float:
        return self.correct / self.asked if self.asked else 0.0


def load_study_notes(path: str = STUDY_NOTES_PATH) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_system_prompt(notes: str) -> list[dict]:
    return [
        {"type": "text", "text": INSTRUCTIONS},
        {
            "type": "text",
            "text": f"<study_notes>\n{notes}\n</study_notes>",
            "cache_control": {"type": "ephemeral"},
        },
    ]


def extract_topics(client: Anthropic, system_prompt: list[dict]) -> list[str]:
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": (
                "List the main topics covered in the study notes. "
                "Return them as a numbered list, one topic per line, "
                "with no additional text. Example:\n1. Topic A\n2. Topic B"
            ),
        }],
    )
    return _parse_numbered_list(messages.text_from_message(response))


def _parse_numbered_list(text: str) -> list[str]:
    topics = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        # Strip leading numbering like "1. ", "1) ", "- ", "* "
        if line[0].isdigit() and len(line) > 2 and line[1] in ".):":
            line = line[2:].strip()
        elif line[:2] in ("- ", "* ", "• "):
            line = line[2:].strip()
        if line:
            topics.append(line)
    return topics


def select_topics(topics: list[str]) -> list[str]:
    print("\nTopics found in study notes:")
    for i, t in enumerate(topics, 1):
        print(f"  {i}. {t}")
    raw = input(
        "\nEnter topic numbers to study (comma-separated), or press Enter for all: "
    ).strip()
    if not raw:
        return topics
    selected = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(topics):
                selected.append(topics[idx])
    return selected if selected else topics


def adjust_difficulty(state: TopicState) -> None:
    pct = state.score_pct
    idx = DIFFICULTY_LEVELS.index(state.difficulty)
    if pct > DIFFICULTY_UP_THRESHOLD and idx < len(DIFFICULTY_LEVELS) - 1:
        state.difficulty = DIFFICULTY_LEVELS[idx + 1]
    elif pct < DIFFICULTY_DOWN_THRESHOLD and idx > 0:
        state.difficulty = DIFFICULTY_LEVELS[idx - 1]


def ask_question(
    client: Anthropic,
    system_prompt: list[dict],
    conversation: list[MessageParam],
    state: TopicState,
    q_num: int,
    total: int,
) -> None:
    context = (
        f"[Topic: {state.name} | Difficulty: {state.difficulty} | "
        f"Score so far: {state.correct}/{state.asked}]\n\n"
        f"Ask me question {q_num} of {total} for this topic. "
        f"Difficulty: {state.difficulty}."
    )
    messages.add_message("user", conversation, context)

    print(f"\nQ{q_num}/{total}: ", end="", flush=True)
    buffer: list[str] = []
    with client.messages.stream(
        model=MODEL,
        max_tokens=256,
        system=system_prompt,
        messages=conversation,
    ) as stream:
        for chunk in stream.text_stream:
            print(chunk, end="", flush=True)
            buffer.append(chunk)
    print()

    messages.add_message("assistant", conversation, "".join(buffer))


def evaluate_answer(
    client: Anthropic,
    system_prompt: list[dict],
    conversation: list[MessageParam],
    state: TopicState,
) -> None:
    # Combine answer + eval request into one user message (API requires alternating turns)
    eval_request = "Please evaluate my answer above."
    last_user_msg = conversation[-1]
    combined = f"{last_user_msg['content']}\n\n{eval_request}"
    conversation[-1] = {"role": "user", "content": combined}

    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        system=system_prompt,
        messages=conversation,
    )
    feedback = messages.text_from_message(response)
    messages.add_message("assistant", conversation, response)

    print(f"\n  → {feedback}\n")

    state.asked += 1
    if feedback.strip().upper().startswith("CORRECT"):
        state.correct += 1


def show_topic_report(state: TopicState) -> None:
    pct = state.score_pct
    bar = "=" * 50
    print(f"\n{bar}")
    print(f"Section report: {state.name}")
    print(f"Score: {state.correct}/{state.asked} ({pct:.0%})")
    if pct <= 0.80:
        print("Suggestion: Review the parts of this topic where you hesitated or answered incorrectly.")
    else:
        print("Great job on this section!")
    print(bar)


def show_overall_summary(all_states: list[TopicState], exited_early: bool = False) -> None:
    bar = "#" * 50
    print(f"\n{bar}")
    print("Partial session summary:" if exited_early else "Session complete! Final summary:")
    total_correct = sum(s.correct for s in all_states)
    total_asked = sum(s.asked for s in all_states)
    for s in all_states:
        if s.asked > 0:
            print(f"  {s.name}: {s.correct}/{s.asked} ({s.score_pct:.0%})")
        else:
            print(f"  {s.name}: not attempted")
    if total_asked > 0:
        overall = total_correct / total_asked
        print(f"\nOverall: {total_correct}/{total_asked} ({overall:.0%})")
    print(bar)


def main() -> None:
    load_dotenv("config.env")
    client = Anthropic()

    try:
        notes = load_study_notes()
    except FileNotFoundError:
        print(f"Error: study notes not found at {STUDY_NOTES_PATH}")
        sys.exit(1)

    system_prompt = build_system_prompt(notes)

    print("Analyzing study notes...")
    topics = extract_topics(client, system_prompt)
    if not topics:
        print("No topics found. Make sure your study notes have meaningful headings or sections.")
        sys.exit(1)

    selected = select_topics(topics)
    print(f"\nLet's study {len(selected)} topic(s): {', '.join(selected)}")
    print("(Type 'exit' at any time to end the session)\n")

    all_states: list[TopicState] = []
    exited_early = False

    for topic_name in selected:
        state = TopicState(name=topic_name)
        all_states.append(state)
        conversation: list[MessageParam] = []

        print(f"\n{'─' * 50}")
        print(f"Topic: {topic_name}")
        print("─" * 50)

        for q_num in range(1, QUESTIONS_PER_TOPIC + 1):
            ask_question(client, system_prompt, conversation, state, q_num, QUESTIONS_PER_TOPIC)

            user_answer = input("Your answer: ").strip()
            if user_answer.lower() == "exit":
                exited_early = True
                break

            messages.add_message("user", conversation, user_answer)
            evaluate_answer(client, system_prompt, conversation, state)
            adjust_difficulty(state)

        if exited_early:
            break

        show_topic_report(state)

    show_overall_summary(all_states, exited_early=exited_early)


if __name__ == "__main__":
    main()
