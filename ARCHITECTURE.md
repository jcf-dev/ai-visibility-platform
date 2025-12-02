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
    - `Run`: Top-level container with `input_hash` for deduplication.
    - `Brand` / `Prompt`: Shared entities with case-insensitive uniqueness (reused across runs).
    - `run_brands` / `run_prompts`: Many-to-many association tables.
    - `Response`: The raw output and metadata.
    - `ResponseBrandMention`: Derived analysis data.
- **Why SQLite**: Zero-config, sufficient for the assignment. Easily swappable for Postgres via connection string.

#### Schema Design: Many-to-Many Relationships
- **Brands and Prompts are Shared**: Instead of duplicating brand/prompt data per run, they are stored once and associated with multiple runs via junction tables.
- **Case-Insensitive Upsert**: The system uses `LOWER()` SQL function to match brands and prompts case-insensitively. "OpenAI", "openai", and "OPENAI" are treated as the same entity.
- **Benefits**: Reduced storage, better data integrity, enables historical analysis across runs.

