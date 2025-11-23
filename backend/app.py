from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple, Optional, Dict, Any
from main import (
    DecentralizedAgent,
    NegotiationSpace,
    LLMClient,
    Preference,
    create_demo_scenario,
    run_negotiation,
)
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

def create_scenario_from_preferences(
    user_prefs: Dict[str, Any],
    llm: LLMClient
) -> Tuple[DecentralizedAgent, List[DecentralizedAgent]]:
    """
    Create agents from received user preferences instead of demo data.

    Args:
        user_prefs: Dict with 'preferences', 'participant_name', 'role', etc.
        llm: LLM client

    Returns:
        Tuple of (developer_agent, list_of_neighbor_agents)
    """

    # Extract user info
    participant_name = user_prefs.get("participant_name", "User")
    role = user_prefs.get("role", "neighbor")
    pref_dict = user_prefs.get("preferences", {})

    # Convert preference dict to Preference tuples
    user_preferences: List[Preference] = [
        (key, value) for key, value in pref_dict.items()
    ]

    print(f"\n{'='*60}")
    print(f"Creating scenario from user preferences:")
    print(f"Participant: {participant_name}")
    print(f"Role: {role}")
    print(f"Preferences count: {len(user_preferences)}")
    print(f"{'='*60}\n")

    # If user is a neighbor/stakeholder, create them as a neighbor
    # and create a default policy maker
    if role != "developer":
        # Create the user as a neighbor agent
        user_agent = DecentralizedAgent(
            name=participant_name,
            role="neighbor",
            preferences=user_preferences,
            llm=llm,
            max_side_payment_budget=5000.0  # Default budget
        )

        # Create a default policy maker
        policy_maker = DecentralizedAgent(
            name="Policy_Maker",
            role="developer",
            preferences=[
                ("total_budget_under", 50000000.0),
                ("case_rate_target_below", 50.0),
            ],
            llm=llm,
            max_side_payment_budget=0
        )

        # Return with user as one of the neighbors
        return policy_maker, [user_agent]

    else:
        # User is the developer/policy maker
        policy_maker = DecentralizedAgent(
            name=participant_name,
            role="developer",
            preferences=user_preferences,
            llm=llm,
            max_side_payment_budget=0
        )

        # Create some default neighbors to negotiate with
        default_neighbors = [
            DecentralizedAgent(
                name="Healthcare_Worker",
                role="neighbor",
                preferences=[
                    ("min_mask_compliance_rate", 80.0),
                    ("min_air_changes_per_hour", 6.0),
                    ("max_acceptable_case_rate", 20.0),
                ],
                llm=llm,
                max_side_payment_budget=5000.0
            ),
            DecentralizedAgent(
                name="Business_Owner",
                role="neighbor",
                preferences=[
                    ("max_capacity_reduction", 30.0),
                    ("revenue_loss_tolerance", 20.0),
                ],
                llm=llm,
                max_side_payment_budget=3000.0
            ),
        ]

        return policy_maker, default_neighbors

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Backend Negotiation WebSocket API", "status": "running"}


@app.websocket("/ws/negotiate")
async def websocket_negotiate(websocket: WebSocket):
    await websocket.accept()
    try:
        # Receive preferences from frontend
        data = await websocket.receive_text()
        user_preferences = json.loads(data)

        # If no preferences provided, use demo scenario
        if not user_preferences or "preferences" not in user_preferences or not user_preferences.get("preferences"):
            await websocket.send_text(json.dumps({"type": "status", "message": "No preferences provided, using demo scenario..."}))
            api_key = os.environ.get("OPENROUTER_API_KEY")
            llm = LLMClient(api_key, model="google/gemini-2.5-flash-preview-09-2025")
            policy_maker, stakeholders = create_demo_scenario(llm, llm)
        else:
            await websocket.send_text(json.dumps({"type": "status", "message": f"Received preferences for {user_preferences.get('participant_name', 'User')}, starting negotiation..."}))

            # Setup LLM
            api_key = os.environ.get("OPENROUTER_API_KEY")
            llm = LLMClient(api_key, model="google/gemini-2.5-flash-preview-09-2025")

            # Create scenario from actual user preferences
            policy_maker, stakeholders = create_scenario_from_preferences(user_preferences, llm)

        space = NegotiationSpace()

        # Capture the event loop BEFORE starting threads
        loop = asyncio.get_running_loop()
        update_queue = asyncio.Queue()

        # Callback to queue updates (sync, not async)
        def on_update(update):
            try:
                # Use call_soon_threadsafe to safely queue from another thread
                loop.call_soon_threadsafe(update_queue.put_nowait, update)
            except Exception as e:
                print(f"Error queuing update: {e}")

        # Run negotiation in thread pool so we don't block event loop
        executor = ThreadPoolExecutor(max_workers=1)

        def run_neg():
            return run_negotiation(
                policy_maker,
                stakeholders,
                space,
                max_rounds=7,
                on_update=on_update
            )

        # Start negotiation in background
        negotiation_task = loop.run_in_executor(executor, run_neg)

        # Stream updates while negotiation runs
        pending_updates = []
        while True:
            # Check for new updates in queue
            while not update_queue.empty():
                try:
                    update = update_queue.get_nowait()
                    pending_updates.append(update)
                except asyncio.QueueEmpty:
                    break

            # Send any pending updates
            for update in pending_updates:
                await websocket.send_text(json.dumps(update))
                pending_updates.remove(update)

            # Check if negotiation is done
            if negotiation_task.done():
                break

            # Small delay to avoid busy waiting
            await asyncio.sleep(0.1)

        # Get final proposal
        final_proposal = negotiation_task.result()

        # Send final result back
        if final_proposal:
            await websocket.send_text(json.dumps({
                "type": "final_proposal",
                "base_project": final_proposal.base_project,
                "modifications": final_proposal.modifications,
                "compensation": final_proposal.compensation,
                "total_cost": final_proposal.total_cost,
            }))

    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            await websocket.send_text(json.dumps({"type": "error", "error": str(e)}))
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
