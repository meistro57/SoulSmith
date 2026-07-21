# backend/app/main.py
"""
SoulSmith FastAPI Main Application.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.db import get_all_canonical_events, init_database, log_canonical_event
from app.encounters import EncounterFrame, EncounterFrameRequest, generate_encounter_frame
from app.grammar import (
    CURRENT_GRAMMAR_VERSION,
    NumericDiceRoll,
    RollRequest,
    get_available_versions,
    get_versioned_grammar,
    generate_numeric_roll,
    interpret_numeric_roll,
)
from app.phenomena import DEFAULT_ACTIVE_PHENOMENA, Phenomenon
from app.relics import RelicAttuneRequest, RelicAttuneResponse, process_relic_attunement
from app.rules import ResolveSceneRequest, ResolveSceneResponse, evaluate_scene_outcome
from app.soulkeeper import SoulkeeperNarration, generate_soulkeeper_narration
from app.soulprint import (
    SoulprintProfile,
    SoulprintRequest,
    generate_astrological_soulprint,
)
from app.vision import PhotoIngestRequest, PhotoIngestResponse, process_dice_photo


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield


app = FastAPI(
    title="SoulSmith Mythic Engine API",
    description="Backend API for SoulSmith - Living Mythology Engine",
    version="1.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RoomManager:
    def __init__(self) -> None:
        self.rooms: Dict[str, List[WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.rooms.setdefault(room_id, []).append(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket) -> None:
        if room_id in self.rooms:
            self.rooms[room_id].remove(websocket)
            if not self.rooms[room_id]:
                del self.rooms[room_id]

    async def broadcast(self, room_id: str, message: dict) -> None:
        for connection in self.rooms.get(room_id, []):
            await connection.send_json(message)


room_manager = RoomManager()


@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "service": "SoulSmith Engine", "version": "1.2.0"}


@app.get("/api/v1/dice/grammar")
def get_dice_grammar(version: str = CURRENT_GRAMMAR_VERSION):
    grammar = get_versioned_grammar(version)
    return grammar.model_dump()


@app.get("/api/v1/dice/grammar/versions")
def list_dice_grammar_versions():
    return get_available_versions()


@app.post("/api/v1/dice/roll")
def cast_dice_roll(req: RollRequest | None = None):
    req = req or RollRequest()
    return generate_numeric_roll(grammar_version=req.grammar_version, seed=req.seed)


@app.post("/api/v1/dice/interpret")
def interpret_dice_roll(req: NumericDiceRoll):
    return interpret_numeric_roll(req)


@app.post("/api/v1/encounters/frame")
def frame_encounter(req: EncounterFrameRequest) -> EncounterFrame:
    return generate_encounter_frame(req)


@app.post("/api/v1/dice/photo-ingest")
def optical_dice_photo_ingest(req: PhotoIngestRequest) -> PhotoIngestResponse:
    return process_dice_photo(req)


@app.post("/api/v1/scenes/resolve")
def resolve_encounter_scene(req: ResolveSceneRequest):
    outcome: ResolveSceneResponse = evaluate_scene_outcome(req)
    narration: SoulkeeperNarration = generate_soulkeeper_narration(
        dice_read=req.dice_read,
        player_intent=req.player_intent,
        outcome=outcome,
        soul_name=req.soul_name,
        calling="Keeper of Lore",
    )
    event_id = log_canonical_event(
        soul_name=req.soul_name,
        outcome_class=outcome.outcome_class,
        dice_read=req.dice_read.model_dump(),
        narration=narration.model_dump(),
        canon_facts=outcome.canon_facts,
        player_intent=req.player_intent,
        chosen_approach=req.chosen_approach,
        resource_investment={
            "resonance_spent": req.resonance_spent,
            "strain_accepted": req.strain_accepted,
        },
        deterministic_outcome=outcome.model_dump(),
    )
    return {
        "outcome": outcome,
        "narration": narration,
        "event_id": event_id,
        "dice_read": req.dice_read,
    }


@app.get("/api/v1/chronicle/events")
def list_chronicle_events():
    events = get_all_canonical_events()
    return {
        "events": events,
        "active_world_facts": [
            "The Starforge remains dormant beneath the crystal peaks.",
            "The King Without a Reflection traverses the outer Veils.",
        ],
    }


@app.get("/api/v1/phenomena")
def get_active_phenomena() -> List[Phenomenon]:
    return DEFAULT_ACTIVE_PHENOMENA


@app.post("/api/v1/relics/attune")
def attune_relic(req: RelicAttuneRequest) -> RelicAttuneResponse:
    return process_relic_attunement(req)


@app.post("/api/v1/soulprints/preview")
def create_soulprint(req: SoulprintRequest) -> SoulprintProfile:
    return generate_astrological_soulprint(req)


@app.websocket("/ws/v1/convergence/{room_id}")
async def convergence_websocket(websocket: WebSocket, room_id: str):
    await room_manager.connect(room_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await room_manager.broadcast(
                room_id,
                {
                    "sender": data.get("sender", "Anonymous Soul"),
                    "action_type": data.get("action_type", "roll"),
                    "payload": data.get("payload", {}),
                },
            )
    except WebSocketDisconnect:
        room_manager.disconnect(room_id, websocket)
        await room_manager.broadcast(room_id, {"system": "A Soul departed the room."})
