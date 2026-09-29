# Stage 2.4 Package

This package extends the Stage 2.3 frozen model-comparison baseline with the first deterministic routing layer.

## Included

- deterministic `auto` / `remote` / `local` routing
- Stage 2.3 evidence-backed remote default
- separate remote/local client configuration
- per-client `/no_think` behavior
- API route metadata
- Spring gateway passthrough
- React demo route selector
- structured route-selection logging
- routing policy JSON and design document
- routing regression tests

## Intentionally excluded

- automatic fallback
- circuit breaker
- provider health scoring
- dynamic cost budgets
- LLM-based route selection
- heuristic query-complexity routing

Those belong to Stage 2.5 or later and require separate measured validation.
