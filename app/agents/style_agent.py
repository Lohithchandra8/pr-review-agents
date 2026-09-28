"""
Style/convention agent.

Takes formatted diff text (from github_client.format_diff_for_agents) and
asks Claude to flag style/convention issues: naming, formatting, unclear
code, missed docstrings, etc. This agent does NOT judge logic or security
issues — that's the next agent's job. Keeping agents narrowly scoped is
what makes the later critic agent's job possible.

Standalone test (from the project root, with ANTHROPIC_API_KEY in .env):

    python -m app.agents.style_agent Lohithchandra8/ai-research-assistant 1
"""

import os
import sys

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

load_dotenv()

STYLE_SYSTEM_PROMPT = """You are a code style reviewer. You review diffs \
for STYLE AND CONVENTION issues only — not logic, not security, not bugs.

Look for: unclear naming, inconsistent formatting, missing docstrings/\
comments where the code isn't self-explanatory, overly long lines or \
functions, and violations of common conventions for the language shown.

For each diff you review, output a numbered list of findings. For each \
finding include:
- file: the filename
- issue: a one-sentence description of the style issue
- confidence: high, medium, or low

If you find nothing worth flagging, say exactly: "No style issues found."

Do not comment on anything outside style/convention — leave logic, \
security, and correctness entirely to other reviewers. Be concise; do \
not pad findings with unnecessary explanation."""


def run_style_agent(diff_text: str) -> str:
    """
    Sends the diff to Claude with the style-focused system prompt and
    returns the raw findings text.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is not set. Check your .env file.")

    llm = ChatAnthropic(model="claude-sonnet-4-5-20250929", temperature=0)

    messages = [
        ("system", STYLE_SYSTEM_PROMPT),
        ("human", f"Review this diff:\n\n{diff_text}"),
    ]

    response = llm.invoke(messages)
    return response.content


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m app.agents.style_agent owner/repo pr_number")
        sys.exit(1)

    # Reuse the diff puller you already tested
    from app.github_client import format_diff_for_agents, get_pr_diff

    repo_name = sys.argv[1]
    number = int(sys.argv[2])

    files = get_pr_diff(repo_name, number)
    diff_text = format_diff_for_agents(files)

    print(f"Running style agent on {repo_name} PR #{number}...\n")
    findings = run_style_agent(diff_text)
    print(findings)