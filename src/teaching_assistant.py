from __future__ import annotations

import sys
from dataclasses import dataclass, field
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
4. When asked to evaluate an answer, start your response with CORRECT, PARTIAL, or INCORRECT \
   (in uppercase), followed by one or two sentences of feedback:
   - CORRECT: the answer is fully right; briefly confirm it
   - PARTIAL: the answer is on the right track but incomplete or imprecise; explain what is missing
   - INCORRECT: the answer is wrong; give a Socratic hint rather than revealing the full answer
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
    correct: float = 0.0
    asked: int = 0
    asked_questions: list[str] = field(default_factory=list)

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
) -> str:
    no_repeat = ""
    if state.asked_questions:
        prior = "\n".join(f"  - {q}" for q in state.asked_questions)
        no_repeat = f"\nDo not ask about the same concept as any of these previous questions:\n{prior}"

    context = (
        f"[Topic: {state.name} | Difficulty: {state.difficulty} | "
        f"Score so far: {state.correct:g}/{state.asked}]{no_repeat}\n\n"
        f"Ask me question {q_num} of {total} for this topic. "
        f"Difficulty: {state.difficulty}."
    )
    messages.add_message("user", conversation, context)

    print(f"\nQ{q_num}/{total} [{state.difficulty}]: ", end="", flush=True)
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

    question_text = "".join(buffer)
    messages.add_message("assistant", conversation, question_text)
    return question_text


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
    verdict = feedback.strip().upper()
    if verdict.startswith("CORRECT"):
        state.correct += 1
    elif verdict.startswith("PARTIAL"):
        state.correct += 0.5


def generate_topic_report(
    client: Anthropic,
    system_prompt: list[dict],
    conversation: list[MessageParam],
    state: TopicState,
) -> None:
    pct = state.score_pct
    suggestion_instruction = (
        "The student did very well — do NOT include improvement suggestions."
        if pct > 0.80
        else "Include concrete suggestions for what to review, referencing specific concepts from the study notes."
    )
    prompt = (
        f"The student has finished the '{state.name}' section. "
        f"Score: {state.correct:g}/{state.asked} ({pct:.0%}). "
        "Write a brief section report (3-5 sentences) covering:\n"
        "1. Which concepts the student demonstrated solid understanding of\n"
        "2. Which specific concepts they struggled with (based on incorrect or partial answers)\n"
        f"3. {suggestion_instruction}"
    )
    messages.add_message("user", conversation, prompt)

    bar = "=" * 50
    print(f"\n{bar}")
    print(f"Section report: {state.name}  |  Score: {state.correct:g}/{state.asked} ({pct:.0%})")
    print("─" * 50)
    with client.messages.stream(
        model=MODEL,
        max_tokens=512,
        system=system_prompt,
        messages=conversation,
    ) as stream:
        for chunk in stream.text_stream:
            print(chunk, end="", flush=True)
    print(f"\n{bar}")


def show_overall_summary(all_states: list[TopicState], exited_early: bool = False) -> None:
    bar = "#" * 50
    print(f"\n{bar}")
    print("Partial session summary:" if exited_early else "Session complete! Final summary:")
    total_correct = sum(s.correct for s in all_states)
    total_asked = sum(s.asked for s in all_states)
    for s in all_states:
        if s.asked > 0:
            print(f"  {s.name}: {s.correct:g}/{s.asked} ({s.score_pct:.0%})")
        else:
            print(f"  {s.name}: not attempted")
    if total_asked > 0:
        overall = total_correct / total_asked
        print(f"\nOverall: {total_correct:g}/{total_asked} ({overall:.0%})")
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
            question = ask_question(client, system_prompt, conversation, state, q_num, QUESTIONS_PER_TOPIC)
            state.asked_questions.append(question[:120])

            user_answer = input("Your answer: ").strip()
            if user_answer.lower() == "exit":
                exited_early = True
                break

            messages.add_message("user", conversation, user_answer)
            evaluate_answer(client, system_prompt, conversation, state)
            adjust_difficulty(state)

        if exited_early:
            break

        generate_topic_report(client, system_prompt, conversation, state)

    show_overall_summary(all_states, exited_early=exited_early)


if __name__ == "__main__":
    main()
