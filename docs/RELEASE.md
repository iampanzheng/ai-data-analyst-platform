# P1 v1.0.0 — Final Portfolio Release

**Status:** release candidate; publish only after gates pass.

## Highlights

- End-to-end natural language → validated SQL → read-only PostgreSQL → evidence-backed answer/report and deterministic delivery.
- Controlled descriptive statistics, Pearson correlation, percent change, and evidence-derived visualization.
- React Analyst Workspace: Data, Analysis, Chart, Report, Provenance.
- Deterministic route/fallback, evaluation harness, telemetry, and bounded model/tool interfaces.
- Production-oriented local Compose verification, structured redaction, loopback port binding, and non-root application containers.
- Public repository and deterministic GitHub Actions CI; MIT licensed.

## Verification evidence

- Stage 3.8 HTTP acceptance: **7/7 PASS** (historical verified run).
- Latest Stage 4.4 local `make repo-check`, `make publish-check`, `make verify`: **PASS**, user-provided output.
- First GitHub Actions push run: **PASS**, 1m34s (user-provided output).
- Release candidate MUST be revalidated from the final `v1.0.0` commit/tag before publishing. Do not present historical checks as a new release-specific run.

## Demo

[~70-second end-to-end application demo](assets/p1-ai-data-analyst-demo.mp4) — versioned repository asset. An additional copy should be attached as a GitHub Release asset. The release asset may be downloaded rather than played inline.

## Running

`cp .env.example .env && make verify` (Docker Compose and uv required). Default Mock mode does not require provider credentials.

## Limits / nonclaims

This is a self-hosted local portfolio reference release, **not a publicly hosted multi-tenant SaaS**. No public URL, authentication, tenant isolation, or production cloud SLA is claimed. The included curated fixture is not a general data warehouse. Real-provider functionality depends on external API access. Verification demonstrates bounded controls, not that arbitrary LLM prose is always correct.

## License

MIT — see root `LICENSE`.
