# backend/app/main.py
"""
SoulSmith FastAPI Main Application.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Dict, List, Optional

from fastapi import (
    FastAPI,
    Header,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
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
    add_gathering_contribution,
    add_story_mark_record,
    approve_portrait_candidate_transaction,
    compile_memory_object_record,
    create_community_symbol_record,
    create_portrait_candidate_record,
    create_portrait_version_record,
    create_private_note_record,
    create_reflection_record,
    execute_integration_event,
    get_all_canonical_events,
    get_all_local_threads,
    get_all_open_questions,
    get_all_seeds,
    get_community_symbols_records,
    get_memory_objects_records,
    get_or_create_avatar_identity_record,
    get_or_create_equipment_appearance_record,
    get_or_create_gathering_session,
    get_or_create_preferences_record,
    get_or_create_primary_constellation,
    get_or_create_relics_records,
    get_or_create_visual_consent_record,
    get_portrait_candidate_record,
    get_portrait_candidates_records,
    get_portrait_version_record,
    get_portrait_versions_records,
    get_private_notes_records,
    get_probable_paths_records,
    get_reflections_records,
    get_relic_history_records,
    get_story_marks_records,
    get_user_by_email,
    get_user_by_username,
    init_database,
    log_canonical_event,
    log_probable_path_record,
    plant_or_echo_seed,
    reject_portrait_candidate_record,
    resolve_open_question,
    update_awakening_stage_record,
    update_candidate_generation_result,
    update_preferences_record,
    update_probable_path_manifestation,
    update_relic_stage_record,
)
from app.visual_memory import (
    AddStoryMarkRequest,
    ApproveCandidateRequest,
    AvatarIdentityModel,
    CompileMemoryObjectRequest,
    CompilePortraitPromptRequest,
    ConsentSettingsModel,
    CreateAvatarIdentityRequest,
    CreatePortraitCandidateRequest,
    CreatePortraitVersionRequest,
    EquipmentAppearanceModel,
    GenerateCandidateRequest,
    MemoryObjectModel,
    PortraitGenerationCandidateModel,
    PortraitVersionModel,
    RejectCandidateRequest,
    StoryMarkModel,
)
from app.portrait_compiler import compile_portrait_prompt, PromptCompilationResult
from app.portrait_provider import get_portrait_provider, ProviderGenerationRequest
from app.reflection import (
    CreatePrivateNoteRequest,
    CreateReflectionRequest,
    PlayerPreferencesModel,
    PrivateNoteModel,
    ReflectionSessionModel,
    UpdatePreferencesRequest,
)
from app.convergence import (
    CanonForkRequest,
    CanonMergeRequest,
    CommunitySymbolModel,
    CreateCommunitySymbolRequest,
    GatheringContributeRequest,
    GatheringSessionModel,
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
    user_record = get_user_by_email(req.username_or_email) or get_user_by_username(
        req.username_or_email
    )
    if not user_record or not verify_password(
        req.password, user_record["password_hash"]
    ):
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
    stage_info = AWAKENING_STAGE_DESCRIPTIONS.get(
        constellation["awakening_stage"],
        {
            "title": constellation["awakening_stage"].capitalize(),
            "description": "The Constellation patterns unfold across Aspects.",
        },
    )
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Relic not found"
        )

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Relic not found"
        )

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Relic not found"
        )

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Relic not found"
        )

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


# Phase 7: Convergence & Community Mythology Endpoints


@app.get("/api/v1/convergence/symbols")
def list_community_symbols():
    records = get_community_symbols_records()
    return {"symbols": [CommunitySymbolModel(**r) for r in records]}


@app.post("/api/v1/convergence/symbols/create")
def create_community_symbol(req: CreateCommunitySymbolRequest):
    record = create_community_symbol_record(
        symbol_name=req.symbol_name,
        description=req.description,
        contributing_souls=req.contributing_souls,
        canon_status=req.canon_status,
    )
    return {"symbol": CommunitySymbolModel(**record)}


@app.get("/api/v1/convergence/gatherings/{room_id}")
def get_gathering_session(
    room_id: str, phenomenon_name: str = "Awakening of the Salt Spire"
):
    record = get_or_create_gathering_session(
        room_id=room_id, phenomenon_name=phenomenon_name
    )
    return {"gathering": GatheringSessionModel(**record)}


@app.post("/api/v1/convergence/gatherings/contribute")
def contribute_to_gathering(req: GatheringContributeRequest):
    try:
        result = add_gathering_contribution(
            gathering_id=req.gathering_id,
            contributor_soul=req.contributor_soul,
            role=req.role,
            resonance_amount=req.resonance_amount,
            notes=req.notes,
        )
        return {
            "gathering": GatheringSessionModel(**result["gathering"]),
            "latest_contribution": result["latest_contribution"],
        }
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))


@app.post("/api/v1/convergence/canon/merge")
def merge_shared_canon(req: CanonMergeRequest):
    symbol_record = create_community_symbol_record(
        symbol_name=req.symbol_name,
        description=req.description,
        contributing_souls=req.consenting_souls,
        canon_status="public_canon",
    )
    return {
        "success": True,
        "canon_merge_summary": f"Shared phenomenon '{req.symbol_name}' merged into public world canon with consent from {len(req.consenting_souls)} Souls.",
        "symbol": CommunitySymbolModel(**symbol_record),
    }


@app.post("/api/v1/convergence/canon/fork")
def fork_private_canon(req: CanonForkRequest):
    return {
        "success": True,
        "fork_summary": f"Soul '{req.forking_soul}' forked shared gathering '{req.gathering_id}' into a private timeline branch. Reason: {req.reason}.",
    }


# Phase 8: Reflection & Accessibility Endpoints


@app.get("/api/v1/reflection/preferences")
def get_player_preferences(soul_id: str = "Kaelen the Star-Watcher"):
    record = get_or_create_preferences_record(soul_id=soul_id)
    return {"preferences": PlayerPreferencesModel(**record)}


@app.post("/api/v1/reflection/preferences")
def update_player_preferences(req: UpdatePreferencesRequest):
    record = update_preferences_record(
        req.soul_id,
        narrative_intensity=req.narrative_intensity,
        spiritual_framing=req.spiritual_framing,
        reduced_motion=req.reduced_motion,
        high_contrast=req.high_contrast,
        allow_ai_indexing_default=req.allow_ai_indexing_default,
    )
    return {"preferences": PlayerPreferencesModel(**record)}


@app.get("/api/v1/reflection/sessions")
def list_reflection_sessions(soul_id: str = "Kaelen the Star-Watcher"):
    records = get_reflections_records(soul_id=soul_id)
    return {"sessions": [ReflectionSessionModel(**r) for r in records]}


@app.post("/api/v1/reflection/sessions/create")
def create_reflection_session(req: CreateReflectionRequest):
    record = create_reflection_record(
        soul_id=req.soul_id,
        prompt_question=req.prompt_question,
        player_reflection=req.player_reflection,
        share_with_ai=req.share_with_ai,
    )
    return {"session": ReflectionSessionModel(**record)}


@app.get("/api/v1/reflection/notes")
def list_private_notes(soul_id: str = "Kaelen the Star-Watcher"):
    records = get_private_notes_records(soul_id=soul_id)
    return {"notes": [PrivateNoteModel(**r) for r in records]}


@app.post("/api/v1/reflection/notes/create")
def create_private_note(req: CreatePrivateNoteRequest):
    record = create_private_note_record(
        soul_id=req.soul_id,
        title=req.title,
        content=req.content,
        allow_ai_indexing=req.allow_ai_indexing,
    )
    return {"note": PrivateNoteModel(**record)}


# Phase 9: Visual Identity Foundation & Memory Objects Endpoints


@app.get("/api/v1/visual/avatar/{soul_id}")
def get_visual_avatar_profile(soul_id: str):
    identity = get_or_create_avatar_identity_record(soul_id=soul_id)
    story_marks = get_story_marks_records(soul_id=soul_id)
    equipment = get_or_create_equipment_appearance_record(soul_id=soul_id)
    portraits = get_portrait_versions_records(soul_id=soul_id)
    consent = get_or_create_visual_consent_record(soul_id=soul_id)
    return {
        "identity": AvatarIdentityModel(**identity),
        "story_marks": [StoryMarkModel(**m) for m in story_marks],
        "equipment": EquipmentAppearanceModel(**equipment),
        "portraits": [PortraitVersionModel(**p) for p in portraits],
        "consent": ConsentSettingsModel(**consent),
    }


@app.post("/api/v1/visual/avatar/create")
def create_avatar_identity(req: CreateAvatarIdentityRequest):
    record = get_or_create_avatar_identity_record(
        soul_id=req.soul_id,
        face=req.face,
        hair=req.hair,
        body=req.body,
        species=req.species,
        eyes=req.eyes,
    )
    return {"identity": AvatarIdentityModel(**record)}


@app.post("/api/v1/visual/story-marks/add")
def add_story_mark(req: AddStoryMarkRequest):
    record = add_story_mark_record(
        soul_id=req.soul_id,
        mark_type=req.mark_type,
        location=req.location,
        origin_event_id=req.origin_event_id,
        acquired_at=req.acquired_at,
        visibility=req.visibility,
        status=req.status,
    )
    return {"story_mark": StoryMarkModel(**record)}


@app.post("/api/v1/visual/portraits/snapshot")
def create_portrait_snapshot(req: CreatePortraitVersionRequest):
    record = create_portrait_version_record(
        soul_id=req.soul_id,
        label=req.label,
        image_url=req.image_url,
    )
    return {"portrait": PortraitVersionModel(**record)}


@app.post("/api/v1/visual/memory-objects/compile")
def compile_memory_object(req: CompileMemoryObjectRequest):
    record = compile_memory_object_record(
        event_id=req.event_id,
        event_title=req.event_title,
        participants=[p.model_dump() for p in req.participants],
        location_environment=req.location_environment,
        relics_involved=req.relics_involved,
        emotional_tone=req.emotional_tone,
        action_composition=req.action_composition,
        lasting_consequence=req.lasting_consequence,
        privacy_consent_scope=req.privacy_consent_scope,
    )
    return {"memory_object": MemoryObjectModel(**record)}


@app.get("/api/v1/visual/memory-objects")
def list_memory_objects():
    records = get_memory_objects_records()
    return {"memory_objects": [MemoryObjectModel(**r) for r in records]}


# Phase 10: Portrait Generation & Continuity Endpoints


@app.post(
    "/api/v1/visual-memory/portraits/compile",
    response_model=PromptCompilationResult,
)
def compile_portrait_prompt_endpoint(req: CompilePortraitPromptRequest):
    identity_dict = get_or_create_avatar_identity_record(soul_id=req.soul_id)
    story_marks_list = get_story_marks_records(soul_id=req.soul_id)
    equipment_dict = get_or_create_equipment_appearance_record(soul_id=req.soul_id)

    identity = AvatarIdentityModel(**identity_dict)
    story_marks = [StoryMarkModel(**m) for m in story_marks_list]
    equipment = EquipmentAppearanceModel(**equipment_dict)

    ref_url = None
    if req.source_portrait_version_id:
        source_pv = get_portrait_version_record(req.source_portrait_version_id)
        if source_pv:
            ref_url = source_pv["image_url"]

    result = compile_portrait_prompt(
        identity=identity,
        equipment=equipment,
        story_marks=story_marks,
        reference_image_url=ref_url,
        generation_type=req.generation_type,
        emotional_state=req.emotional_state,
        style_preset=req.style_preset,
    )
    return result


@app.post("/api/v1/visual-memory/portraits/candidates")
def create_portrait_candidate_endpoint(req: CreatePortraitCandidateRequest):
    identity_dict = get_or_create_avatar_identity_record(soul_id=req.soul_id)
    story_marks_list = get_story_marks_records(soul_id=req.soul_id)
    equipment_dict = get_or_create_equipment_appearance_record(soul_id=req.soul_id)

    identity = AvatarIdentityModel(**identity_dict)
    story_marks = [StoryMarkModel(**m) for m in story_marks_list]
    equipment = EquipmentAppearanceModel(**equipment_dict)

    ref_url = None
    if req.source_portrait_version_id:
        source_pv = get_portrait_version_record(req.source_portrait_version_id)
        if source_pv:
            ref_url = source_pv["image_url"]

    compiled = compile_portrait_prompt(
        identity=identity,
        equipment=equipment,
        story_marks=story_marks,
        reference_image_url=ref_url,
        generation_type=req.generation_type,
        emotional_state=req.emotional_state,
        style_preset=req.style_preset,
    )

    candidate = create_portrait_candidate_record(
        soul_id=req.soul_id,
        generation_type=req.generation_type,
        compiled_prompt=compiled.compiled_prompt,
        canonical_identity_snapshot=identity.model_dump(),
        story_marks_snapshot=[m.model_dump() for m in story_marks],
        equipment_snapshot=equipment.model_dump(),
        source_portrait_version_id=req.source_portrait_version_id,
        reference_image_url=ref_url,
        negative_prompt=", ".join(compiled.negative_constraints),
    )
    return {"candidate": PortraitGenerationCandidateModel(**candidate)}


@app.post("/api/v1/visual-memory/portraits/candidates/{candidate_id}/generate")
def generate_portrait_candidate_endpoint(
    candidate_id: str, req: Optional[GenerateCandidateRequest] = None
):
    candidate = get_portrait_candidate_record(candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{candidate_id}' not found",
        )

    provider_type = (req and req.provider_type) or None
    seed = (req and req.seed) or None

    provider = get_portrait_provider(provider_type)
    gen_req = ProviderGenerationRequest(
        candidate_id=candidate["candidate_id"],
        soul_id=candidate["soul_id"],
        compiled_prompt=candidate["compiled_prompt"],
        generation_type=candidate["generation_type"],
        reference_image_url=candidate.get("reference_image_url"),
        seed=seed,
    )

    result = provider.generate(gen_req)

    if result.success:
        updated = update_candidate_generation_result(
            candidate_id=candidate_id,
            status="generated",
            generated_image_url=result.generated_image_url,
            provider=result.provider,
            provider_model=result.provider_model,
            provider_request_id=result.provider_request_id,
            generation_seed=result.generation_seed,
        )
    else:
        updated = update_candidate_generation_result(
            candidate_id=candidate_id,
            status="failed",
            provider=result.provider,
            provider_model=result.provider_model,
            failure_reason=result.failure_reason,
        )

    return {"candidate": PortraitGenerationCandidateModel(**updated)}


@app.post("/api/v1/visual-memory/portraits/candidates/{candidate_id}/approve")
def approve_portrait_candidate_endpoint(
    candidate_id: str, req: ApproveCandidateRequest
):
    candidate = get_portrait_candidate_record(candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{candidate_id}' not found",
        )

    if candidate["soul_id"] != req.soul_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Candidate '{candidate_id}' does not belong to soul '{req.soul_id}'",
        )

    if candidate["status"] == "approved":
        pv = get_portrait_version_record(candidate["resulting_portrait_version_id"])
        return {
            "portrait_version": PortraitVersionModel(**pv),
            "candidate": PortraitGenerationCandidateModel(**candidate),
            "message": "Candidate was already approved (idempotent response).",
        }

    if candidate["status"] != "generated":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve candidate in state '{candidate['status']}'. Must be in 'generated' state.",
        )

    try:
        pv_dict = approve_portrait_candidate_transaction(
            candidate_id, soul_id=req.soul_id, custom_label=req.label
        )
        updated_cand = get_portrait_candidate_record(candidate_id)
        return {
            "portrait_version": PortraitVersionModel(**pv_dict),
            "candidate": PortraitGenerationCandidateModel(**updated_cand),
            "message": "Candidate approved and promoted to canonical PortraitVersion.",
        }
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@app.post("/api/v1/visual-memory/portraits/candidates/{candidate_id}/reject")
def reject_portrait_candidate_endpoint(candidate_id: str, req: RejectCandidateRequest):
    candidate = get_portrait_candidate_record(candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{candidate_id}' not found",
        )

    if candidate["soul_id"] != req.soul_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Candidate '{candidate_id}' does not belong to soul '{req.soul_id}'",
        )

    if candidate["status"] == "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reject a candidate that has already been approved into canon.",
        )

    try:
        updated = reject_portrait_candidate_record(candidate_id, soul_id=req.soul_id)
        return {
            "candidate": PortraitGenerationCandidateModel(**updated),
            "message": "Candidate rejected. Saved in audit log without mutating canon.",
        }
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@app.get("/api/v1/visual-memory/portraits/candidates")
def list_portrait_candidates_endpoint(
    soul_id: str = "Kaelen the Star-Watcher",
):
    records = get_portrait_candidates_records(soul_id=soul_id)
    return {"candidates": [PortraitGenerationCandidateModel(**r) for r in records]}


@app.get("/api/v1/visual-memory/portraits/candidates/{candidate_id}")
def get_portrait_candidate_endpoint(candidate_id: str):
    record = get_portrait_candidate_record(candidate_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{candidate_id}' not found",
        )
    return {"candidate": PortraitGenerationCandidateModel(**record)}


@app.get("/api/v1/visual-memory/portraits/versions")
def list_portrait_versions_endpoint(soul_id: str = "Kaelen the Star-Watcher"):
    records = get_portrait_versions_records(soul_id=soul_id)
    return {"portrait_versions": [PortraitVersionModel(**r) for r in records]}


@app.get("/api/v1/visual-memory/portraits/versions/{version_id}")
def get_portrait_version_endpoint(version_id: str):
    record = get_portrait_version_record(version_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portrait version '{version_id}' not found",
        )
    return {"portrait_version": PortraitVersionModel(**record)}


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
