"""
Summarizer agent.

Takes the critic's verified findings and turns them into a clean,
human-readable review comment — the kind you'd actually want posted on
a real PR. This is the last agent in the pipeline; it doesn't evaluate
anything, just formats what the critic already verified.

Standalone test is via the full graph (app/graph.py), not this file
directly, since it needs critic output as input.
"""

import os

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

load_dotenv()

SUMMARIZER_SYSTEM_PROMPT = """You are formatting a code review for \
posting as a GitHub PR comment. You will be given a critic's verified \
findings about a diff (issues that already passed verification — do \
not second-guess them).

Turn them into a clean, professional PR review comment in Markdown:
- Start with a one-line overall summary (e.g. "Found 5 items worth \
addressing, mostly around naming and structure.")
- Group findings under clear headers if there's a natural grouping \
(e.g. "Style & Convention", "Logic & Security") — omit a section \
entirely if it has no findings
- For each finding: a short bullet with the file, the issue, and a \
brief suggested fix if one is obvious
- Keep the tone constructive and concise, like a helpful teammate, \
not a lecture
- End with a short closing line if there's nothing blocking (e.g. \
"No blocking issues — nice to have if you get a chance.") or flag \
clearly if something looks blocking

Do not include confidence scores or mention the review pipeline itself \
in the output — write it as a normal human-style PR review."""


def run_summarizer_agent(critic_output: str) -> str:
    """
    Sends the critic's verified findings to Claude for formatting into
    a clean PR review comment, and returns the formatted Markdown text.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is not set. Check your .env file.")

    llm = ChatAnthropic(model="claude-sonnet-4-5-20250929", temperature=0)

    messages = [
        ("system", SUMMARIZER_SYSTEM_PROMPT),
        ("human", f"Format this into a PR review comment:\n\n{critic_output}"),
    ]

    response = llm.invoke(messages)
    return response.content