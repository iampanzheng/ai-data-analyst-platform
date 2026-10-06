# Phase 3 — Stage 3.7: Analyst Workspace / Frontend Integration Polish

## Why this stage exists

Stages 3.1–3.6 built strong backend and artifact contracts, but the frontend accumulated each capability as a separate vertical card. Stage 3.7 consolidates those capabilities into a single analyst workspace suitable for a portfolio demo while keeping the backend frozen.

## Design principles

1. **Trust boundaries stay visible.** Conversational LLM output is visually separated from verified data, controlled analysis, chart artifacts, report artifacts, and provenance.
2. **Progressive disclosure.** Manual SQL, schema, and provenance are available without dominating the primary workflow.
3. **One workspace, several artifact views.** Data, analysis, chart, report, and provenance are tabs over the same analysis run.
4. **No new dependency surface.** The implementation uses the existing React/Vite stack only.
5. **Responsive demo quality.** Desktop uses a control/results split; smaller screens collapse to a single column.

## Workspace structure

```text
Hero / trust model

┌────────────────────┬────────────────────────────────────────┐
│ Analysis request   │ LLM answer + execution status          │
│ routing/fallback   ├────────────────────────────────────────┤
│ manual SQL         │ Data | Analysis | Chart | Report | ... │
│ schema browser     │ current verified artifact view         │
└────────────────────┴────────────────────────────────────────┘
```

## Non-goals

- no backend API changes
- no new chart library
- no authentication/user management
- no dashboard persistence/history
- no multi-session workspace
- no PDF/Office export

Those should be separate later milestones if justified.


## Presentation polish v0.1.1

The first browser pass showed that the workspace structure was sound but the conversational answer still exposed raw Markdown syntax and verified findings were too implementation-oriented. v0.1.1 keeps the artifact contracts unchanged and adds a presentation layer:

- safe allowlisted Markdown rendering for the conversational answer
- human-readable correlation cards with rounded display precision
- presentation-friendly evidence summaries derived from verified report/delivery artifacts
- expandable technical evidence containing the exact deterministic summary and artifact labels
- raw values and complete precision remain available in Provenance and exported delivery artifacts

The renderer intentionally does not support raw HTML and never uses `dangerouslySetInnerHTML`.

## Visualization and presentation final polish v0.1.2

The second browser pass showed that the workspace and safe Markdown presentation were sound, while the chart remained closer to an implementation proof than a demo-quality analytical view. v0.1.2 stays frontend-only and closes that presentation gap:

- Data values are formatted for humans at render time only; raw evidence is untouched.
- Analysis cards expose friendly operation names while keeping deterministic operation payloads unchanged.
- SVG charts now show ticks, grids, friendly axis labels, and hover-accessible verified values.
- Scatter plots use a padded data domain instead of forcing the y-axis to zero, improving readability for bounded measures such as percentages.
- The frontend does not invent city/row labels for scatter points because the current controlled chart artifact provides only x/y coordinates.
- Report and Provenance presentation become more portfolio-friendly without modifying delivery payloads or verified source identifiers.
- Conversational answers are explicitly marked as LLM-generated to strengthen the visible trust boundary.

No raw HTML rendering, new chart dependency, backend contract change, or evidence transformation is introduced.

## v0.1.3 final presentation polish

The final polish pass remains display-only. Safe Markdown now supports inline emphasis without raw HTML, chart axes use rounded nice-scale ticks rather than arbitrary padded endpoints, and known bachelor-degree percentage aliases map to the same localized presentation label. Verified artifacts and exported values remain unchanged.

## v1.0 closeout

Stage 3.7 closed after v0.1.3 verification: backend regression passed, Vite production build passed, all five workspace tabs were browser-verified, delivery downloads remained functional, and the final presentation polish behaved as intended. No backend API or verified-artifact contract changed during Stage 3.7.
