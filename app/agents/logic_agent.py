"""
Logic/security agent.

Takes formatted diff text and asks Claude to flag logic bugs, edge cases,
and security concerns. This agent does NOT comment on style/naming/
formatting — that's the style agent's job. Keeping the two scopes separate
is what lets the critic agent later judge each finding cleanly.

Standalone test (from the project root, with ANTHROPIC_API_KEY in .env):

    python -m app.agents.logic_agent Lohithchandra8/ai-research-assistant 1
"""

import os
import sys

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

load_dotenv()

LOGIC_SYSTEM_PROMPT = """You are a code logic and security reviewer. You \
review diffs for BUGS, EDGE CASES, and SECURITY CONCERNS only — not \
style, not naming, not formatting.

Look for: unhandled exceptions, off-by-one errors, null/None handling \
gaps, race conditions, unsafe patterns (SQL injection, command \
injection, unsafe deserialization, hardcoded secrets), missing input \
validation, and logic that doesn't match what the code appears to \
intend.

For each diff you review, output a numbered list of findings. For each \
finding include:
- file: the filename
- issue: a one-sentence description of the bug/security concern
- severity: high, medium, or low
- confidence: high, medium, or low

If you find nothing worth flagging, say exactly: "No logic or security \
issues found."

Do not comment on style, naming, or formatting — leave that entirely to \
other reviewers. Be concise; do not pad findings with unnecessary \
explanation."""


def run_logic_agent(diff_text: str) -> str:
    """
    Sends the diff to Claude with the logic/security-focused system
    prompt and returns the raw findings text.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is not set. Check your .env file.")

    llm = ChatAnthropic(model="claude-sonnet-4-5-20250929", temperature=0)

    messages = [
        ("system", LOGIC_SYSTEM_PROMPT),
        ("human", f"Review this diff:\n\n{diff_text}"),
    ]

    response = llm.invoke(messages)
    return response.content


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m app.agents.logic_agent owner/repo pr_number")
        sys.exit(1)

    from app.github_client import format_diff_for_agents, get_pr_diff

    repo_name = sys.argv[1]
    number = int(sys.argv[2])

    files = get_pr_diff(repo_name, number)
    diff_text = format_diff_for_agents(files)

    print(f"Running logic agent on {repo_name} PR #{number}...\n")
    findings = run_logic_agent(diff_text)
    print(findings)