# User-Agent Interaction API

FastAPI backend for user-to-agent interaction in the Policy Agent application with OpenRouter integration.

## Setup

1. Install dependencies:
```bash
pip install -e .
```

2. Create a `.env` file in this directory:
```
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

3. Run the server:
```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload --port 8001
```

The API will be available at `http://localhost:8001`

## API Endpoints

- `GET /` - Health check
- `POST /api/chat` - Chat with the agent
- `POST /api/extract-preferences` - Extract structured preferences from conversation
- `POST /api/format-output` - Format preferences into the final output string

## OpenRouter Setup

Get your API key from https://openrouter.ai and add it to your `.env` file.

## Note

This API runs on port 8001 to avoid conflicts with the main backend (which runs on port 8000 for agent-agent interactions).

