# Phase 4 / Stage 4.4 — GitHub Repository & CI

## Intent

Stage 4.4 converts the completed local Git repository into a publication-ready GitHub repository with deterministic CI. It does not add AI product capabilities.

## CI principle

GitHub Actions should orchestrate the same deterministic validation already used locally rather than reimplementing a second test matrix.

The workflow therefore installs `uv`, copies `.env.example` to an untracked `.env`, runs repository hygiene checks, and executes `make verify` against Docker Compose.

## Security decisions

- workflow permissions are `contents: read`;
- third-party actions are pinned to immutable commit SHAs;
- the workflow does not use `pull_request_target`;
- no LLM/provider secret is required;
- remote-model acceptance is not part of default CI;
- Compose resources are removed in an `always()` cleanup step;
- repository history gets an explicit pre-publication scan before the first public push.

The official `astral-sh/setup-uv` action is used to install uv. The selected workflow pins the action itself to a commit SHA and requests `latest-known` uv so its checksum is known to that action release.

## Publication hygiene

`scripts/repository_check.py` rejects:

- tracked `.env` files;
- tracked virtualenv, `node_modules`, `dist`, or Python cache output;
- tracked ZIP/TAR package artifacts;
- tracked files larger than 20 MiB;
- missing canonical public/demo assets;
- strong secret patterns such as private keys, GitHub/OpenAI/Groq/AWS/Google/Slack tokens.

`--history` additionally scans Git history for forbidden paths and strong secret patterns. It is specifically intended for the first public publication of this long-lived local repository.

## Final Stage 4.4 state

Stage 4.4 is CLOSED. The public repository is available at:

`https://github.com/iampanzheng/ai-data-analyst-platform`

Final evidence:

- local current-tree publication check: PASS;
- full Git-history publication check: PASS;
- deterministic local verification: PASS;
- initial `main` push: PASS;
- first GitHub Actions run: PASS in 1m 34s;
- public README/assets review: PASS;
- MIT License added.

The repository keeps `docs/assets/p1-ai-data-analyst-demo.mp4` as the canonical versioned demo. A temporary GitHub user-attachment URL created from an unsubmitted Issue was observed to return 404 anonymously, so Stage 4.4 does not depend on that mechanism. Stage 4.5 may publish the same MP4 as a GitHub Release asset.
