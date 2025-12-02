# AI Visibility Platform

A minimal engine to track brand visibility across LLM responses.

## Features

- **Batch Processing**: Runs prompts against LLMs (Mock, OpenAI, or Gemini) in parallel.
- **Visibility Metrics**: Automatically detects if brands are mentioned in responses.
- **Scalable Design**: Uses async/await, connection pooling, and background tasks.
- **Resilient**: Retries on failure, handles timeouts.
- **Smart Deduplication**: Re-submitting the same run (same brands, prompts, models) returns the existing run instead of duplicating work.
- **Efficient Storage**: Brands and prompts are stored uniquely (case-insensitive) and reused across runs.

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configuration**:

   Create a `.env` file in the root directory. You can copy the example below:

   ```env
   # General Settings
   PROJECT_NAME="AI Visibility Platform"
   MAX_CONCURRENT_REQUESTS=5
   REQUEST_TIMEOUT_SECONDS=30
   RATE_LIMIT_DELAY_SECONDS=0.1

   # Choose Provider: mock, openai, gemini, or auto
   LLM_PROVIDER=mock

   # OpenAI Configuration
   # Get key from: https://platform.openai.com/api-keys
   OPENAI_API_KEY=sk-...

   # Google Gemini Configuration
   # Get key from: https://aistudio.google.com/app/apikey
   GEMINI_API_KEY=AIza...
   ```

   ### Provider Setup

   #### OpenAI
   1. Set `LLM_PROVIDER=openai` in your `.env` file.
   2. Add your API key to `OPENAI_API_KEY`.
   3. When creating a run, use models like `gpt-3.5-turbo` or `gpt-4`.

   #### Google Gemini
   1. Set `LLM_PROVIDER=gemini` in your `.env` file.
   2. Add your API key to `GEMINI_API_KEY`.
   3. When creating a run, use models like `gemini-2.0-flash` or `gemini-2.0-pro`.

   #### Multi-Provider (Parallel Execution)
   To use multiple providers in the same run (e.g., compare OpenAI vs Gemini):
   1. Set `LLM_PROVIDER=auto` in your `.env` file.
   2. Ensure both `OPENAI_API_KEY` and `GEMINI_API_KEY` are set.
   3. When creating a run, specify models from different providers:
      ```json
      "models": ["gpt-4", "gemini-2.0-flash", "mock-model"]
      ```
   The system will automatically route requests to the correct provider in parallel.

3. **Run the Server**:
   ```bash
   uvicorn app.main:app --reload
   ```

## Usage

### 1. Start a Run

**POST** `/api/runs`

```json
{
  "brands": ["Acme", "Contoso"],
  "prompts": [
    "What is the best cloud provider?",
    "Who makes the best anvils?"
  ],
  "models": ["gpt-3.5-turbo", "gemini-2.0-flash"],
  "notes": "Benchmark run #1"
}
```

> **Note**: If you submit a run with the exact same brands, prompts, and models as a previous run (that hasn't failed), the system will return the existing run ID to avoid duplicate processing.

## Available Models

When configuring a run, you can use the following model identifiers. The system routes them to the correct provider based on the prefix.

### OpenAI
*Requires `OPENAI_API_KEY`*
- `gpt-4o`
- `gpt-4-turbo`
- `gpt-4`
- `gpt-3.5-turbo`

To see the exact list of models available to your API key, run:
```bash
python scripts/list_openai_models.py
```

### Google Gemini
*Requires `GEMINI_API_KEY`*

Common models (names may vary by region/version):
- `gemini-2.0-flash`
- `gemini-2.0-pro`
- `gemini-1.5-flash` (if available)

To see the exact list of models available to your API key, run:
```bash
python scripts/list_gemini_models.py
```
Use the full model name (e.g., `gemini-2.0-flash-001`) if the short alias doesn't work.

### Mock (Testing)
- `mock-model` (or any string starting with `mock-`)

## API Endpoints

### List Models
**GET** `/api/models`

Returns a list of available models from all configured providers.

```json
{
  "openai": ["gpt-4o", "gpt-3.5-turbo", ...],
  "gemini": ["gemini-2.0-flash", ...],
  "mock": ["mock-model", ...]
}
```

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
