# backend/app/main.py
"""
SoulSmith FastAPI Main Application.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware

from app.auth import (
    AuthResponse,
    UserLoginRequest,
    UserModel,
    UserSignupRequest,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.curiosity import (
    IntegrateThreadRequest,
    QuestionResolveRequest,
    SeedPlantRequest,
)
from app.constellation import (
    AWAKENING_STAGE_DESCRIPTIONS,
    AdvanceAwakeningRequest,
    CreateAspectRequest,
    CreateBondRequest,
)
from app.db import (
    create_aspect_record,
    create_cross_aspect_bond_record,
    create_user_record,
    execute_integration_event,
    get_all_canonical_events,
    get_all_local_threads,
    get_all_open_questions,
    get_all_seeds,
    get_or_create_primary_constellation,
    get_or_create_relics_records,
    get_probable_paths_records,
    get_relic_history_records,
    get_user_by_email,
    get_user_by_username,
    init_database,
    log_canonical_event,
    log_probable_path_record,
    plant_or_echo_seed,
    resolve_open_question,
    update_awakening_stage_record,
    update_probable_path_manifestation,
    update_relic_stage_record,
)
from app.relics import (
    RelicEventModel,
    RelicModel,
    RelicNarrativeAttuneRequest,
    RelicOverdrawRequest,
    RelicRepairRequest,
    RelicTransfigureRequest,
)
from app.probable_paths import (
    CreateProbablePathRequest,
    ExploreAlternateSceneRequest,
    ManifestPathRequest,
    ProbablePathModel,
    simulate_alternate_scene_exploration,
)
from app.encounters import (
    EncounterFrame,
    EncounterFrameRequest,
    generate_encounter_frame,
)
from app.grammar import (
    CURRENT_GRAMMAR_VERSION,
    NumericDiceRoll,
    RollRequest,
    generate_numeric_roll,
    get_available_versions,
    get_versioned_grammar,
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


@app.post("/api/v1/auth/signup", response_model=AuthResponse)
def signup(req: UserSignupRequest):
    if get_user_by_email(req.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists",
        )
    if get_user_by_username(req.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken",
        )

    hashed = hash_password(req.password)
    user_record = create_user_record(
        email=req.email,
        username=req.username,
        password_hash=hashed,
        display_name=req.display_name,
    )
    user_model = UserModel(
        id=user_record["id"],
        email=user_record["email"],
        username=user_record["username"],
        display_name=user_record["display_name"],
    )
    token = create_access_token(user_model.id)
    return AuthResponse(access_token=token, user=user_model)


@app.post("/api/v1/auth/login", response_model=AuthResponse)
def login(req: UserLoginRequest):
    user_record = get_user_by_email(req.username_or_email) or get_user_by_username(req.username_or_email)
    if not user_record or not verify_password(req.password, user_record["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password",
        )

    user_model = UserModel(
        id=user_record["id"],
        email=user_record["email"],
        username=user_record["username"],
        display_name=user_record["display_name"],
        created_at=user_record.get("created_at"),
    )
    token = create_access_token(user_model.id)
    return AuthResponse(access_token=token, user=user_model)


@app.get("/api/v1/auth/me", response_model=UserModel)
def get_me(authorization: Optional[str] = Header(None)):
    return get_current_user(authorization=authorization)


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

    # Curiosity Engine: Auto-plant or echo seed if a Thread symbol is present in the roll
    seed_result = None
    thread_symbol = req.dice_read.interpretation.thread
    if thread_symbol in ["Bond", "Memory", "Mark", "Prophecy"]:
        symbol_name = f"{req.dice_read.interpretation.spark} {req.dice_read.interpretation.domain}"
        question_text = f"What hidden connection does the {symbol_name} hold for {req.soul_name} under {req.dice_read.interpretation.pressure}?"
        seed_result = plant_or_echo_seed(
            symbol=symbol_name,
            thread_type=thread_symbol,
            narrative_context=req.player_intent,
            soul_id=req.soul_name,
            initial_question=question_text,
        )

    # Probable Paths Engine: Auto-log unchosen approach branch
    all_approaches = ["Guile", "Confrontation", "Release", "Integration"]
    unchosen = [a for a in all_approaches if a.lower() != req.chosen_approach.lower()]
    alternate_approach = unchosen[0] if unchosen else "Direct Resistance"

    path_title = f"The {req.dice_read.interpretation.domain} Fork: {req.chosen_approach} vs {alternate_approach}"
    probable_path = log_probable_path_record(
        event_id=event_id,
        soul_id=req.soul_name,
        path_title=path_title,
        chosen_path=f"Resolved via {req.chosen_approach}",
        unchosen_approach=alternate_approach,
        potential_outcome_class=outcome.outcome_class,
        manifestation_type="dream",
        provenance_summary=f"Event #{event_id[:6]}: Chosen path '{req.chosen_approach}' persisted. '{alternate_approach}' preserved as dormant probability branch.",
    )

    return {
        "outcome": outcome,
        "narration": narration,
        "event_id": event_id,
        "dice_read": req.dice_read,
        "seed": seed_result,
        "probable_path": probable_path,
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


@app.get("/api/v1/curiosity/seeds")
def list_curiosity_seeds():
    return {"seeds": get_all_seeds()}


@app.post("/api/v1/curiosity/seeds/plant")
def plant_curiosity_seed(req: SeedPlantRequest):
    return plant_or_echo_seed(
        symbol=req.symbol,
        thread_type=req.thread_type,
        narrative_context=req.narrative_context,
        soul_id=req.soul_id,
        initial_question=req.initial_question,
    )


@app.get("/api/v1/curiosity/questions")
def list_curiosity_questions():
    return {"questions": get_all_open_questions()}


@app.post("/api/v1/curiosity/questions/resolve")
def resolve_curiosity_question(req: QuestionResolveRequest):
    success = resolve_open_question(
        question_id=req.question_id,
        resolution_notes=req.resolution_notes,
        status=req.status,
    )
    return {"success": success}


@app.get("/api/v1/curiosity/threads")
def list_local_threads(soul_name: str = "Unbound Soul"):
    return {"threads": get_all_local_threads(soul_id=soul_name)}


@app.post("/api/v1/curiosity/integrate")
def integrate_local_thread(req: IntegrateThreadRequest):
    return execute_integration_event(
        thread_id=req.thread_id,
        soul_id=req.soul_name,
        choice_made=req.choice_made,
        target_relic_id=req.target_relic_id,
    )


@app.get("/api/v1/phenomena")
def get_active_phenomena() -> List[Phenomenon]:
    return DEFAULT_ACTIVE_PHENOMENA


@app.post("/api/v1/relics/attune")
def attune_relic(req: RelicAttuneRequest) -> RelicAttuneResponse:
    return process_relic_attunement(req)


@app.post("/api/v1/soulprints/preview")
def create_soulprint(req: SoulprintRequest) -> SoulprintProfile:
    return generate_astrological_soulprint(req)


@app.get("/api/v1/constellation")
def get_constellation():
    constellation = get_or_create_primary_constellation()
    stage_info = AWAKENING_STAGE_DESCRIPTIONS.get(constellation["awakening_stage"], {
        "title": constellation["awakening_stage"].capitalize(),
        "description": "The Constellation patterns unfold across Aspects.",
    })
    return {
        "constellation": constellation,
        "stage_info": stage_info,
    }


@app.post("/api/v1/constellation/aspects/create")
def create_aspect(req: CreateAspectRequest):
    aspect = create_aspect_record(
        constellation_id=req.constellation_id,
        aspect_name=req.aspect_name,
        calling=req.calling,
        origin=req.origin,
        era_or_world=req.era_or_world,
    )
    return {"aspect": aspect}


@app.post("/api/v1/constellation/bonds/create")
def create_cross_aspect_bond(req: CreateBondRequest):
    bond = create_cross_aspect_bond_record(
        constellation_id=req.constellation_id,
        source_aspect_id=req.source_aspect_id,
        target_aspect_id=req.target_aspect_id,
        bond_type=req.bond_type,
        description=req.description,
    )
    return {"bond": bond}


@app.post("/api/v1/constellation/advance")
def advance_awakening_stage(req: AdvanceAwakeningRequest):
    new_stage = update_awakening_stage_record(
        constellation_id=req.constellation_id,
        target_stage=req.target_stage,
    )
    return {"awakening_stage": new_stage}


@app.get("/api/v1/probable-paths")
def list_probable_paths(soul_id: str = "Kaelen the Star-Watcher"):
    paths = get_probable_paths_records(soul_id=soul_id)
    return {"probable_paths": paths}


@app.post("/api/v1/probable-paths/log")
def log_probable_path(req: CreateProbablePathRequest):
    path = log_probable_path_record(
        soul_id=req.soul_id,
        path_title=req.path_title,
        chosen_path=req.chosen_path,
        unchosen_approach=req.unchosen_approach,
        potential_outcome_class=req.potential_outcome_class,
        event_id=req.event_id,
        manifestation_type=req.manifestation_type,
        provenance_summary=req.provenance_summary,
    )
    return {"probable_path": path}


@app.post("/api/v1/probable-paths/manifest")
def manifest_probable_path(req: ManifestPathRequest):
    path = update_probable_path_manifestation(
        path_id=req.path_id,
        manifestation_type=req.manifestation_type,
        status=req.status,
    )
    return {"probable_path": path}


@app.post("/api/v1/probable-paths/explore")
def explore_probable_path(req: ExploreAlternateSceneRequest):
    paths = get_probable_paths_records(soul_id=req.soul_name)
    matched = next((p for p in paths if p["id"] == req.path_id), None)
    if not matched:
        raise ValueError("Probable path not found")

    path_model = ProbablePathModel(**matched)
    result = simulate_alternate_scene_exploration(path_model, req.soul_name)
    return {"alternate_scene": result}


# Relic Recognition API Endpoints


@app.get("/api/v1/relics")
def list_relics(soul_id: str = "Kaelen the Star-Watcher"):
    records = get_or_create_relics_records(soul_id=soul_id)
    return {"relics": [RelicModel(**r) for r in records]}


@app.get("/api/v1/relics/{relic_id}/history")
def get_relic_history(relic_id: str):
    records = get_relic_history_records(relic_id=relic_id)
    return {"history": [RelicEventModel(**r) for r in records]}


@app.post("/api/v1/relics/attune-narrative")
def attune_relic_narrative(req: RelicNarrativeAttuneRequest):
    relics = get_or_create_relics_records(soul_id=req.soul_id)
    target = next((r for r in relics if r["id"] == req.relic_id), None)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relic not found")

    current_stage = target["stage"]
    if current_stage == "Dormant":
        next_stage = "Remembered"
    elif current_stage == "Remembered":
        next_stage = "Awakened"
    else:
        next_stage = "Awakened"

    result = update_relic_stage_record(
        relic_id=req.relic_id,
        soul_id=req.soul_id,
        action="attune",
        new_stage=next_stage,
        narrative_condition_met=req.narrative_condition_met,
        chronicle_evidence_summary=req.chronicle_evidence_summary,
    )
    return {
        "relic": RelicModel(**result["relic"]),
        "relic_event": RelicEventModel(**result["relic_event"]),
    }


@app.post("/api/v1/relics/overdraw")
def overdraw_relic(req: RelicOverdrawRequest):
    relics = get_or_create_relics_records(soul_id=req.soul_id)
    target = next((r for r in relics if r["id"] == req.relic_id), None)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relic not found")

    current_stage = target["stage"]
    if current_stage == "Overdrawn":
        new_stage = "Fractured"
        action = "fracture"
        cond = "Overdrawn power pushed past structural resonance limit."
        evidence = "The relic's vessel shattered into splintered glints."
        effect = "FRACTURED: Relic capability disabled until narrative repair condition is met."
    else:
        new_stage = "Overdrawn"
        action = "overdraw"
        cond = f"Channeled overdrawn power: {req.intensity_boost}."
        evidence = "Soulkeeper accepts +1 Glitch Strain to force acute ascendancy."
        effect = f"OVERDRAWN: {req.intensity_boost}. Channelling adds +1 Strain per encounter."

    result = update_relic_stage_record(
        relic_id=req.relic_id,
        soul_id=req.soul_id,
        action=action,
        new_stage=new_stage,
        narrative_condition_met=cond,
        chronicle_evidence_summary=evidence,
        new_effect=effect,
    )
    return {
        "relic": RelicModel(**result["relic"]),
        "relic_event": RelicEventModel(**result["relic_event"]),
    }


@app.post("/api/v1/relics/repair")
def repair_relic(req: RelicRepairRequest):
    relics = get_or_create_relics_records(soul_id=req.soul_id)
    target = next((r for r in relics if r["id"] == req.relic_id), None)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relic not found")

    if target["stage"] != "Fractured":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Relic is not in Fractured state",
        )

    restored_effect = "Repaired and cleansed of glitch strain. Fully Awakened."
    result = update_relic_stage_record(
        relic_id=req.relic_id,
        soul_id=req.soul_id,
        action="repair",
        new_stage="Awakened",
        narrative_condition_met="Narrative repair condition fulfilled via Chronicle evidence.",
        chronicle_evidence_summary=req.repair_evidence_summary,
        new_effect=restored_effect,
    )
    return {
        "relic": RelicModel(**result["relic"]),
        "relic_event": RelicEventModel(**result["relic_event"]),
    }


@app.post("/api/v1/relics/transfigure")
def transfigure_relic(req: RelicTransfigureRequest):
    relics = get_or_create_relics_records(soul_id=req.soul_id)
    target = next((r for r in relics if r["id"] == req.relic_id), None)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relic not found")

    transfigured_effect = f"TRANSFIGURED ANCHOR ({req.transfigured_form}): Permanently bridges Constellation Aspects and alters world canon."
    result = update_relic_stage_record(
        relic_id=req.relic_id,
        soul_id=req.soul_id,
        action="transfigure",
        new_stage="Transfigured",
        narrative_condition_met=f"Transfigured as Constellation Anchor: '{req.anchor_name}'.",
        chronicle_evidence_summary=f"Transfigured into mythic form '{req.transfigured_form}' across eras.",
        new_effect=transfigured_effect,
        is_anchor=True,
    )
    return {
        "relic": RelicModel(**result["relic"]),
        "relic_event": RelicEventModel(**result["relic_event"]),
    }


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
