from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from main import (
    DecentralizedAgent,
    NegotiationSpace,
    LLMClient,
    create_demo_scenario,
    run_negotiation,
)
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

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
        preferences = json.loads(data)

        await websocket.send_text(json.dumps({"type": "status", "message": "Received preferences, starting negotiation..."}))

        # Setup LLM
        api_key = os.environ.get("OPENROUTER_API_KEY")
        llm = LLMClient(api_key, model="google/gemini-2.5-flash-preview-09-2025")

        # Create demo scenario (for now, keep using demo data)
        policy_maker, stakeholders = create_demo_scenario(llm, llm)
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
