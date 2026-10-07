# GitHub Repository Metadata — P1 AI Data Analyst Platform

This file prepares the public repository metadata for Stage 4.4. It does **not** require the repository to be published yet.

## Recommended repository name

```text
ai-data-analyst-platform
```

Alternative if the portfolio uses a numbered naming convention:

```text
p1-ai-data-analyst
```

Prefer the descriptive name unless the surrounding portfolio repository already explains the P1 numbering.

## GitHub About description

Recommended concise description:

> Evidence-backed AI Data Analyst with validated SQL, controlled analytics, deterministic reporting, model routing/evaluation, and production-oriented security boundaries.

Shorter fallback:

> Production-oriented AI Data Analyst with validated SQL, controlled analytics, evidence-bound reporting, and model evaluation.

## Suggested topics

Use a focused set rather than maximizing topic count:

```text
ai-engineering
llm
text-to-sql
fastapi
spring-boot
react
postgresql
docker
sql-security
llm-evaluation
observability
portfolio-project
```

Optional topics if GitHub search positioning benefits from them:

```text
ollama
groq
vite
python
java
```

## Website field

Leave empty until Stage 4.5 has a stable public deployment URL.

Do not point the Website field at localhost, a temporary tunnel, or an unstable preview environment.

## README opening order

The public README should preserve this order:

1. project name + one-sentence engineering premise;
2. primary Analyst Workspace screenshot;
3. why the project exists / trust model;
4. current architecture;
5. implemented capabilities;
6. demo surfaces;
7. trust boundaries;
8. stack + quick start;
9. measured evaluation / acceptance;
10. limitations and project status.

This ordering is intentional: first establish product value, then engineering depth, then evidence.

## Repository social-preview guidance

If a social-preview image is added later, it should contain only:

```text
AI Data Analyst
Evidence-backed LLM analytics
Validated SQL · Controlled Analysis · Provenance
```

Use a clean crop of the actual Analyst Workspace or a simple architectural motif. Do not imply production traffic, customers, or deployment scale that has not been demonstrated.

## Public-claim guardrails

Safe claims:

- production-oriented;
- production-readiness engineering;
- evidence-backed;
- deterministic security / reporting boundaries;
- measured model comparison;
- repeatable local verification;
- end-to-end acceptance coverage.

Avoid until Stage 4.5 provides evidence:

- production deployment serving users;
- enterprise-ready;
- horizontally scalable production system;
- high availability;
- production SLA;
- real customer adoption.

## First-publication checklist for Stage 4.4

Before creating the GitHub repository:

- [ ] Stage 4.3 is CLOSED.
- [ ] README renders correctly in GitHub-flavored Markdown.
- [ ] Mermaid architecture renders correctly.
- [ ] All screenshot links resolve.
- [ ] No `.env`, API keys, credentials, generated archives, or local caches are tracked.
- [ ] `make verify` passes from the intended final local branch.
- [ ] `make publish-check` passes, including full Git-history scanning.
- [ ] Git history has been reviewed for accidentally committed secrets or oversized artifacts.
- [ ] Repository description and topics are set from this file.
- [ ] Default branch name and visibility are chosen deliberately.
- [ ] Stage tags intended for publication are present.

Stage 4.4 owns the actual repository creation, first push, and CI configuration. Follow [`GITHUB-PUBLISHING.md`](GITHUB-PUBLISHING.md) for the prepared first-publication procedure.
