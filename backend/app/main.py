"""
SoulSmith FastAPI Main Application
"""

import uuid
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.grammar import SEVEN_DICE_GRAMMAR, DiceRollRead
from app.rules import evaluate_scene_outcome, ResolveSceneRequest, ResolveSceneResponse
from app.soulkeeper import generate_soulkeeper_narration, SoulkeeperNarration
from app.soulprint import generate_astrological_soulprint, SoulprintRequest, SoulprintProfile
from app.vision import process_dice_photo, PhotoIngestRequest, PhotoIngestResponse
from app.phenomena import DEFAULT_ACTIVE_PHENOMENA, Phenomenon
from app.relics import process_relic_attunement, RelicAttuneRequest, RelicAttuneResponse
from app.db import init_database, log_canonical_event, get_all_canonical_events

app = FastAPI(
    title="SoulSmith Mythic Engine API",
    description="Backend API for SoulSmith - Living Mythology Engine",
    version="1.1.0"
)

# Initialize database tables on startup
@app.on_event("startup")
def on_startup():
    init_database()

# CORS middleware for local dev & frontend PWA
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"status": "ok", "service": "SoulSmith Engine", "version": "1.1.0"}

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

@app.post("/api/v1/dice/photo-ingest")
def optical_dice_photo_ingest(req: PhotoIngestRequest) -> PhotoIngestResponse:
    """Simulates computer vision optical dice photo scanning & face classification."""
    return process_dice_photo(req)

@app.post("/api/v1/scenes/resolve")
def resolve_encounter_scene(req: ResolveSceneRequest):
    """
    Evaluates encounter outcome through deterministic rules ladder,
    triggers Soulkeeper AI narration, and logs event to database.
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

    # 3. Log event to database
    event_id = log_canonical_event(
        soul_name=req.soul_name,
        outcome_class=outcome.outcome_class,
        dice_read=req.dice_read.model_dump(),
        narration=narration.model_dump(),
        canon_facts=outcome.canon_facts
    )

    return {
        "outcome": outcome,
        "narration": narration,
        "event_id": event_id
    }

@app.get("/api/v1/chronicle/events")
def list_chronicle_events():
    """Returns all recorded events from the persistent database."""
    events = get_all_canonical_events()
    return {
        "events": events,
        "active_world_facts": [
            "The Starforge remains dormant beneath the crystal peaks.",
            "The King Without a Reflection traverses the outer Veils."
        ]
    }

@app.get("/api/v1/phenomena")
def get_active_phenomena() -> List[Phenomenon]:
    """Returns all active world phenomena & world pressures."""
    return DEFAULT_ACTIVE_PHENOMENA

@app.post("/api/v1/relics/attune")
def attune_relic(req: RelicAttuneRequest) -> RelicAttuneResponse:
    """Processes relic attunement, overdraw, and stage progression."""
    return process_relic_attunement(req)

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
            await room_manager.broadcast(room_id, {
                "sender": data.get("sender", "Anonymous Soul"),
                "action_type": data.get("action_type", "roll"),
                "payload": data.get("payload", {})
            })
    except WebSocketDisconnect:
        room_manager.disconnect(room_id, websocket)
        await room_manager.broadcast(room_id, {"system": "A Soul departed the room."})
