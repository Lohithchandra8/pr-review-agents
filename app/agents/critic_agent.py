"""
Critic/verifier agent.

This is the key differentiator of the project: it takes the raw findings
from the style and logic agents (plus the original diff) and judges each
one — is it actually present in the diff, is it a duplicate, is the
severity/confidence accurate — before anything gets surfaced to a human.

It logs BOTH what it kept and what it filtered out, since the filtered
list is the most interesting evidence that this agent is doing real work
(catching another agent's hallucination) rather than just passing
everything through.

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

For each finding, check:
1. Is the issue actually present in the diff? (Not hallucinated or \
misreading the code)
2. Is it a duplicate of another finding in the list?
3. Is the stated confidence/severity accurate, or should it be \
adjusted?

Output your response in exactly this format:

## Verified Findings
(a numbered list of findings that passed your check — keep the \
original file/issue text, adjust confidence if needed)

## Filtered Out
(a numbered list of findings you removed, each with a one-sentence \
reason why — e.g. "hallucinated: diff shows no such line", \
"duplicate of finding #2", "confidence overstated: minor stylistic \
preference, not an actual convention violation")

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