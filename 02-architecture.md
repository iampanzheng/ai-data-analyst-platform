# 02 Architecture

## Target architecture

```text
[React]
   |
[Spring Boot]
   |  Auth / users / conversations / gateway
   v
[FastAPI]
   |
[Analyst Agent]
   |-- Schema Tool
   |-- SQL Tool
   |-- Python Tool
   |-- Chart Tool
   `-- Report Tool
        |
   [PostgreSQL]
```

## Design principle
The deterministic path is the foundation:

```text
request → validate → execute → evidence
```

The LLM is inserted later:

```text
question → schema retrieval → LLM SQL generation → SQL validation → execution → analysis → answer
```

## V1 agent choice
Use one analyst agent. Avoid multi-agent decomposition until evaluation shows a real need.

## Service boundaries

### Spring Boot
Business/API edge. Authentication, conversations, history, rate limiting, request correlation, AI gateway.

### FastAPI
AI execution service. Agent graph, tools, evaluation hooks, model routing.

### PostgreSQL
Application data plus analytics sample datasets.
