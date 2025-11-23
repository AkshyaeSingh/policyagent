#!/usr/bin/env python3
"""
Test script for WebSocket negotiation backend
"""
import asyncio
import json
import websockets
import sys

async def test_websocket():
    uri = "ws://localhost:8000/ws/negotiate"

    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            # Send real preferences
            print("Sending user preferences...")
            preferences = {
                "participant_name": "Healthcare_Worker_Test",
                "role": "neighbor",
                "preferences": {
                    "min_mask_compliance_rate": 85.0,
                    "min_air_changes_per_hour": 8.0,
                    "max_acceptable_case_rate": 15.0,
                    "priority_medical_access": True,
                }
            }
            await websocket.send(json.dumps(preferences))

            # Receive updates
            print("\n=== WebSocket Connection Successful ===\n")
            update_count = 0

            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    update = json.loads(message)
                    update_count += 1

                    # Pretty print the update
                    update_type = update.get('type', 'unknown')
                    print(f"\n[Update #{update_count}] Type: {update_type.upper()}")
                    print("-" * 50)

                    if update.get('round'):
                        print(f"  Round: {update.get('round')}")

                    if update.get('agent'):
                        agent = update.get('agent')
                        score = update.get('score')
                        status = "✓" if score >= 4 else "⚠" if score == 3 else "✗"
                        print(f"  Agent: {agent} {status}")
                        print(f"  Score: {score}/5")
                        if update.get('explanation'):
                            print(f"  Explanation: {update.get('explanation')[:100]}...")

                    if update.get('average_score'):
                        print(f"  Average Score: {update.get('average_score'):.1f}/5")

                    if update.get('scores'):
                        print("  All Scores:")
                        for agent_name, score in update.get('scores', {}).items():
                            status = "✓" if score >= 4 else "⚠" if score == 3 else "✗"
                            print(f"    {agent_name}: {score}/5 {status}")

                    if update.get('message'):
                        print(f"  Message: {update.get('message')}")

                    if update.get('reasoning'):
                        print(f"  Reasoning: {update.get('reasoning')[:100]}...")

                    if update.get('modifications_count'):
                        print(f"  Modifications: {update.get('modifications_count')}")

                    if update.get('total_cost'):
                        print(f"  Total Cost: ${update.get('total_cost'):,.0f}")

                    # Stop if we see completion
                    if update_type in ['complete', 'failed']:
                        print("\n" + "=" * 50)
                        print("=== Negotiation Complete ===")
                        print("=" * 50)
                        break

                except asyncio.TimeoutError:
                    print("\nTimeout - no message received for 10 seconds")
                    break
                except json.JSONDecodeError as e:
                    print(f"\nJSON decode error: {e}")
                    break

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print(f"\n✓ Test complete! Received {update_count} updates")

if __name__ == "__main__":
    print("WebSocket Negotiation Test Script")
    print("=" * 50)
    print("Make sure the backend is running: uv run python app.py")
    print("=" * 50)
    asyncio.run(test_websocket())
