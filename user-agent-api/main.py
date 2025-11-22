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


class QuestionGenerationRequest(BaseModel):
    user_name: str
    user_role: str
    user_description: str


class UpdatePreferencesRequest(BaseModel):
    user_name: str
    user_role: str
    user_description: str
    answers: List[Dict[str, Any]]


class FinalizePreferencesRequest(BaseModel):
    user_name: str
    user_role: str
    user_description: str
    answers: List[Dict[str, Any]]


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


@app.post("/api/generate-questions")
async def generate_questions(request: QuestionGenerationRequest):
    """Generate contextual questions based on user input"""
    try:
        prompt = f"""You are generating questions to understand a user's policy preferences.

User Information:
- Name: {request.user_name}
- Role: {request.user_role}
- Description: {request.user_description}

Generate 8-12 short, clear questions that help understand their preferences. Questions should be:
- One sentence each
- Focused on specific policy trade-offs
- Relevant to their role and description
- Similar to: "You'd accept a 10-story building on your block if it meant 20% lower rents"

Output ONLY a JSON array of question strings:
["question 1", "question 2", "question 3", ...]"""

        messages = [
            {"role": "system", "content": "You are a question generation system. Output only valid JSON arrays."},
            {"role": "user", "content": prompt}
        ]
        
        response_text = await call_openrouter(messages, model="anthropic/claude-3.5-sonnet")
        
        # Parse JSON response
        response_text = response_text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        try:
            questions = json.loads(response_text)
            if not isinstance(questions, list):
                questions = [questions] if questions else []
        except json.JSONDecodeError:
            # Fallback: try to extract questions from text
            questions = [
                "You'd accept a 10-story building on your block if it meant 20% lower rents",
                "You care about the noise of the construction site",
                "You care specifically about noise during the morning",
                "Parking availability is important to you",
                "You're willing to accept compensation for inconveniences",
            ]
        
        return {"questions": questions}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")


class GenerateNextQuestionRequest(BaseModel):
    user_name: str
    user_role: str
    user_description: str
    previous_answers: List[Dict[str, Any]]
    current_preferences: Dict[str, Any]
    question_count: int


@app.post("/api/generate-next-question")
async def generate_next_question(request: GenerateNextQuestionRequest):
    """Generate the next question dynamically based on previous answers and current preferences"""
    try:
        # Build context from previous answers
        answers_text = ""
        if request.previous_answers:
            answers_text = "\n".join([
                f"Q: {ans.get('question', '')}\nA: {ans.get('answer', '')}"
                for ans in request.previous_answers[-5:]  # Last 5 answers for context
            ])
        
        preferences_text = ""
        if request.current_preferences:
            preferences_text = "\n".join([
                f"- {key}: {value}"
                for key, value in request.current_preferences.items()
            ])
        
        prompt = f"""You are generating the NEXT question to understand a user's policy preferences.

User Information:
- Name: {request.user_name}
- Role: {request.user_role}
- Initial Description: {request.user_description}

Previous Answers ({len(request.previous_answers)} answered so far):
{answers_text if answers_text else "None yet"}

Current Extracted Preferences:
{preferences_text if preferences_text else "None yet"}

Generate ONE new question that:
1. Builds on what you've learned from previous answers
2. Explores areas not yet covered
3. Gets more specific based on their revealed preferences
4. Helps extract concrete values (numbers, dates, constraints)
5. Is relevant to their role: {request.user_role}

The question should be:
- One clear sentence
- Focused on a specific policy trade-off or preference
- Not repetitive of previous questions
- Designed to extract a specific preference value if possible

Examples:
- "You'd accept a 10-story building on your block if it meant 20% lower rents"
- "You care specifically about noise during the morning"
- "What's the minimum compensation you'd accept for construction inconveniences?"

Output ONLY the question as a plain string (no JSON, no quotes, just the question text).
If you have enough information to extract all preferences, output: "COMPLETE" """

        messages = [
            {"role": "system", "content": "You are an adaptive question generation system. Generate one question at a time based on what you've learned."},
            {"role": "user", "content": prompt}
        ]
        
        response_text = await call_openrouter(messages, model="anthropic/claude-3.5-sonnet")
        response_text = response_text.strip()
        
        # Remove quotes if present
        if response_text.startswith('"') and response_text.endswith('"'):
            response_text = response_text[1:-1]
        if response_text.startswith("'") and response_text.endswith("'"):
            response_text = response_text[1:-1]
        
        # Check if AI says we're complete
        if "COMPLETE" in response_text.upper() or request.question_count >= 12:
            return {"complete": True, "question": None}
        
        return {"question": response_text, "complete": False}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating next question: {str(e)}")


@app.post("/api/update-preferences")
async def update_preferences(request: UpdatePreferencesRequest):
    """Update preferences incrementally as user answers questions"""
    try:
        # Build context from user info and answers
        answers_text = "\n".join([
            f"Q: {ans.get('question', '')}\nA: {ans.get('answer', '')}"
            for ans in request.answers
        ])
        
        prompt = f"""Based on the user's initial description and their answers so far, extract their preferences.

User: {request.user_name} ({request.user_role})
Initial Description: {request.user_description}

Answers so far:
{answers_text}

Extract preferences as key-value pairs. Use descriptive snake_case keys.
Output ONLY JSON:
{{"preferences": {{"key": value_or_null}}}}"""

        messages = [
            {"role": "system", "content": "You are a preference extraction system. Output only valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        response_text = await call_openrouter(messages, model="anthropic/claude-3.5-sonnet")
        
        # Parse JSON
        response_text = response_text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        try:
            extracted_data = json.loads(response_text)
            preferences = extracted_data.get("preferences", {})
        except json.JSONDecodeError:
            preferences = {}
        
        # Log to console (backend side, not shown to user)
        print(f"\n{'='*60}")
        print(f"LIVE PREFERENCE UPDATE for {request.user_name} ({request.user_role})")
        print(f"After {len(request.answers)} answers:")
        for key, value in preferences.items():
            if value is None:
                print(f"  - {key}: None")
            elif isinstance(value, (int, float)):
                print(f"  - {key}: {float(value)}")
            else:
                print(f"  - {key}: {value}")
        print(f"{'='*60}\n")
        
        return {
            "preferences": preferences,
            "participant_name": request.user_name,
            "role": request.user_role
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating preferences: {str(e)}")


@app.post("/api/finalize-preferences")
async def finalize_preferences(request: FinalizePreferencesRequest):
    """Finalize and format preferences after all questions are answered"""
    try:
        # Build full context
        answers_text = "\n".join([
            f"Q: {ans.get('question', '')}\nA: {ans.get('answer', '')}"
            for ans in request.answers
        ])
        
        prompt = f"""Extract the final, complete preferences from this user's input.

User: {request.user_name} ({request.user_role})
Initial Description: {request.user_description}

All Answers:
{answers_text}

Extract ALL preferences mentioned. Be thorough and specific.
- Use descriptive snake_case keys (e.g., "noise_level_below_db", "compensation_minimum")
- Values: float for numbers, string for text/dates, None if mentioned but no value
- Include all constraints, requirements, and priorities

Output ONLY JSON:
{{"preferences": {{"key": value_or_null}}}}"""

        messages = [
            {"role": "system", "content": "You are a preference extraction system. Output only valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        response_text = await call_openrouter(messages, model="anthropic/claude-3.5-sonnet")
        
        # Parse JSON
        response_text = response_text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        try:
            extracted_data = json.loads(response_text)
            preferences = extracted_data.get("preferences", {})
        except json.JSONDecodeError:
            preferences = {}
        
        # Format output
        participant_prefs = ParticipantPreferences(
            participant_name=request.user_name,
            role=request.user_role,
            preferences=preferences
        )
        
        output = PreferencesOutput(participants=[participant_prefs])
        
        # Format as string
        output_lines = ["PARTICIPANTS:\n"]
        output_lines.append(f"\n{participant_prefs.participant_name} ({participant_prefs.role}):\n")
        for key, value in participant_prefs.preferences.items():
            if value is None:
                output_lines.append(f"  - {key}: None")
            elif isinstance(value, (int, float)):
                output_lines.append(f"  - {key}: {float(value)}")
            else:
                output_lines.append(f"  - {key}: {value}")
        
        formatted_output = "\n".join(output_lines)
        
        # Print final output (backend side)
        print(f"\n{'='*60}")
        print("FINAL PREFERENCES OUTPUT:")
        print(formatted_output)
        print(f"{'='*60}\n")
        
        return {
            "participant_name": request.user_name,
            "role": request.user_role,
            "preferences": preferences,
            "formatted_output": formatted_output,
            "json_output": output.model_dump()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finalizing preferences: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

