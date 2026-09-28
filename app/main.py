"""
FastAPI entrypoint for the multi-agent PR review service.

POST /review runs the full pipeline (style + logic agents -> critic ->
summarizer) against a real GitHub PR, and optionally posts the result
as a comment on that PR.

Run locally:

    uvicorn app.main:app --reload

Then, e.g.:

    curl -X POST http://localhost:8000/review \\
        -H "Content-Type: application/json" \\
        -d '{"repo": "Lohithchandra8/ai-research-assistant", "pr_number": 1, "post": false}'
"""

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.github_client import format_diff_for_agents, get_pr_diff, post_pr_comment
from app.graph import build_review_graph

app = FastAPI(title="PR Review Agents")

# Build the graph once at startup rather than per-request — it's stateless
# and cheap to reuse across calls.
review_graph = build_review_graph()


class ReviewRequest(BaseModel):
    repo: str  # e.g. "owner/repo"
    pr_number: int
    post: bool = False  # if true, posts the review as a real PR comment


class ReviewResponse(BaseModel):
    review: str
    posted: bool
    comment_url: Optional[str] = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/review", response_model=ReviewResponse)
def review_pr(request: ReviewRequest) -> ReviewResponse:
    try:
        files = get_pr_diff(request.repo, request.pr_number)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Could not fetch PR diff: {e}")

    diff_text = format_diff_for_agents(files)

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

    comment_url = None
    if request.post:
        comment_url = post_pr_comment(request.repo, request.pr_number, review)

    return ReviewResponse(review=review, posted=request.post, comment_url=comment_url)