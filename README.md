# AI Visibility Platform

A minimal engine to track brand visibility across LLM responses.

## Features

- **Batch Processing**: Runs prompts against LLMs (Mock, OpenAI, or Gemini) in parallel.
- **Visibility Metrics**: Automatically detects if brands are mentioned in responses.
- **Scalable Design**: Uses async/await, connection pooling, and background tasks.
- **Resilient**: Retries on failure, handles timeouts.

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

## Available Models

When configuring a run, you can use the following model identifiers. The system routes them to the correct provider based on the prefix.

### OpenAI
*Requires `OPENAI_API_KEY`*
- `gpt-4o`
- `gpt-4-turbo`
- `gpt-4`
- `gpt-3.5-turbo`

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