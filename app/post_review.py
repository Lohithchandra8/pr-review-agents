"""
Runs the full review pipeline against a real PR, and optionally posts
the result as a comment on that PR.

By default this is a DRY RUN — it only prints the review. You must pass
--post explicitly to actually comment on a real PR, since posting is a
visible, irreversible action.

Usage:

    # Dry run (just prints the review):
    python -m app.post_review Lohithchandra8/ai-research-assistant 1

    # Actually posts a comment on the real PR:
    python -m app.post_review Lohithchandra8/ai-research-assistant 1 --post
"""

import sys

from app.github_client import format_diff_for_agents, get_pr_diff, post_pr_comment
from app.graph import build_review_graph


def main():
    if len(sys.argv) < 3:
        print("Usage: python -m app.post_review owner/repo pr_number [--post]")
        sys.exit(1)

    repo_name = sys.argv[1]
    number = int(sys.argv[2])
    should_post = "--post" in sys.argv[3:]

    files = get_pr_diff(repo_name, number)
    diff_text = format_diff_for_agents(files)

    print(f"Running review pipeline on {repo_name} PR #{number}...\n")

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

    review = result["final_review"]

    print("=" * 60)
    print("REVIEW")
    print("=" * 60)
    print(review)
    print()

    if should_post:
        print("Posting comment to the real PR...")
        url = post_pr_comment(repo_name, number, review)
        print(f"Posted: {url}")
    else:
        print("Dry run only — nothing was posted. Re-run with --post to comment on the real PR.")


if __name__ == "__main__":
    main()