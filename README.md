# PR Review Agents

A multi-agent system that reviews GitHub pull requests: separate agents
check style and logic/security concerns, a critic agent filters out
hallucinated or low-confidence findings, and a summarizer produces a
clean, human-readable review.

Built with LangGraph, FastAPI, and the GitHub API.

## Status

🚧 Early scaffold — GitHub diff pulling is wired up; agents are not yet built.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# fill in GITHUB_TOKEN and ANTHROPIC_API_KEY in .env
```

## Try the diff puller

```bash
python -m app.github_client owner/repo 12
```

Replace `owner/repo` and `12` with a real repo and PR number (try one
of your own repos first).

## Run the API

```bash
uvicorn app.main:app --reload
```

Then check `http://localhost:8000/health`.

## Run with Docker

```bash
docker build -t pr-review-agents .
docker run -p 8000:8000 --env-file .env pr-review-agents
```

## Roadmap

- [x] Project scaffold + GitHub diff pulling
- [ ] Style/convention agent
- [ ] Logic/security agent + parallel graph wiring
- [ ] Critic/verifier agent
- [ ] Summarizer + GitHub comment posting
- [ ] Deployment (webhook or GitHub Action) + polish
