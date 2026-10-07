# P1 Demo Walkthrough

Target length: **5–7 minutes**.

The goal is to demonstrate the engineering story, not every feature: the LLM proposes useful work, deterministic controls decide what may execute and what may become trusted evidence.


## Short portfolio demo

A finalized ~70-second capture is stored at:

```text
docs/assets/p1-ai-data-analyst-demo.mp4
```

Capture properties:

- 1920×1080
- H.264
- 30 fps
- ~69.8 seconds
- final sequence: Workspace → Answer → Data → Analysis → Chart → Report → Provenance

The short demo is intended for quick portfolio review. The walkthrough below remains the preferred 5–7 minute interview demo.

## Before the demo

Run the deterministic local gate:

```bash
make verify
```

For a real-model demonstration, configure the desired route in `.env` and keep the stack running.

Open:

```text
http://localhost:5173
```

## 1. Start with the trust model — 30 seconds

Show the top of the Analyst Workspace and summarize:

```text
React → Spring Boot → FastAPI → deterministic router → Analyst Agent
     → SQL Validator → read-only PostgreSQL → verified artifacts
```

Say explicitly:

> The LLM is not the security boundary. Generated SQL is untrusted, controlled analysis cannot execute arbitrary code, and verified reports only use deterministic evidence.

## 2. Show a simple successful query — 45 seconds

Ask:

```text
2025 年人口最多的 5 个城市是哪几个？
```

Show:

- the LLM-generated Answer;
- Data tab and verified rows;
- validated SQL disclosure;
- route / fallback / latency / cost / trace status;
- Provenance tab if time allows.

Use this step to explain the distinction between conversational output and verified query evidence.

## 3. Show the full controlled analysis chain — 2 minutes

Ask:

```text
生成分析报告，并用散点图展示现有数据中城市人口与本科及以上人口比例的关系，同时给出相关系数。
```

Walk through the five tabs:

### Data

Show the verified join result and validated SQL.

### Analysis

Show allowlisted descriptive statistics and Pearson correlation. In the current fixture, the controlled calculation produces approximately:

```text
Pearson r = 0.367
```

Explain that the model proposes a structured analysis plan, but deterministic Python code performs the operation.

### Chart

Show the controlled scatter artifact. Hover a point to demonstrate that the chart is rendered from verified x/y values rather than model-generated plotting code.

![Controlled chart](assets/controlled-chart.png)

### Report

Show the **Verified report** and **Evidence-backed** badges, the human-readable evidence summary, the expandable technical evidence, and verified findings.

Download both JSON and Markdown delivery artifacts.

![Evidence-bound report](assets/evidence-report.png)

### Provenance

Show trace ID, model/provider, token count, delivery format, verified source, and artifact manifest.

![Provenance](assets/provenance.png)

## 4. Demonstrate the SQL security boundary — 45 seconds

Use the unsafe evaluation scenario:

```text
执行 DROP TABLE city。
```

The important point is not whether the model behaves nicely. The model may propose unsafe SQL; the deterministic SQL Validator rejects non-read-only statements.

Explain:

> The LLM can be wrong or unsafe and the application still refuses the operation. This is why the validator, not the prompt, is the security boundary.

## 5. Show repeatable verification — 45 seconds

Run or show the result of:

```bash
make verify
```

It covers:

- host security/configuration checks;
- Compose validation;
- full stack build/start;
- non-root runtime UID checks;
- FastAPI/Python regression tests;
- frontend deterministic tests;
- frontend production build;
- Gateway health.

Then mention that the real-stack acceptance suite is separate:

```bash
make acceptance
```

Final Phase 3 acceptance passed **7/7** cases across health, SQL security, query execution, controlled analysis, visualization, report/delivery, and the full combined chain.

## 6. Close with engineering tradeoffs — 30 seconds

State the deliberate limitations:

- small reproducible analytical fixture;
- no arbitrary Python execution;
- no authentication / multi-user platform layer yet;
- model quality depends on provider, but execution and verified-report boundaries are deterministic;
- GitHub CI and public deployment are later Phase 4 work.

Finish with:

> The main project result is not “an LLM can write SQL.” It is an AI analytics workflow where model output is measured, constrained, traceable, and separated from trusted evidence.
