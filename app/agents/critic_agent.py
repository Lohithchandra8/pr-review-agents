"""
Critic/verifier agent.

This is the key differentiator of the project: it takes the raw findings
from the style and logic agents (plus the original diff) and judges each
one before anything gets surfaced to a human.

A finding is kept only if the critic can quote concrete evidence for it
from the diff. It logs BOTH what it kept and what it filtered out (with
reasons), since the filtered list is the clearest evidence that this
agent is doing real work rather than passing everything through.

Standalone test (from the project root, with ANTHROPIC_API_KEY in .env):

    python -m app.agents.critic_agent Lohithchandra8/ai-research-assistant 1
"""

import os
import sys

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

load_dotenv()

CRITIC_SYSTEM_PROMPT = """You are a critic reviewing another AI \
reviewer's findings about a code diff. You do NOT review the code \
yourself from scratch — you judge the findings you're given against \
the actual diff text.

Note on diff format: every added line in the diff starts with a \
leading + marker (and removed lines with -). That marker is part of \
the diff format, not the code. Ignore it when judging indentation or \
formatting.

A finding is kept ONLY if it passes every check below:
1. Evidence: you can quote a specific line or snippet from the diff \
that demonstrates the problem. If you cannot point to concrete text \
in the diff that shows the issue, reject it as unsupported. This \
applies to formatting claims (whitespace, indentation, file endings) \
as much as to logic claims.
2. No hedging: reject findings that only say something "appears", \
"seems", or "may" be a problem without a concrete demonstration.
3. Real convention: for style findings, the cited rule must be a \
widely accepted convention (for example PEP 8) and must actually say \
what the finding claims. Reject invented or misquoted rules, and \
purely subjective preferences.
4. No duplicates: reject a finding that repeats another one.
5. Accurate confidence: adjust the stated confidence if it is \
overstated.

Output your response in exactly this format:

## Verified Findings
(a numbered list of the findings that passed — keep the original \
file/issue text, adjust confidence if needed, and add a line \
"Evidence:" with the quoted snippet from the diff)

## Filtered Out
(a numbered list of the findings you removed, each with a \
one-sentence reason, for example "unsupported: no line in the diff \
shows the claimed problem", "misquoted rule: the convention does not \
say this", "duplicate of finding #2")

If nothing was filtered out, write "None — all findings verified" \
under Filtered Out. If nothing survives verification, write "None — \
no findings held up" under Verified Findings. Be concise and decisive; \
do not hedge."""


def run_critic_agent(diff_text: str, style_findings: str, logic_findings: str) -> str:
    """
    Sends the diff plus both agents' raw findings to Claude for
    verification, and returns the critic's structured output (verified
    findings + what was filtered out and why).
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is not set. Check your .env file.")

    llm = ChatAnthropic(model="claude-sonnet-4-5-20250929", temperature=0)

    combined_findings = (
        f"STYLE AGENT FINDINGS:\n{style_findings}\n\n"
        f"LOGIC/SECURITY AGENT FINDINGS:\n{logic_findings}"
    )

    messages = [
        ("system", CRITIC_SYSTEM_PROMPT),
        (
            "human",
            f"Here is the diff being reviewed:\n\n{diff_text}\n\n"
            f"Here are the findings to verify:\n\n{combined_findings}",
        ),
    ]

    response = llm.invoke(messages)
    return response.content


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m app.agents.critic_agent owner/repo pr_number")
        sys.exit(1)

    from app.agents.logic_agent import run_logic_agent
    from app.agents.style_agent import run_style_agent
    from app.github_client import format_diff_for_agents, get_pr_diff

    repo_name = sys.argv[1]
    number = int(sys.argv[2])

    files = get_pr_diff(repo_name, number)
    diff_text = format_diff_for_agents(files)

    print(f"Running full pipeline on {repo_name} PR #{number}...\n")

    print("Running style agent...")
    style_findings = run_style_agent(diff_text)

    print("Running logic agent...")
    logic_findings = run_logic_agent(diff_text)

    print("Running critic agent...\n")
    critic_output = run_critic_agent(diff_text, style_findings, logic_findings)

    print("=" * 60)
    print("CRITIC OUTPUT")
    print("=" * 60)
    print(critic_output)