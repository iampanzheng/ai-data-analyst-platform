# Stage 3.8 — End-to-End Acceptance

This suite verifies the already implemented P1 product path without adding new product behavior.

It exercises the running Spring Boot gateway / FastAPI / PostgreSQL / LLM stack through HTTP and checks stable contracts rather than exact natural-language wording.

## Coverage

- health / database availability
- SQL security rejection
- basic ranked query
- controlled descriptive statistics
- controlled chart artifact
- evidence-bound report + delivery package
- full query → analysis → chart → report → delivery chain

## Run

Start the normal stack first, then:

```bash
python -m acceptance.run
```

To run one case:

```bash
python -m acceptance.run --case ACC-007
```

Reports are written to:

```text
acceptance/results/acceptance-report.json
acceptance/results/acceptance-report.md
```

The acceptance suite intentionally avoids asserting exact LLM prose. It asserts verified artifacts, controlled operations, security outcomes, and delivery/provenance contracts.
