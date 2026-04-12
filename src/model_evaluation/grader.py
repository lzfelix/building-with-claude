import json

from anthropic import Anthropic

from helpers.prompt import run_prompt


def grade_by_model(client: Anthropic, test_case: dict) -> dict:
    eval_prompt = f"""
    You are an expert code reviewer. Evaluate this AI-generated solution.

    Task: {test_case['task']}
    Generated solution: {test_case['predicted_output']}
    Ground truth solution: {test_case['expected_output']}

    Provide your evaluation as a structured JSON object with:
    - "strengths": An array of 1-3 key strengths
    - "weaknesses": An array of 1-3 key areas for improvement
    - "reasoning": A concise explanation of your assessment and why not maximum grade was given, if applicable.
    - "score": A number between 1-10

    The generated solution does not need to match perfectly the ground truth
    to receive a high score, as there can be multiple valid approaches.
    Focus on the correctness, efficiency, and clarity of the generated solution.
    """

    model_output = run_prompt(client, eval_prompt, model="claude-haiku-4-5", assistant_prompt="```json", stop_sequences=["```"])

    evaluation_report = json.loads(model_output)
    return evaluation_report | test_case
