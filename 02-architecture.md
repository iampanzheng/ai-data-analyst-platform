# 02 Architecture

## Current runnable architecture

```text
[React :5173]
      |
[Spring Boot Gateway :8080]
      |  request correlation / API boundary
      v
[FastAPI AI Service :8000]
      |
[Analyst Agent v0.1]
      |-- Schema Tool
      |-- LLM Client
      `-- SQL Tool
              |
        [SQL Validator]
              |
      [PostgreSQL :5432]
```

## Analyst flow

```text
question
  ↓
schema metadata
  ↓
LLM SQL generation
  ↓
SQL candidate (untrusted)
  ↓
SQL validation
  ↓
read-only execution
  ↓
query evidence
  ↓
LLM answer
```

## Design principle

The deterministic foundation remains:

```text
request → validate → execute → evidence
```

The LLM is an interchangeable component, not the security boundary.

## V1 agent choice

Use one Analyst Agent. Avoid multi-agent decomposition until evaluation shows a concrete need.

## Service boundaries

### React

Portfolio/demo UI for natural-language questions, validated/manual SQL, query results, and available schema metadata.

### Spring Boot

Application/API edge and gateway. The current implementation proxies schema, query, health, and analyze calls and propagates `X-Trace-ID`. Authentication, users, conversations, and distributed rate limiting remain future platform work.

### FastAPI

AI execution service. Hosts schema/query APIs, Analyst Agent v0.1, LLM provider abstraction, SQL validation/execution, telemetry, and the evaluation entry point.

### PostgreSQL

Application metadata and analytics sample data. Analyst SQL is executed in a read-only transaction with timeout and row caps.

## Implemented tools vs planned tools

Implemented now:

```text
Schema Tool
SQL Tool
LLM Client
SQL Validator
```

Planned later:

```text
Python Analysis Tool
Chart Tool
Report Tool
```

## Model-provider boundary

```text
Analyst Agent
     ↓
  LLMClient
   ├── Mock provider
   └── OpenAI-compatible provider
```

The default Mock provider is deterministic and supports repeatable development/evaluation. Real-model comparison, routing, fallback, and cost control are later P1 work built on the same interface.
