# Phase 3 — Stage 3.6: Export / Deliverable Packaging

## Objective

Package existing verified analysis artifacts into inert, user-downloadable JSON and Markdown deliverables.

Stage 3.6 does not perform new analysis and does not ask the LLM to author an export format. It packages only artifacts already accepted by earlier controlled stages.

## Trust boundary

Accepted sources:

- verified `query_result`
- controlled `analysis_result`
- controlled `chart_artifact`
- controlled `report_artifact` with `source = verified_artifacts`

Rejected:

- missing report artifact
- report artifacts from any other source
- arbitrary templates or scripts
- model-generated HTML/JavaScript/Python export code

## Delivery artifact

The API exposes a versioned `delivery_artifact` containing:

- format version
- title/source
- manifest and provenance
- controlled report snapshot
- evidence snapshot
- deterministic export filenames
- deterministic Markdown content

The JSON download contains the complete delivery artifact. Markdown is rendered from the same verified snapshot so both formats share one evidence base.

## V1 scope

Supported:
- JSON
- Markdown

Deferred:
- PDF
- DOCX/PPTX
- server-side template engines
- email/share workflows
- arbitrary user templates

These can be considered only after the deterministic export boundary is stable and evaluated.


## Evidence-bound summary hotfix (v0.1.1)

Closeout review of v0.1 found that the controlled report artifact still copied the conversational LLM `final_answer` into `report_artifact.summary`. Even though the SQL/analysis/chart evidence was verified, that free-form answer could contain unsupported source-attribution language and then be packaged under `source = verified_artifacts`.

The current boundary is stricter:

```text
LLM final_answer
  -> conversational answer only

verified query_result
+ selected controlled analysis_result operations
+ optional controlled chart_artifact
  -> deterministic report summary
  -> delivery artifact / Markdown
```

The report exposes `summary_source = deterministic_evidence`. The deterministic summary may state verified row/table/column metadata and exact controlled analysis/chart values, but it does not inherit model-authored provenance or external-source claims.
