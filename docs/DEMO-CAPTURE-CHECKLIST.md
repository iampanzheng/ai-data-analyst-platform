# Demo Capture Checklist — P1 AI Data Analyst Platform

This checklist defines the final portfolio evidence to capture after the application is in its intended demo state.

The goal is to show the engineering story with the fewest high-signal assets possible.

## Capture principles

- Use the real application, not a mockup.
- Prefer one coherent run over stitching together unrelated states.
- Keep secrets, local paths, browser profiles, and unrelated tabs out of frame.
- Do not show `.env` contents or provider API keys.
- Keep the trust distinction visible: **LLM-generated Answer** vs **Verified artifacts**.
- Use a stable real-model route only when the environment is reliable; otherwise use the deterministic local baseline and clearly label it.

## Static screenshots for README

The repository should keep four primary screenshots.

### 1. Analyst Workspace

Must show:

- natural-language business question;
- LLM-generated Answer label;
- primary route / fallback status;
- Data / Analysis / Chart / Report / Provenance tabs;
- enough of the result to make the product immediately understandable.

Target file:

```text
docs/assets/analyst-workspace.png
```

### 2. Controlled Chart

Must show:

- human-readable axes;
- nice ticks / grid;
- controlled-chart badge;
- at least one tooltip if practical;
- chart generated from verified query evidence.

Target file:

```text
docs/assets/controlled-chart.png
```

### 3. Evidence-bound Report

Must show:

- Verified report;
- Evidence-backed label;
- evidence summary;
- technical evidence section;
- verified findings;
- deterministic JSON / Markdown download controls if visible.

Target file:

```text
docs/assets/evidence-report.png
```

### 4. Provenance

Must show:

- trace ID;
- model / provider;
- token count;
- delivery format;
- verified source;
- artifact manifest.

Target file:

```text
docs/assets/provenance.png
```

## Optional short demo video

Recommended length: **60–90 seconds** for a portfolio landing page or interview follow-up.

Suggested sequence:

```text
0–10s    Analyst Workspace + business question
10–25s   Run analysis / show Answer and route status
25–40s   Data + Analysis tabs
40–55s   Chart tab and tooltip
55–70s   Report tab + evidence-backed summary
70–80s   Provenance tab
80–90s   Unsafe SQL rejection or make verify evidence (optional)
```

Avoid long waits for a model response in the final edit. If recording a real remote route, capture a successful run and trim dead time rather than implying lower latency than actually measured.

## Long-form interview demo

Use [`DEMO.md`](DEMO.md) for the 5–7 minute walkthrough.

The high-signal sequence is:

1. explain the trust model;
2. run a normal verified query;
3. run the full analysis + chart + report scenario;
4. inspect provenance;
5. demonstrate unsafe SQL rejection;
6. show `make verify` / acceptance evidence;
7. close with known limitations and design tradeoffs.

## Final capture hygiene

Before saving assets:

- [ ] browser zoom is consistent;
- [ ] no API keys / secrets / personal bookmarks are visible;
- [ ] route/provider labels are intentional;
- [ ] trace IDs are acceptable to publish;
- [ ] no temporary error banners are visible;
- [ ] screenshot crop includes enough context to identify the feature;
- [ ] filenames match README references;
- [ ] large screenshots are resized/compressed without making text unreadable.

## What not to capture

Do not add screenshots of:

- raw `.env` files;
- provider dashboards containing keys or account details;
- repetitive terminal logs already summarized by acceptance reports;
- dozens of low-value UI states;
- mock screens that do not correspond to implemented behavior.

The four existing README screenshots plus one short video are sufficient for the final portfolio surface.
