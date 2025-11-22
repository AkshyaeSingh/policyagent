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


async def call_openrouter(messages: List[Dict[str, str]], model: str = "x-ai/grok-beta-fast") -> str:
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
    policy_dimensions: Dict[str, Any]
    question_count: int


# Policy Dimensions for airborne virus scenario
POLICY_DIMENSIONS = {
    "indoor_capacity_limit": (0, 100),
    "outdoor_capacity_limit": (0, 100),
    "social_distance_required_feet": (0, 10),
    "ventilation_standard_ACH": (0, 12),
    "business_curfew_hour": (18, 24),
    "essential_business_hours_only": (0, 1),
    "phased_reopening_weeks": (0, 52),
    "mask_mandate_level": (0, 4),
    "mask_provision_budget_per_person": (0, 50),
    "ppe_subsidy_percentage": (0, 100),
    "testing_frequency_requirement": (0, 7),
    "contact_tracing_level": (0, 3),
    "isolation_support_daily_amount": (0, 200),
    "quarantine_enforcement_level": (0, 3),
    "business_subsidy_percentage": (0, 80),
    "unemployment_bonus_weekly": (0, 600),
    "rent_relief_percentage": (0, 100),
    "essential_worker_hazard_pay": (0, 10),
    "travel_restriction_level": (0, 4),
    "essential_activities_list_restrictiveness": (0, 10),
    "exercise_allowance_hours": (0, 24),
    "household_mixing_allowed": (0, 3),
    "vaccine_mandate_sectors": (0, 10),
    "vaccine_priority_tiers": (1, 10),
    "treatment_rationing_criteria": (0, 3),
    "medical_resource_redistribution": (0, 1),
    "transparency_level": (0, 10),
    "update_frequency_hours": (1, 168),
    "misinformation_penalty_severity": (0, 5),
    "community_input_weight": (0, 1),
}

# Policy dimension units for display
DIMENSION_UNITS = {
    "indoor_capacity_limit": "%",
    "outdoor_capacity_limit": "%",
    "social_distance_required_feet": "feet",
    "ventilation_standard_ACH": "ACH",
    "business_curfew_hour": "hour (24h format)",
    "essential_business_hours_only": "binary (0/1)",
    "phased_reopening_weeks": "weeks",
    "mask_mandate_level": "level (0-4)",
    "mask_provision_budget_per_person": "$",
    "ppe_subsidy_percentage": "%",
    "testing_frequency_requirement": "times/week",
    "contact_tracing_level": "level (0-3)",
    "isolation_support_daily_amount": "$/day",
    "quarantine_enforcement_level": "level (0-3)",
    "business_subsidy_percentage": "%",
    "unemployment_bonus_weekly": "$/week",
    "rent_relief_percentage": "%",
    "essential_worker_hazard_pay": "$/hour",
    "travel_restriction_level": "level (0-4)",
    "essential_activities_list_restrictiveness": "level (0-10)",
    "exercise_allowance_hours": "hours/day",
    "household_mixing_allowed": "households",
    "vaccine_mandate_sectors": "sectors",
    "vaccine_priority_tiers": "tier (1-10)",
    "treatment_rationing_criteria": "level (0-3)",
    "medical_resource_redistribution": "binary (0/1)",
    "transparency_level": "level (0-10)",
    "update_frequency_hours": "hours",
    "misinformation_penalty_severity": "level (0-5)",
    "community_input_weight": "weight (0-1)",
}


@app.post("/api/generate-next-question")
async def generate_next_question(request: GenerateNextQuestionRequest):
    """Generate the next question dynamically based on previous answers and current preferences"""
    try:
        # Build context from previous answers
        answers_text = ""
        if request.previous_answers:
            answers_text = "\n".join([
                f"Q: {ans.get('question', {}).get('text', '') if isinstance(ans.get('question'), dict) else ans.get('question', '')}\nA: {ans.get('answer', '')}"
                for ans in request.previous_answers[-5:]
            ])
        
        preferences_text = ""
        if request.current_preferences:
            preferences_text = "\n".join([
                f"- {key}: {value}"
                for key, value in request.current_preferences.items()
            ])
        
        policy_dimensions_text = ""
        if request.policy_dimensions:
            policy_dimensions_text = "\n".join([
                f"- {key}: {value}"
                for key, value in request.policy_dimensions.items()
            ])
        
        # Get relevant policy dimensions for this user role
        role_dimension_mapping = {
            "Business_Owner": ["indoor_capacity_limit", "business_subsidy_percentage", "mask_mandate_level", "business_curfew_hour"],
            "Healthcare_Worker": ["mask_mandate_level", "ventilation_standard_ACH", "ppe_subsidy_percentage", "testing_frequency_requirement"],
            "Parent": ["school_format_preference", "child_mask_tolerance", "testing_frequency_requirement", "vaccine_mandate_sectors"],
            "Essential_Worker": ["essential_worker_hazard_pay", "ppe_subsidy_percentage", "testing_frequency_requirement", "sick_leave_days"],
            "Remote_Worker": ["travel_restriction_level", "lockdown_strictness", "public_space_restrictions"],
            "Elderly_Resident": ["isolation_support_daily_amount", "priority_delivery", "vaccine_priority_tiers"],
            "Small_Landlord": ["rent_relief_percentage", "eviction_moratorium", "property_tax_relief"],
            "Young_Adult": ["gathering_size_limit", "bar_closure_hour", "event_cancellation_tolerance"],
        }
        
        relevant_dimensions = role_dimension_mapping.get(request.user_role, list(POLICY_DIMENSIONS.keys())[:10])
        
        prompt = f"""You are generating questions for an AIRBORNE VIRUS CRISIS scenario requiring rapid coordination between individual autonomy and collective safety.

CONTEXT: We're in a crisis requiring rapid coordination. Users express preferences that map to policy dimensions.

User Information:
- Name: {request.user_name}
- Role: {request.user_role}
- Description: {request.user_description}

Previous Answers ({len(request.previous_answers)} answered):
{answers_text if answers_text else "None yet"}

Current Preferences Extracted:
{preferences_text if preferences_text else "None yet"}

Current Policy Dimensions Mapped:
{policy_dimensions_text if policy_dimensions_text else "None yet"}

Relevant Policy Dimensions for {request.user_role}:
{', '.join(relevant_dimensions)}

Generate ONE question that helps fill in missing policy dimensions. Focus on questions relevant to {request.user_role} in a virus crisis.

QUESTION TYPES AND FORMATS:

1. "trade_off" - For comparing two scenarios (swipe left/right)
   MUST include option_A and option_B objects with caption:
   {{
     "type": "trade_off",
     "question": "Which world would you prefer?",
     "option_A": {{
       "caption": "Restaurants at 75% capacity, 50 new cases daily"
     }},
     "option_B": {{
       "caption": "Restaurants at 25% capacity, 5 new cases daily"
     }},
     "reveals": ["indoor_capacity_limit", "risk_tolerance"]
   }}

2. "slider" - For ranking/preference intensity (0-100 slider)
   MUST include range and unit:
   {{
     "type": "slider",
     "question": "You're at a grocery store. How many people is too crowded?",
     "range": [5, 50],
     "unit": "people",
     "reveals": ["personal_space_requirement", "risk_tolerance"]
   }}

3. "numerical" - For specific numbers with units (multiple choice options)
   MUST include options array with units:
   {{
     "type": "numerical",
     "question": "Maximum indoor capacity you'd accept for your business?",
     "options": ["25%", "50%", "75%", "100%"],
     "unit": "percentage",
     "reveals": ["indoor_capacity_limit"]
   }}

4. "yes_no" - For binary choices (swipe left/right)
   {{
     "type": "yes_no",
     "question": "Your favorite bar requires proof of vaccination to enter",
     "context": "But your friend group is split on vaccination",
     "reveals": ["vaccine_mandate_support", "social_priority"]
   }}

5. "allocation" - For budget/resource distribution (slider bars that sum to constraint)
   MUST include options array and constraint:
   {{
     "type": "allocation",
     "question": "You have $100 in tax money to allocate:",
     "options": ["Business subsidies to stay open", "Free masks and tests for everyone", "Hazard pay for essential workers", "Unemployment benefits", "Hospital capacity expansion"],
     "constraint": 100,
     "reveals": ["economic_priority", "safety_priority"]
   }}

IMPORTANT:
- For trade_off: MUST include option_A and option_B objects (not just strings)
- For numerical: MUST provide 3-5 options with units
- For slider: MUST provide range [min, max] and unit
- For allocation: MUST provide options array and constraint number
- Questions MUST be specific to virus crisis and {request.user_role} role
- Focus on filling missing policy dimensions from: {', '.join(relevant_dimensions)}

Output ONLY valid JSON. If you have enough information, output: {{"complete": true}}

Generate the question now:"""

        messages = [
            {"role": "system", "content": "You are a question generation system for virus crisis policy preferences. Output only valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        response_text = await call_openrouter(messages)
        response_text = response_text.strip()
        
        # Parse JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        try:
            question_data = json.loads(response_text)
            if question_data.get("complete"):
                return {"complete": True, "question": None}
            
            return {
                "question": question_data,
                "complete": False
            }
        except json.JSONDecodeError:
            # Fallback - generate a role-appropriate question
            fallback_questions = {
                "Business_Owner": {
                    "type": "trade_off",
                    "question": "Which scenario would you prefer?",
                    "option_A": {"caption": "Restaurants at 75% capacity, 50 new cases daily"},
                    "option_B": {"caption": "Restaurants at 25% capacity, 5 new cases daily"},
                    "reveals": ["indoor_capacity_limit"]
                },
                "Healthcare_Worker": {
                    "type": "slider",
                    "question": "What's the minimum mask compliance rate you'd accept?",
                    "range": [50, 100],
                    "unit": "%",
                    "reveals": ["min_mask_compliance_rate"]
                },
                "Parent": {
                    "type": "yes_no",
                    "question": "Should schools require masks for children?",
                    "reveals": ["child_mask_tolerance"]
                },
                "Essential_Worker": {
                    "type": "numerical",
                    "question": "What's the minimum hazard pay you'd need?",
                    "options": ["$2/hour", "$5/hour", "$8/hour", "$10/hour"],
                    "unit": "$/hour",
                    "reveals": ["hazard_pay_minimum"]
                },
            }
            
            fallback = fallback_questions.get(request.user_role, {
                "type": "yes_no",
                "question": "Should masks be required in indoor public spaces?",
                "reveals": ["mask_mandate_level"]
            })
            
            return {
                "question": fallback,
                "complete": False
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating next question: {str(e)}")


@app.post("/api/update-preferences")
async def update_preferences(request: UpdatePreferencesRequest):
    """Update preferences incrementally as user answers questions"""
    try:
        # Build context from user info and answers
        answers_text = "\n".join([
            f"Q: {ans.get('question', {}).get('text', '') if isinstance(ans.get('question'), dict) else ans.get('question', '')}\nA: {ans.get('answer', '')}\nType: {ans.get('question', {}).get('type', 'unknown') if isinstance(ans.get('question'), dict) else 'unknown'}"
            for ans in request.answers
        ])
        
        prompt = f"""You are extracting preferences for an AIRBORNE VIRUS CRISIS scenario.

User: {request.user_name} ({request.user_role})
Initial Description: {request.user_description}

Answers so far:
{answers_text}

Available Policy Dimensions:
{json.dumps(list(POLICY_DIMENSIONS.keys()), indent=2)}

Extract preferences and map them to policy dimensions. For each answer:
1. Extract the user's preference value
2. Map it to relevant policy dimensions
3. Convert to appropriate types (float for numbers, string for categories, boolean for yes/no)

Example mappings:
- "75% capacity" → {{"indoor_capacity_limit": 75.0}}
- "mask required" → {{"mask_mandate_level": 3.0}}
- "$5000 subsidy" → {{"business_subsidy_percentage": 25.0}}
- "hazard pay $5/hour" → {{"essential_worker_hazard_pay": 5.0}}

Output ONLY JSON:
{{
  "preferences": {{
    "preference_key": value
  }},
  "policy_dimensions": {{
    "dimension_key": value
  }}
}}

Use role-appropriate preference keys from stakeholder examples."""

        messages = [
            {"role": "system", "content": "You are a preference extraction system for virus crisis policy. Map preferences to policy dimensions. Output only valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        response_text = await call_openrouter(messages)
        
        # Parse JSON
        response_text = response_text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        try:
            extracted_data = json.loads(response_text)
            preferences = extracted_data.get("preferences", {})
            policy_dimensions = extracted_data.get("policy_dimensions", {})
        except json.JSONDecodeError:
            preferences = {}
            policy_dimensions = {}
        
        # Log to console (backend side, not shown to user)
        print(f"\n{'='*60}")
        print(f"LIVE PREFERENCE UPDATE for {request.user_name} ({request.user_role})")
        print(f"After {len(request.answers)} answers:")
        print("\nUser Preferences:")
        for key, value in preferences.items():
            if value is None:
                print(f"  - {key}: None")
            elif isinstance(value, (int, float)):
                print(f"  - {key}: {float(value)}")
            else:
                print(f"  - {key}: {value}")
        
        if policy_dimensions:
            print("\nPolicy Dimensions Mapped:")
            for key, value in policy_dimensions.items():
                unit = DIMENSION_UNITS.get(key, "")
                if value is None:
                    print(f"  - {key}: None {unit}".strip())
                elif isinstance(value, (int, float)):
                    print(f"  - {key}: {float(value)} {unit}".strip())
                else:
                    print(f"  - {key}: {value} {unit}".strip())
        print(f"{'='*60}\n")
        
        return {
            "preferences": preferences,
            "policy_dimensions": policy_dimensions,
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
            f"Q: {ans.get('question', {}).get('text', '') if isinstance(ans.get('question'), dict) else ans.get('question', '')}\nA: {ans.get('answer', '')}\nType: {ans.get('question', {}).get('type', 'unknown') if isinstance(ans.get('question'), dict) else 'unknown'}"
            for ans in request.answers
        ])
        
        prompt = f"""You are finalizing preferences for an AIRBORNE VIRUS CRISIS scenario.

User: {request.user_name} ({request.user_role})
Initial Description: {request.user_description}

All Answers:
{answers_text}

Available Policy Dimensions:
{json.dumps(list(POLICY_DIMENSIONS.keys()), indent=2)}

Extract ALL final preferences and map them to policy dimensions. Be thorough and specific.

For preferences, use role-appropriate keys:
- Business_Owner: max_capacity_reduction, mask_requirement_acceptance, air_filtration_investment, revenue_loss_tolerance, compensation_required_monthly, delivery_pivot_capability, outdoor_space_available
- Healthcare_Worker: min_mask_compliance_rate, min_air_changes_per_hour, max_acceptable_case_rate, work_from_home_requirement, priority_medical_access, isolation_support_needed
- Parent: school_format_preference, child_mask_tolerance_hours, activity_restriction_acceptance, childcare_subsidy_needed, testing_frequency_acceptable, vaccine_requirement_support
- Essential_Worker: hazard_pay_minimum, ppe_provision_required, sick_leave_days_needed, testing_provided_frequency, transport_subsidy_needed, shift_flexibility_needed
- Remote_Worker: lockdown_strictness_acceptable, tax_increase_tolerance, public_space_restrictions_acceptable, delivery_service_dependence, gym_closure_tolerance_weeks, travel_restriction_tolerance
- Elderly_Resident: isolation_support_hours_weekly, priority_delivery_access, medical_appointment_transport, social_interaction_minimum_weekly, vaccination_priority_level, community_space_safety_requirement
- Small_Landlord: rent_freeze_tolerance_months, eviction_moratorium_acceptance, property_tax_relief_needed, maintenance_delay_acceptable, tenant_support_contribution, commercial_tenant_flexibility
- Young_Adult: gathering_size_limit_acceptable, bar_closure_hour_acceptable, event_cancellation_tolerance, mask_wearing_situations, testing_for_events_acceptable, vaccine_passport_support

Output ONLY JSON:
{{
  "preferences": {{
    "preference_key": value
  }},
  "policy_dimensions": {{
    "dimension_key": value
  }}
}}"""

        messages = [
            {"role": "system", "content": "You are a preference extraction system for virus crisis policy. Map preferences to policy dimensions. Output only valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        response_text = await call_openrouter(messages)
        
        # Parse JSON
        response_text = response_text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        try:
            extracted_data = json.loads(response_text)
            preferences = extracted_data.get("preferences", {})
            policy_dimensions = extracted_data.get("policy_dimensions", {})
        except json.JSONDecodeError:
            preferences = {}
            policy_dimensions = {}
        
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
        if policy_dimensions:
            print("\nPOLICY DIMENSIONS MAPPED:")
            for key, value in policy_dimensions.items():
                unit = DIMENSION_UNITS.get(key, "")
                if value is None:
                    print(f"  - {key}: None {unit}".strip())
                elif isinstance(value, (int, float)):
                    print(f"  - {key}: {float(value)} {unit}".strip())
                else:
                    print(f"  - {key}: {value} {unit}".strip())
        print(f"{'='*60}\n")
        
        return {
            "participant_name": request.user_name,
            "role": request.user_role,
            "preferences": preferences,
            "policy_dimensions": policy_dimensions,
            "formatted_output": formatted_output,
            "json_output": output.model_dump()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finalizing preferences: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

