# Policy agent!

## The Core Problem
Traditional governance suffers from:

Low engagement: Policy consultations are boring, technical, and inaccessible

Poor representation: Only loud voices or special interests get heard

Preference falsification: People don't reveal true preferences due to social pressure

Aggregation problems: No good way to synthesize millions of individual preferences into coherent policy

## Solution

creates a parallel, transparent governance infrastructure. The tinder for Policy.

Accelerating democratic technology to outpace authoritarian tech adoption

Building resilient infrastructure that distributes power rather than concentrating it

Creating transparency tools that make governance manipulation harder

Empowering individual sovereignty through personal AI representatives


## Technical Architecture
### Phase 1: Preference Extraction

Gamified app with swipeable policy scenarios

Progressive disclosure (start simple, get more nuanced)

Contextual questions based on user's revealed preferences

Visual/story-based scenarios rather than abstract policy language

### Phase 2: Agent Representation

Each person's preferences encoded as a vector/embedding

Agents understand trade-offs and priority rankings

Can extrapolate to new issues based on value patterns

Maintains uncertainty bounds on preferences

### Phase 3: Multi-Agent Negotiation

Agents find Pareto-optimal solutions

Weighted by demographic representation

Can simulate coalitions and compromises

Transparent negotiation logs

### Phase 4: Policy Output

Clear policy recommendations with confidence scores

Minority reports showing dissenting clusters

Simulation of expected outcomes

Audit trail of how decision was reached

## Key Innovations for Demo

Preference Learning: Show how agent learns complex preferences from simple swipes

Visualization: Beautiful latent space visualization showing preference clusters

Negotiation Theater: Live visualization of agents negotiating

Outcome Simulation: Show predicted effects of different policies

## Quick Start

### User-Agent Interaction API Setup

1. Navigate to the user-agent-api directory:
```bash
cd user-agent-api
```

2. Install dependencies:
```bash
pip install -e .
```

3. Create a `.env` file with your OpenRouter API key:
```
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

4. Run the API server:
```bash
python main.py
```

The API will be available at `http://localhost:8001`

**Note:** The `backend` folder is reserved for agent-agent interactions and should not be modified.

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Usage

1. Enter participant name and role (e.g., "Alice", "Noise-Sensitive neighbor")
2. Start chatting with the agent about your preferences and concerns
3. Click "Extract Preferences" to generate structured output
4. The output will be formatted as shown in the example, ready to send to your coworker for agent-agent analysis

## Project Structure

- `backend/` - Reserved for agent-agent interactions (do not modify)
- `user-agent-api/` - User-to-agent interaction API with OpenRouter integration
- `frontend/` - React frontend for user interaction

### Output Format

The system outputs structured preferences in the format:
```
PARTICIPANTS:

Participant Name (Role):
  - preference_key_1: value_or_None
  - preference_key_2: value_or_None
```

Values can be:
- `float` for numeric values (e.g., `250000.0`, `60.0`)
- `str` for text/dates (e.g., `"2026-06-01"`, `"8am"`)
- `None` if mentioned but no specific value given


