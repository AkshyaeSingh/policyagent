# Running Both Frontends Simultaneously

## Setup

You can now run two separate frontends:

1. **Tinder-style Preferences Frontend** (Port 5173)
2. **Negotiation Visualization Frontend** (Port 5174)

## How to Run

### Terminal 1: User-Agent API (for preferences)
```bash
cd user-agent-api
uv run python main.py
# Runs on port 8001
```

### Terminal 2: Negotiation Backend
```bash
cd backend
uv run python app.py
# Runs on port 8002
```

### Terminal 3: Tinder Preferences Frontend
```bash
cd frontend
npm run dev
# Runs on port 5173
# Open http://localhost:5173
```

### Terminal 4: Negotiation Visualization Frontend
```bash
cd frontend
npm run dev:negotiation
# Runs on port 5174
# Opens http://localhost:5174/negotiation.html automatically
```

## Usage Flow

1. Complete the preference flow on port 5173
2. After preferences are captured, click "Start Negotiation"
3. The negotiation visualization will open on port 5174
4. Both windows can be viewed simultaneously!

## Direct Access

You can also access the negotiation visualization directly at:
- `http://localhost:5174/negotiation.html`
- Or with preferences: `http://localhost:5174/negotiation.html?preferences={json}`

