# P1 Portfolio Positioning

## One-line project description

Built a production-oriented AI Data Analyst application spanning React, Spring Boot, FastAPI, PostgreSQL, provider-independent LLM integration, AST-based SQL security, observability, and deterministic evaluation.

## Resume bullets

- Designed an end-to-end AI analytics architecture using React, Java/Spring Boot, Python/FastAPI, and PostgreSQL, with a provider-independent LLM abstraction and explicit tool boundaries.
- Implemented an AST-based SQL security layer with schema/table allowlists, read-only execution, timeout/row limits, and structured rejection codes so model-generated SQL cannot directly reach the database.
- Built a reproducible 30-case evaluation harness covering SQL correctness, result correctness, answer checks, security rejection, latency, token usage, and estimated cost; established a deterministic Mock baseline before real-model comparison.
- Added trace propagation and structured JSON logging across the application path and verified the portfolio baseline with 51 Python tests, 5 Java tests, a live 30-case evaluation run, and browser smoke tests.

## Interview narrative

The project deliberately separates probabilistic intelligence from deterministic controls. The LLM proposes SQL; application policy decides whether it is safe; PostgreSQL returns evidence; evaluation measures whether the behavior is actually correct. The next phase uses the existing harness to compare real models and make routing/cost decisions from measurements rather than intuition.

## Important limitation to state explicitly

The current checked-in baseline uses a deterministic Mock provider. Do not describe the Mock correctness score as real LLM performance or claim production AI usage that has not been implemented.
