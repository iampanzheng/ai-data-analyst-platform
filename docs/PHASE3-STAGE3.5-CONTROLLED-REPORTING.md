# Phase 3 — Stage 3.5 Controlled Reporting

Status: **CLOSED / verified baseline**

## Objective

Add a report-quality evidence packaging layer without allowing the model to invent a second factual surface or emit executable/report code.

## Architecture

```text
verified SQL result
+ optional controlled analysis_result
+ optional controlled chart_artifact
+ evidence-backed final_answer
        ↓
LLM report selection plan (JSON only; no factual prose)
        ↓
deterministic report validator / assembler
        ↓
report_artifact
        ↓
React Report Panel / JSON export
```

## Report planner contract

The model may only select existing verified artifacts:

```json
{
  "title": "short non-factual title",
  "include_summary": true,
  "include_query_evidence": true,
  "analysis_operation_indexes": [0],
  "include_chart": true
}
```

The model may not provide findings, evidence values, Markdown, HTML, code, SQL, Python, or JavaScript.

## Deterministic assembler

`report_artifact` contains:

- `title`
- `summary` (existing evidence-backed `final_answer`, if selected)
- `key_findings` copied deterministically from selected controlled-analysis operations
- `evidence` references bound to verified application artifacts
- `chart_refs`
- `source = verified_artifacts`

Analysis references are validated by array index. Chart references are rejected when no controlled chart artifact exists. Extra/freeform plan keys are rejected.

## Trigger

Controlled reporting is optional and only runs for explicit report intent, including `report`, `报告`, `分析报告`, `简报`, or `brief`.

Normal questions preserve the existing path and return `report_artifact = null`.

## Frontend

The Report Panel renders:

- summary
- deterministic verified findings
- evidence references
- JSON export of the controlled `report_artifact`

No server-side file generation or PDF dependency is introduced in this stage.

## Final verification

- Compose full pytest: PASS, 100%
- reporting unit tests: 5/5 PASS
- frontend production build: PASS (`vite v8.3.1`, 15 modules transformed)
- report-only remote smoke: PASS
- combined correlation + scatter + report remote smoke: PASS
- report evidence binding verified against query result, controlled analysis operation, and chart artifact
- deterministic report finding exactly matched `pearson_r = 0.36675379037073685` from controlled analysis
- `fallback_used = false` and `errors = []` on both remote report smokes

## Closeout

Stage 3.5 is frozen as the v1.0 closeout baseline. The next milestone is Stage 3.6 — Export / Deliverable Packaging.
