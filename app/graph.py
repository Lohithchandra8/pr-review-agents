"""
LangGraph wiring for the multi-agent review pipeline.

Wires up: style agent + logic agent (parallel) -> critic agent (joins
both, filters findings) -> summarizer agent (formats final review).

Graph shape:

    START --> style --\
                        --> critic --> summarizer --> END
    START --> logic  --/

LangGraph waits for BOTH style and logic to complete before running
critic, since critic has incoming edges from both.

Standalone test (from the project root):

    python -m app.graph Lohithchandra8/ai-research-assistant 1
"""

import sys
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.critic_agent import run_critic_agent
from app.agents.logic_agent import run_logic_agent
from app.agents.style_agent import run_style_agent
from app.agents.summarizer_agent import run_summarizer_agent


class ReviewState(TypedDict):
    diff: str
    style_findings: str
    logic_findings: str
    critic_output: str
    final_review: str


def style_node(state: ReviewState) -> dict:
    findings = run_style_agent(state["diff"])
    return {"style_findings": findings}


def logic_node(state: ReviewState) -> dict:
    findings = run_logic_agent(state["diff"])
    return {"logic_findings": findings}


def critic_node(state: ReviewState) -> dict:
    output = run_critic_agent(
        diff_text=state["diff"],
        style_findings=state["style_findings"],
        logic_findings=state["logic_findings"],
    )
    return {"critic_output": output}


def summarizer_node(state: ReviewState) -> dict:
    review = run_summarizer_agent(state["critic_output"])
    return {"final_review": review}


def build_review_graph():
    """
    Builds and compiles the review graph: style and logic run in
    parallel from START, both feed into critic (a join), critic feeds
    into summarizer, summarizer feeds into END.
    """
    graph = StateGraph(ReviewState)

    graph.add_node("style", style_node)
    graph.add_node("logic", logic_node)
    graph.add_node("critic", critic_node)
    graph.add_node("summarizer", summarizer_node)

    graph.add_edge(START, "style")
    graph.add_edge(START, "logic")

    # Join: critic waits for both style and logic to finish
    graph.add_edge("style", "critic")
    graph.add_edge("logic", "critic")

    graph.add_edge("critic", "summarizer")
    graph.add_edge("summarizer", END)

    return graph.compile()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m app.graph owner/repo pr_number")
        sys.exit(1)

    from app.github_client import format_diff_for_agents, get_pr_diff

    repo_name = sys.argv[1]
    number = int(sys.argv[2])

    files = get_pr_diff(repo_name, number)
    diff_text = format_diff_for_agents(files)

    print(f"Running review graph on {repo_name} PR #{number}...\n")

    review_graph = build_review_graph()
    result = review_graph.invoke(
        {
            "diff": diff_text,
            "style_findings": "",
            "logic_findings": "",
            "critic_output": "",
            "final_review": "",
        }
    )

    print("=" * 60)
    print("RAW STYLE FINDINGS")
    print("=" * 60)
    print(result["style_findings"])
    print()
    print("=" * 60)
    print("RAW LOGIC/SECURITY FINDINGS")
    print("=" * 60)
    print(result["logic_findings"])
    print()
    print("=" * 60)
    print("CRITIC OUTPUT (verified + filtered)")
    print("=" * 60)
    print(result["critic_output"])
    print()
    print("=" * 60)
    print("FINAL REVIEW (ready to post)")
    print("=" * 60)
    print(result["final_review"])