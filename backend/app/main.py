"""
SoulSmith FastAPI Main Application
"""

import uuid
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.grammar import SEVEN_DICE_GRAMMAR, DiceRollRead
from app.rules import evaluate_scene_outcome, ResolveSceneRequest, ResolveSceneResponse, SoulSheetResources
from app.soulkeeper import generate_soulkeeper_narration, SoulkeeperNarration
from app.soulprint import generate_astrological_soulprint, SoulprintRequest, SoulprintProfile

app = FastAPI(
    title="SoulSmith Mythic Engine API",
    description="Backend API for SoulSmith - Living Mythology Engine",
    version="1.0.0"
)

# CORS middleware for local dev & frontend PWA
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store & World Chronicle log
CHRONICLE_EVENTS: List[Dict] = []
ACTIVE_WORLD_FACTS: List[str] = [
    "The Starforge remains dormant beneath the crystal peaks.",
    "The King Without a Reflection traverses the outer Veils."
]

# WebSocket Connection Manager for Convergence Rooms
class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, List[WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = []
        self.rooms[room_id].append(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket):
        if room_id in self.rooms:
            self.rooms[room_id].remove(websocket)
            if not self.rooms[room_id]:
                del self.rooms[room_id]

    async def broadcast(self, room_id: str, message: dict):
        if room_id in self.rooms:
            for connection in self.rooms[room_id]:
                await connection.send_json(message)

room_manager = RoomManager()

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "service": "SoulSmith Engine", "version": "1.0.0"}

@app.get("/api/v1/dice/grammar")
def get_dice_grammar():
    """Returns the full 7-dice grammar rules & face definitions."""
    return SEVEN_DICE_GRAMMAR

@app.post("/api/v1/dice/roll")
def cast_dice_roll() -> DiceRollRead:
    """Randomly casts all seven dice according to grammar face tables."""
    import random
    sparks = list(SEVEN_DICE_GRAMMAR["spark"].faces.keys())
    domains = list(SEVEN_DICE_GRAMMAR["domain"].faces.keys())
    pressures = list(SEVEN_DICE_GRAMMAR["pressure"].faces.keys())
    aims = list(SEVEN_DICE_GRAMMAR["aim"].faces.keys())
    approaches = list(SEVEN_DICE_GRAMMAR["approach"].faces.keys())
    verdicts = list(SEVEN_DICE_GRAMMAR["verdict"].faces.keys())
    threads = list(SEVEN_DICE_GRAMMAR["thread"].faces.keys())

    return DiceRollRead(
        spark=random.choice(sparks),
        domain=random.choice(domains),
        pressure=random.choice(pressures),
        aim=random.choice(aims),
        approach=random.choice(approaches),
        verdict=random.choice(verdicts),
        thread=random.choice(threads)
    )

@app.post("/api/v1/scenes/resolve")
def resolve_encounter_scene(req: ResolveSceneRequest):
    """
    Evaluates encounter outcome through deterministic rules ladder,
    then triggers Soulkeeper AI narration and logs event to World Chronicle.
    """
    # 1. Deterministic rules ladder evaluation
    outcome: ResolveSceneResponse = evaluate_scene_outcome(req)

    # 2. Soulkeeper AI Orchestration pass
    narration: SoulkeeperNarration = generate_soulkeeper_narration(
        dice_read=req.dice_read,
        player_intent=req.player_intent,
        outcome=outcome,
        soul_name=req.soul_name,
        calling="Keeper of Lore"
    )

    # 3. Log event to Chronicle
    event_entry = {
        "id": str(uuid.uuid4()),
        "soul_name": req.soul_name,
        "dice_read": req.dice_read.model_dump(),
        "outcome_class": outcome.outcome_class,
        "narration": narration.model_dump(),
        "rules_effects": outcome.model_dump()
    }
    CHRONICLE_EVENTS.append(event_entry)
    ACTIVE_WORLD_FACTS.extend(outcome.canon_facts)

    return {
        "outcome": outcome,
        "narration": narration,
        "event_id": event_entry["id"]
    }

@app.get("/api/v1/chronicle/events")
def list_chronicle_events():
    """Returns all recorded events in the World Chronicle."""
    return {
        "events": CHRONICLE_EVENTS,
        "active_world_facts": ACTIVE_WORLD_FACTS
    }

@app.post("/api/v1/soulprints/preview")
def create_soulprint(req: SoulprintRequest) -> SoulprintProfile:
    """Generates an optional Astrological Soulprint profile."""
    return generate_astrological_soulprint(req)

@app.websocket("/ws/v1/convergence/{room_id}")
async def convergence_websocket(websocket: WebSocket, room_id: str):
    """Real-time WebSocket connection for multiplayer Convergence rooms."""
    await room_manager.connect(room_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Broadcast roll or action to room
            await room_manager.broadcast(room_id, {
                "sender": data.get("sender", "Anonymous Soul"),
                "action_type": data.get("action_type", "roll"),
                "payload": data.get("payload", {})
            })
    except WebSocketDisconnect:
        room_manager.disconnect(room_id, websocket)
        await room_manager.broadcast(room_id, {"system": "A Soul departed the room."})
