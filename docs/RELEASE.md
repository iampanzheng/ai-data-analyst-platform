# P1 v1.0.0 — Final Portfolio Release

**Status:** Released — v1.0.0 (Latest).

## Highlights

- End-to-end natural language → validated SQL → read-only PostgreSQL → evidence-backed answer/report and deterministic delivery.
- Controlled descriptive statistics, Pearson correlation, percent change, and evidence-derived visualization.
- React Analyst Workspace: Data, Analysis, Chart, Report, Provenance.
- Deterministic route/fallback, evaluation harness, telemetry, and bounded model/tool interfaces.
- Production-oriented local Compose verification, structured redaction, loopback port binding, and non-root application containers.
- Public repository and deterministic GitHub Actions CI; MIT licensed.

## Verification evidence

- Repository publication hygiene: **PASS**
- Release candidate static checks: **PASS**
- Local production verification: **PASS**
- End-to-end acceptance: **7/7 PASS**
- GitHub Actions CI on the final release commit: **PASS**

## Demo

[Download the ~70-second demo (MP4)](https://github.com/iampanzheng/ai-data-analyst-platform/releases/download/v1.0.0/p1-ai-data-analyst-demo.mp4)

The demo covers the complete workflow from natural-language analysis through validated SQL, controlled analytics, visualization, evidence-backed reporting, and provenance.

The MP4 is included as a downloadable GitHub Release asset and is also versioned at `docs/assets/p1-ai-data-analyst-demo.mp4`. GitHub's repository file viewer may not play the video inline.

## Running

`cp .env.example .env && make verify` (Docker Compose and uv required). Default Mock mode does not require provider credentials.

## Limits / nonclaims

This is a self-hosted local portfolio reference release, **not a publicly hosted multi-tenant SaaS**. No public URL, authentication, tenant isolation, or production cloud SLA is claimed. The included curated fixture is not a general data warehouse. Real-provider functionality depends on external API access. Verification demonstrates bounded controls, not that arbitrary LLM prose is always correct.

## License

MIT — see root `LICENSE`.
