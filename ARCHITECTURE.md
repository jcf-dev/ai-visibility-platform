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

