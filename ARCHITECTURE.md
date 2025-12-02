# Architecture & Design

## Overview

The AI Visibility Platform is designed as a lightweight, asynchronous service to evaluate brand presence in LLM outputs. It prioritizes **scalability**, **reliability**, and **simplicity**.

## Core Components

### 1. API Layer (FastAPI)
- **Role**: Entry point for users/systems.
- **Design**: Async endpoints that offload heavy processing to background tasks.
- **Why**: Ensures the API remains responsive even when triggering large batch jobs.

### 2. Orchestrator (Service Layer)
- **Role**: Manages the execution of runs.
- **Key Features**:
    - **Concurrency Control**: Uses `asyncio.Semaphore` to limit parallel LLM calls (Rate Limiting).
    - **Task Management**: Generates tasks for `(prompt, model)` pairs.
    - **Error Handling**: Catches exceptions per-task so one failure doesn't crash the run.

### 3. LLM Client (Adapter Pattern)
- **Role**: Interface to external LLM providers.
- **Design**: Protocol-based `LLMProvider` with `MockLLMProvider` and `OpenAILLMProvider`.
- **Resilience**: Uses `tenacity` for exponential backoff retries on network failures.

### 4. Data Layer (SQLAlchemy + SQLite)
- **Role**: Persistence.
- **Schema**:
    - `Run`: Top-level container.
    - `Brand` / `Prompt`: Configuration for a specific run (snapshot).
    - `Response`: The raw output and metadata.
    - `ResponseBrandMention`: Derived analysis data.
- **Why SQLite**: Zero-config, sufficient for the assignment. Easily swappable for Postgres via connection string.

## Systems Thinking: Scaling to 100k Prompts/Day

If this system had to handle 100k prompts/day across multiple models, here's what I'd change:

1.  **Queue-Based Architecture**: Replace the in-memory `asyncio` tasks with a durable job queue (e.g., Celery with Redis/RabbitMQ or AWS SQS). This ensures tasks persist across server restarts and allows independent scaling of workers.
2.  **Distributed Rate Limiting**: Move from a local semaphore to a distributed rate limiter (e.g., using Redis) to coordinate limits across multiple worker instances and respect strict provider quotas (TPM/RPM).
3.  **Database Optimization**:
    *   Use batch inserts for `Response` and `ResponseBrandMention` records instead of inserting one by one.
    *   Add database indexes on frequently queried fields (e.g., `run_id`, `created_at`) to speed up reporting.
    *   Consider a read replica for heavy reporting queries.
    *   Migrate from SQLite to **PostgreSQL** with connection pooling (PgBouncer) for high concurrency.
4.  **Observability**: Implement structured logging and metrics (Prometheus/Grafana) to track success rates, latency percentiles, and token usage per provider in real-time.
5.  **Cost Management**: Add a budget tracking layer to pause runs if they exceed a daily spend limit, as 100k prompts can get expensive quickly.
6.  **Data Pipeline**: For massive scale analysis, offload completed run data to a data warehouse (e.g., BigQuery, Snowflake) for complex analytics, keeping the operational DB lean.

## Current Reliability Features

- **Idempotency**: Runs are unique entities. Re-running the same config creates a new Run ID.
- **Retries**: Network glitches are handled by `tenacity` with exponential backoff.
- **Timeouts**: `httpx` timeouts ensure we don't hang forever.
- **Concurrency Control**: Uses `asyncio.Semaphore` to limit parallel LLM calls within a single instance.

## Trade-offs
- **Analysis**: Currently uses simple string matching. In production, this might need NLP or fuzzy matching to catch variations (e.g., "Acme Corp" vs "Acme").
- **Sync vs Async**: Fully async stack chosen for I/O bound nature of LLM calls.
