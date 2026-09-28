"""
Pulls a PR's diff from GitHub and normalizes it into a simple structure
the agents can consume later.

Usage (standalone test, from the project root, with GITHUB_TOKEN set in .env):

    python -m app.github_client owner/repo 12

This should print a clean list of changed files and their patches for
PR #12 in owner/repo. Confirm this works on 2-3 real PRs before moving
on to building any agents on top of it.
"""

import os
import sys
from dataclasses import dataclass
from typing import List, Optional

from dotenv import load_dotenv
from github import Github

load_dotenv()


@dataclass
class ChangedFile:
    filename: str
    status: str  # "added" | "modified" | "removed" | "renamed"
    patch: Optional[str]  # unified diff text; None for binary/no-patch files
    additions: int
    deletions: int


def get_pr_diff(repo_full_name: str, pr_number: int) -> List[ChangedFile]:
    """
    Fetch a PR's changed files from GitHub and return them as a clean
    list of ChangedFile objects.

    repo_full_name: e.g. "Lohithchandra8/ai-research-assistant"
    pr_number: the PR's number (not its internal id)
    """
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is not set. Copy .env.example to .env and fill it in.")

    gh = Github(token)
    repo = gh.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)

    changed_files = []
    for f in pr.get_files():
        changed_files.append(
            ChangedFile(
                filename=f.filename,
                status=f.status,
                patch=f.patch,  # can be None for large/binary files
                additions=f.additions,
                deletions=f.deletions,
            )
        )
    return changed_files


def format_diff_for_agents(files: List[ChangedFile]) -> str:
    """
    Turns the structured file list into a single text block that's easy
    to hand to an LLM prompt. Keep this simple for now — you can get
    fancier (e.g. truncating huge diffs) once the basic loop works.
    """
    parts = []
    for f in files:
        parts.append(f"### {f.filename} ({f.status}, +{f.additions}/-{f.deletions})")
        if f.patch:
            parts.append(f.patch)
        else:
            parts.append("[no text patch available — binary or too large]")
    return "\n\n".join(parts)


def post_pr_comment(repo_full_name: str, pr_number: int, comment_body: str) -> str:
    """
    Posts a comment on a PR. Returns the URL of the created comment.

    This is a real, visible, irreversible action on a real PR — call it
    deliberately, not as part of routine testing. The default flow in
    post_review.py requires an explicit --post flag for this reason.
    """
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is not set. Check your .env file.")

    gh = Github(token)
    repo = gh.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)

    issue_comment = pr.as_issue().create_comment(comment_body)
    return issue_comment.html_url


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m app.github_client owner/repo pr_number")
        sys.exit(1)

    repo_name = sys.argv[1]
    number = int(sys.argv[2])

    files = get_pr_diff(repo_name, number)
    print(f"Found {len(files)} changed file(s) in {repo_name} PR #{number}:\n")
    print(format_diff_for_agents(files))