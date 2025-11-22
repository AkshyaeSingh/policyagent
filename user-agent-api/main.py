from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import httpx
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = FastAPI(title="User-Agent Interaction API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

if not OPENROUTER_API_KEY:
    print("Warning: OPENROUTER_API_KEY not set in environment variables")


class UserMessage(BaseModel):
    message: str
    participant_name: Optional[str] = None
    role: Optional[str] = None
    conversation_history: Optional[List[Dict[str, str]]] = []


class PreferenceExtractionRequest(BaseModel):
    conversation_history: List[Dict[str, str]]
    participant_name: str
    role: str


class Preference(BaseModel):
    key: str
    value: Optional[Any]  # Can be str, float, or None
    value_type: str  # "str", "float", or "none"


class ParticipantPreferences(BaseModel):
    participant_name: str
    role: str
    preferences: Dict[str, Optional[Any]]


class PreferencesOutput(BaseModel):
    participants: List[ParticipantPreferences]


async def call_openrouter(messages: List[Dict[str, str]], model: str = "anthropic/claude-3.5-sonnet") -> str:
    """Call OpenRouter API"""
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenRouter API key not configured")
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://policyagent.local",
        "X-Title": "Policy Agent"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(OPENROUTER_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


@app.get("/")
async def root():
    return {"message": "User-Agent Interaction API", "status": "running"}


@app.post("/api/chat")
async def chat(user_message: UserMessage):
    """Handle user chat interaction with the agent"""
    try:
        # Build conversation context
        messages = []
        
        # System prompt for the agent
        system_prompt = """You are a helpful policy agent assistant. Your role is to engage in a natural conversation with users to understand their preferences and concerns about policy decisions.

Be conversational, empathetic, and ask clarifying questions to understand:
- What matters most to them
- Their constraints and requirements
- Their priorities and trade-offs
- Specific values they care about (costs, timelines, environmental factors, etc.)

Keep the conversation natural and don't be too formal. Ask follow-up questions to get specific numbers, dates, or requirements when relevant."""
        
        messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history
        for msg in user_message.conversation_history:
            messages.append(msg)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message.message})
        
        # Get response from OpenRouter
        response = await call_openrouter(messages)
        
        return {
            "response": response,
            "conversation_history": messages[1:] + [{"role": "assistant", "content": response}]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in chat: {str(e)}")


@app.post("/api/extract-preferences")
async def extract_preferences(request: PreferenceExtractionRequest):
    """Extract structured preferences from conversation history"""
    try:
        # Build prompt for preference extraction
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in request.conversation_history
        ])
        
        extraction_prompt = f"""You are analyzing a conversation between a user and a policy agent. Extract the user's preferences as structured key-value pairs.

Participant Name: {request.participant_name}
Role: {request.role}

Conversation:
{conversation_text}

Extract all preferences mentioned in the conversation. For each preference:
- Use descriptive, snake_case keys (e.g., "total_cost_under", "noise_level_below_db")
- Values should be:
  - Float for numeric values (e.g., 250000.0, 60.0)
  - String for text/dates (e.g., "2026-06-01", "8am")
  - None/null if mentioned but no specific value given

Output ONLY a valid JSON object with this exact structure:
{{
  "preferences": {{
    "preference_key_1": value_or_null,
    "preference_key_2": value_or_null
  }}
}}

Be thorough - extract all mentioned preferences, constraints, requirements, and priorities."""
        
        messages = [
            {"role": "system", "content": "You are a preference extraction system. Output only valid JSON."},
            {"role": "user", "content": extraction_prompt}
        ]
        
        response_text = await call_openrouter(messages, model="anthropic/claude-3.5-sonnet")
        
        # Parse JSON response
        # Try to extract JSON from response (in case it's wrapped in markdown)
        response_text = response_text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        try:
            extracted_data = json.loads(response_text)
            preferences = extracted_data.get("preferences", {})
        except json.JSONDecodeError:
            # Fallback: try to parse as direct JSON object
            try:
                preferences = json.loads(response_text)
            except:
                raise HTTPException(status_code=500, detail="Failed to parse preference extraction response")
        
        # Format output
        participant_prefs = ParticipantPreferences(
            participant_name=request.participant_name,
            role=request.role,
            preferences=preferences
        )
        
        return PreferencesOutput(participants=[participant_prefs])
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting preferences: {str(e)}")


@app.post("/api/format-output")
async def format_output(preferences: PreferencesOutput):
    """Format preferences into the final output string format"""
    try:
        output_lines = ["PARTICIPANTS:\n"]
        
        for participant in preferences.participants:
            output_lines.append(f"\n{participant.participant_name} ({participant.role}):\n")
            
            for key, value in participant.preferences.items():
                if value is None:
                    output_lines.append(f"  - {key}: None")
                elif isinstance(value, (int, float)):
                    output_lines.append(f"  - {key}: {float(value)}")
                else:
                    output_lines.append(f"  - {key}: {value}")
        
        formatted_output = "\n".join(output_lines)
        
        return {
            "formatted_output": formatted_output,
            "json_output": preferences.model_dump()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error formatting output: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

