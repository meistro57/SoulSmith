# backend/app/main.py
"""
SoulSmith FastAPI Main Application.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    Header,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.art_director import (
    ArtDirectionProfileModel,
    ArtDirectionProfileVersionModel,
    CompileArtDirectionSpecRequest,
    CreateArtDirectionProfileRequest,
    ResolveArtDirectionRequest,
    ResolvedArtDirectionModel,
    UpdateArtDirectionProfileRequest,
    apply_art_direction_to_prompt,
    compile_art_direction_spec,
    resolve_art_direction,
)
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
from app.biography import (
    BiographyModel,
    CompileBiographyRequest,
    project_biography_for_viewer,
    source_visible_to,
)
from app.biography_compiler import BiographyCompilationError, compile_biography
from app.campaign import (
    CampaignOpportunityModel,
    CampaignSessionModel,
    CampaignTransitionModel,
    CommitEventRequest,
    EvaluateOpportunitiesRequest,
    ResolveOpportunityRequest,
    StartSessionRequest,
)
from app.campaign_orchestrator import (
    CampaignOrchestratorError,
    commit_canonical_event,
    evaluate_opportunities,
    get_aftermath,
    get_pending_reviews,
    get_session_state,
    get_transition_provenance,
    inspect_opportunity,
    resolve_opportunity,
    start_or_resume_session,
)
from app.chronicle_paintings import (
    ChroniclePaintingModel,
    CreateChroniclePaintingRequest,
    GenerateChroniclePaintingRequest,
)
from app.comfyui.storage import get_asset_root
from app.comfyui.workflow_roles import select_world_workflow_role
from app.constellation import (
    AWAKENING_STAGE_DESCRIPTIONS,
    AdvanceAwakeningRequest,
    CreateAspectRequest,
    CreateBondRequest,
)
from app.convergence import (
    CanonForkRequest,
    CanonMergeRequest,
    CommunitySymbolModel,
    CreateCommunitySymbolRequest,
    GatheringContributeRequest,
    GatheringSessionModel,
)
from app.curiosity import (
    IntegrateThreadRequest,
    QuestionResolveRequest,
    SeedPlantRequest,
)
from app.db import (
    add_gallery_collection_item_record,
    add_gathering_contribution,
    add_group_memory_anchor_record,
    add_group_memory_member_record,
    add_group_memory_tag_record,
    add_legendary_figure_link_record,
    add_story_mark_record,
    approve_biography_transaction,
    approve_chronicle_painting_transaction,
    approve_portrait_candidate_transaction,
    approve_world_memory_record,
    approve_world_visual_candidate_transaction,
    compile_memory_object_record,
    create_art_direction_profile_record,
    create_art_direction_profile_version_record,
    create_aspect_record,
    create_community_symbol_record,
    create_cross_aspect_bond_record,
    create_gallery_collection_record,
    create_group_memory_record,
    create_legendary_figure_record,
    create_portrait_candidate_record,
    create_portrait_version_record,
    create_private_note_record,
    create_reflection_record,
    create_user_record,
    create_world_memory_placement_record,
    create_world_visual_candidate_record,
    execute_integration_event,
    get_all_canonical_events,
    get_all_local_threads,
    get_all_open_questions,
    get_all_seeds,
    get_approved_chronicle_paintings_records,
    get_art_direction_profile_record,
    get_art_direction_profile_version_record,
    get_biography_record,
    get_chronicle_painting_record,
    get_chronicle_paintings_records,
    get_community_symbols_records,
    get_current_art_direction_profile_record,
    get_current_biography_record,
    get_db_connection,
    get_gallery_collection_record,
    get_group_memory_anchors_records,
    get_group_memory_by_event_record,
    get_group_memory_members_records,
    get_group_memory_record,
    get_group_memory_tags_records,
    get_legendary_figure_record,
    get_memory_object_record,
    get_memory_objects_by_event_record,
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
    get_visual_entity_version_record,
    get_visual_entity_versions_records,
    get_world_memory_record,
    get_world_memory_state_history_records,
    get_world_visual_candidate_record,
    get_world_visual_candidates_records,
    init_database,
    list_art_direction_profile_versions_records,
    list_art_direction_profiles_records,
    list_biography_records,
    list_gallery_collections_records,
    list_group_memory_records,
    list_legendary_figures_records,
    list_world_memory_placements_records,
    list_world_memory_records,
    list_world_memory_versions_records,
    log_canonical_event,
    log_probable_path_record,
    mark_world_memory_state_record,
    plant_or_echo_seed,
    reject_biography_record,
    reject_chronicle_painting_record,
    reject_portrait_candidate_record,
    reject_world_memory_record,
    reject_world_visual_candidate_record,
    remove_gallery_collection_item_record,
    remove_group_memory_member_record,
    remove_group_memory_tag_record,
    reorder_gallery_collection_items_record,
    resolve_open_question,
    set_art_direction_profile_status_record,
    update_awakening_stage_record,
    update_candidate_generation_result,
    update_gallery_collection_record,
    update_group_memory_significance_record,
    update_preferences_record,
    update_probable_path_manifestation,
    update_relic_stage_record,
    update_world_visual_candidate_result,
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
from app.group_memories import (
    AddGroupAnchorRequest,
    AddGroupTagRequest,
    AttachMemoryObjectRequest,
    CreateGroupMemoryRequest,
    GroupMemoryModel,
    build_perspective_comparison,
    derive_group_significance,
    derive_members_from_memory_objects,
    derive_title_summary,
    project_group_for_viewer,
    suggest_related_by_similarity,
)
from app.painting_compiler import compile_chronicle_painting_scene
from app.painting_pipeline import (
    create_painting_attempt,
    generate_chronicle_painting,
)
from app.painting_provider import get_painting_provider
from app.painting_reference import (
    ParticipantResolutionError,
    resolve_historical_participants,
)
from app.phenomena import DEFAULT_ACTIVE_PHENOMENA, Phenomenon
from app.portrait_compiler import PromptCompilationResult, compile_portrait_prompt
from app.portrait_provider import (
    ProviderGenerationRequest,
    get_comfyui_status,
    get_portrait_provider,
)
from app.portrait_reference import SourcePortraitError, resolve_source_portrait
from app.probable_paths import (
    CreateProbablePathRequest,
    ExploreAlternateSceneRequest,
    ManifestPathRequest,
    ProbablePathModel,
    simulate_alternate_scene_exploration,
)
from app.reflection import (
    CreatePrivateNoteRequest,
    CreateReflectionRequest,
    PlayerPreferencesModel,
    PrivateNoteModel,
    ReflectionSessionModel,
    UpdatePreferencesRequest,
)
from app.relics import (
    RelicAttuneRequest,
    RelicAttuneResponse,
    RelicEventModel,
    RelicModel,
    RelicNarrativeAttuneRequest,
    RelicOverdrawRequest,
    RelicRepairRequest,
    RelicTransfigureRequest,
    process_relic_attunement,
)
from app.rules import ResolveSceneRequest, ResolveSceneResponse, evaluate_scene_outcome
from app.soulkeeper import SoulkeeperNarration, generate_soulkeeper_narration
from app.soulprint import (
    SoulprintProfile,
    SoulprintRequest,
    generate_astrological_soulprint,
)
from app.style_reviewer import get_art_direction_reviewer
from app.vision import PhotoIngestRequest, PhotoIngestResponse, process_dice_photo
from app.visual_compilers import compile_canonical_delta, compile_visual_prompt
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
from app.visual_world import (
    CreateWorldVisualCandidateRequest,
    GenerateWorldVisualCandidateRequest,
    VisualEntityVersionModel,
    WorldVisualCandidateModel,
)
from app.world_gallery import (
    AddGalleryCollectionItemRequest,
    CreateGalleryCollectionRequest,
    GalleryCollectionItemModel,
    GalleryCollectionModel,
    ReorderGalleryCollectionRequest,
    UpdateGalleryCollectionRequest,
    list_gallery_artifacts,
)
from app.world_memory import (
    CompileWorldMemoryRequest,
    LegendaryFigureModel,
    MarkMemoryStateRequest,
    NPCKnowledgeRequest,
    PlaceWorldMemoryRequest,
    PromoteLegendaryFigureRequest,
    WorldMemoryDeviationModel,
    WorldMemoryModel,
    WorldMemoryPlacementModel,
    project_npc_knowledge,
    project_world_memory_for_viewer,
    world_memory_visible_to,
)
from app.world_memory_compiler import (
    WorldMemoryCompilationError,
    compile_world_memory,
    gather_world_memory_sources,
)
from app.world_visual_provider import (
    WorldVisualGenerationRequest,
    get_world_visual_provider,
)


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

# Serve SoulSmith-owned generated assets (e.g. ComfyUI candidate portraits).
_asset_root = get_asset_root()
_asset_root.mkdir(parents=True, exist_ok=True)
app.mount("/assets", StaticFiles(directory=str(_asset_root)), name="assets")


class RoomManager:
    def __init__(self) -> None:
        self.rooms: dict[str, list[WebSocket]] = {}

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
def get_me(authorization: str | None = Header(None)):
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
def get_active_phenomena() -> list[Phenomenon]:
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
    try:
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
            importance_tier=req.importance_tier,
            importance_score=req.importance_score,
            importance_rationale=req.importance_rationale,
        )
        return {"memory_object": MemoryObjectModel(**record)}
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@app.get("/api/v1/visual/memory-objects")
def list_memory_objects():
    records = get_memory_objects_records()
    return {"memory_objects": [MemoryObjectModel(**r) for r in records]}


@app.get("/api/v1/visual/memory-objects/{memory_object_id}")
def get_memory_object(memory_object_id: str):
    record = get_memory_object_record(memory_object_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory object '{memory_object_id}' not found",
        )
    return {"memory_object": MemoryObjectModel(**record)}


# Phase 10: Portrait Generation & Continuity Endpoints


@app.get("/api/v1/visual-memory/providers/comfyui/status")
def comfyui_provider_status():
    return get_comfyui_status()


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

    try:
        source_version = resolve_source_portrait(
            req.soul_id, req.source_portrait_version_id
        )
    except SourcePortraitError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    ref_url = source_version["image_url"] if source_version else None

    compiled = compile_portrait_prompt(
        identity=identity,
        equipment=equipment,
        story_marks=story_marks,
        reference_image_url=ref_url,
        generation_type=req.generation_type,
        emotional_state=req.emotional_state,
        style_preset=req.style_preset,
    )

    profile_id, profile_version_id, final_prompt = _apply_art_direction_to_compiled(
        req.art_direction_profile_version_id,
        "portrait",
        compiled.compiled_prompt,
        canonical={"soul_id": req.soul_id, "identity": identity.model_dump()},
    )

    candidate = create_portrait_candidate_record(
        soul_id=req.soul_id,
        generation_type=req.generation_type,
        compiled_prompt=final_prompt,
        canonical_identity_snapshot=identity.model_dump(),
        story_marks_snapshot=[m.model_dump() for m in story_marks],
        equipment_snapshot=equipment.model_dump(),
        source_portrait_version_id=req.source_portrait_version_id,
        reference_image_url=ref_url,
        negative_prompt=", ".join(compiled.negative_constraints),
        art_direction_profile_id=profile_id,
        art_direction_profile_version_id=profile_version_id,
    )
    return {"candidate": PortraitGenerationCandidateModel(**candidate)}


@app.post("/api/v1/visual-memory/portraits/candidates/{candidate_id}/generate")
def generate_portrait_candidate_endpoint(
    candidate_id: str, req: GenerateCandidateRequest | None = None
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
        negative_prompt=candidate.get("negative_prompt"),
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


# Phase 4: Visual Worldsmith Endpoints


@app.post("/api/v1/visual-world/candidates")
def create_world_visual_candidate_endpoint(req: CreateWorldVisualCandidateRequest):
    source_version = None
    if req.source_visual_version_id:
        source_version = get_visual_entity_version_record(req.source_visual_version_id)
        if not source_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source visual version '{req.source_visual_version_id}' not found",
            )
        if (
            source_version["entity_id"] != req.entity_id
            or source_version["entity_type"] != req.entity_type
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source visual version does not match the requested entity",
            )

    previous_snapshot = source_version["canonical_snapshot"] if source_version else None
    compiled = compile_visual_prompt(
        entity_type=req.entity_type,
        name=req.name,
        canonical_state=req.canonical_state,
        generation_type=req.generation_type,
        previous_snapshot=previous_snapshot,
        style=req.style,
    )
    canonical_delta = compile_canonical_delta(previous_snapshot, req.canonical_state)
    workflow_role = select_world_workflow_role(req.entity_type, req.generation_type)

    profile_id, profile_version_id, final_prompt = _apply_art_direction_to_compiled(
        req.art_direction_profile_version_id,
        req.entity_type,
        compiled.compiled_prompt,
        canonical=req.canonical_state,
    )

    candidate = create_world_visual_candidate_record(
        entity_id=req.entity_id,
        entity_type=req.entity_type,
        generation_type=req.generation_type,
        canonical_snapshot=req.canonical_state,
        canonical_delta=canonical_delta,
        compiled_prompt=final_prompt,
        workflow_role=workflow_role,
        negative_prompt=", ".join(compiled.negative_constraints),
        source_visual_version_id=req.source_visual_version_id,
        reference_image_url=source_version["image_url"] if source_version else None,
        art_direction_profile_id=profile_id,
        art_direction_profile_version_id=profile_version_id,
    )
    return {"candidate": WorldVisualCandidateModel(**candidate)}


@app.post("/api/v1/visual-world/candidates/{candidate_id}/generate")
def generate_world_visual_candidate_endpoint(
    candidate_id: str, req: GenerateWorldVisualCandidateRequest | None = None
):
    candidate = get_world_visual_candidate_record(candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World visual candidate '{candidate_id}' not found",
        )

    provider = get_world_visual_provider((req and req.provider_type) or None)
    gen_req = WorldVisualGenerationRequest(
        candidate_id=candidate["candidate_id"],
        entity_id=candidate["entity_id"],
        entity_type=candidate["entity_type"],
        compiled_prompt=candidate["compiled_prompt"],
        workflow_role=candidate["workflow_role"],
        generation_type=candidate["generation_type"],
        negative_prompt=candidate.get("negative_prompt"),
        reference_image_url=candidate.get("reference_image_url"),
        seed=(req and req.seed) or None,
    )
    result = provider.generate(gen_req)

    if result.success:
        updated = update_world_visual_candidate_result(
            candidate_id=candidate_id,
            status="generated",
            generated_image_url=result.generated_image_url,
            provider=result.provider,
            provider_model=result.provider_model,
            provider_request_id=result.provider_request_id,
            generation_seed=result.generation_seed,
        )
    else:
        updated = update_world_visual_candidate_result(
            candidate_id=candidate_id,
            status="failed",
            provider=result.provider,
            provider_model=result.provider_model,
            failure_reason=result.failure_reason,
        )
    return {"candidate": WorldVisualCandidateModel(**updated)}


@app.post("/api/v1/visual-world/candidates/{candidate_id}/approve")
def approve_world_visual_candidate_endpoint(candidate_id: str):
    try:
        version = approve_world_visual_candidate_transaction(candidate_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    candidate = get_world_visual_candidate_record(candidate_id)
    return {
        "visual_version": VisualEntityVersionModel(**version),
        "candidate": WorldVisualCandidateModel(**candidate),
        "message": "Candidate approved and promoted to an immutable VisualEntityVersion.",
    }


@app.post("/api/v1/visual-world/candidates/{candidate_id}/reject")
def reject_world_visual_candidate_endpoint(candidate_id: str):
    try:
        updated = reject_world_visual_candidate_record(candidate_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {
        "candidate": WorldVisualCandidateModel(**updated),
        "message": "Candidate rejected. Canonical world state was untouched.",
    }


@app.get("/api/v1/visual-world/{entity_type}/{entity_id}/versions")
def list_visual_entity_versions_endpoint(entity_type: str, entity_id: str):
    records = get_visual_entity_versions_records(entity_type, entity_id)
    return {"versions": [VisualEntityVersionModel(**r) for r in records]}


@app.get("/api/v1/visual-world/{entity_type}/{entity_id}/candidates")
def list_world_visual_candidates_endpoint(entity_type: str, entity_id: str):
    records = get_world_visual_candidates_records(entity_type, entity_id)
    return {"candidates": [WorldVisualCandidateModel(**r) for r in records]}


# Phase 12: Chronicle Paintings + Visual Canon Guardian


def _resolve_memory_for_painting(memory_object_id: str) -> MemoryObjectModel:
    record = get_memory_object_record(memory_object_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory object '{memory_object_id}' not found",
        )
    return MemoryObjectModel(**record)


@app.post("/api/v1/chronicle-paintings")
def create_chronicle_painting_endpoint(req: CreateChroniclePaintingRequest):
    memory_object = _resolve_memory_for_painting(req.memory_object_id)

    try:
        participants = resolve_historical_participants(memory_object)
    except ParticipantResolutionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    scene_spec = compile_chronicle_painting_scene(
        memory_object=memory_object,
        participants=participants,
        composition=req.composition,
        style=req.style,
    )
    historical_refs = [
        {
            "soul_id": p.soul_id,
            "character_name": p.character_name,
            "portrait_version_id": p.portrait_version_id,
            "identity_strategy": p.identity_strategy,
            "portrait_image_url": p.portrait_image_url,
        }
        for p in participants
    ]

    profile_id, profile_version_id, resolved = _resolve_art_direction_profile(
        req.art_direction_profile_version_id, "chronicle_painting"
    )

    painting = create_painting_attempt(
        memory_object=memory_object,
        scene_spec=scene_spec,
        historical_participant_refs=historical_refs,
        generation_type=req.generation_type,
        composition=scene_spec.composition,
        source_painting_id=req.source_painting_id,
        art_direction_profile_id=profile_id,
        art_direction_profile_version_id=profile_version_id,
        resolved_art_direction=resolved,
    )
    return {"painting": painting}


@app.post("/api/v1/chronicle-paintings/{painting_id}/generate")
def generate_chronicle_painting_endpoint(
    painting_id: str, req: GenerateChroniclePaintingRequest | None = None
):
    painting_record = get_chronicle_painting_record(painting_id)
    if not painting_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Painting '{painting_id}' not found",
        )
    memory_object = _resolve_memory_for_painting(painting_record["memory_object_id"])

    result = generate_chronicle_painting(
        painting_id,
        memory_object,
        provider_type=(req and req.provider_type) or None,
        seed=(req and req.seed) or None,
    )
    return {"painting": result}


@app.post("/api/v1/chronicle-paintings/{painting_id}/approve")
def approve_chronicle_painting_endpoint(painting_id: str):
    try:
        approved = approve_chronicle_painting_transaction(painting_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {
        "painting": ChroniclePaintingModel(**approved),
        "message": "Painting approved as the preferred artistic interpretation.",
    }


@app.post("/api/v1/chronicle-paintings/{painting_id}/reject")
def reject_chronicle_painting_endpoint(painting_id: str):
    try:
        rejected = reject_chronicle_painting_record(painting_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {
        "painting": ChroniclePaintingModel(**rejected),
        "message": "Painting rejected. Canonical memory was untouched.",
    }


@app.get("/api/v1/chronicle-paintings/gallery")
def list_approved_chronicle_paintings_endpoint():
    records = get_approved_chronicle_paintings_records()
    return {"paintings": records}


@app.get("/api/v1/chronicle-paintings/providers/capabilities")
def chronicle_painting_provider_capabilities_endpoint():
    provider = get_painting_provider(None)
    return {"capabilities": provider.capabilities()}


@app.get("/api/v1/chronicle-paintings/{painting_id}")
def get_chronicle_painting_endpoint(painting_id: str):
    record = get_chronicle_painting_record(painting_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Painting '{painting_id}' not found",
        )
    return {"painting": ChroniclePaintingModel(**record)}


@app.get("/api/v1/chronicle-paintings")
def list_chronicle_paintings_endpoint(memory_object_id: str | None = None):
    if memory_object_id:
        records = get_chronicle_paintings_records(memory_object_id)
    else:
        records = get_approved_chronicle_paintings_records()
    return {"paintings": [ChroniclePaintingModel(**r) for r in records]}


# Phase 13: Group Memories & Tags


def _resolve_group_memory(group_id: str) -> dict:
    group = get_group_memory_record(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group memory '{group_id}' not found",
        )
    return group


def _project_group(group_id: str, viewer_soul_id: str | None) -> GroupMemoryModel:
    group = _resolve_group_memory(group_id)
    members = get_group_memory_members_records(group_id)
    tags = get_group_memory_tags_records(group_id)
    anchors = get_group_memory_anchors_records(group_id)
    return project_group_for_viewer(
        group=group,
        members=members,
        tags=tags,
        anchors=anchors,
        viewer_soul_id=viewer_soul_id,
    )


def _refresh_group_derived_fields(group_id: str) -> None:
    members = get_group_memory_members_records(group_id)
    memory_objects = []
    for member in members:
        record = get_memory_object_record(member["memory_object_id"])
        if record:
            memory_objects.append(record)

    significance, score, rationale = derive_group_significance(memory_objects)
    update_group_memory_significance_record(
        group_id,
        significance=significance,
        score=score,
        rationale=rationale,
    )


@app.post("/api/v1/group-memories")
def create_group_memory_endpoint(req: CreateGroupMemoryRequest):
    existing = get_group_memory_by_event_record(req.event_id)
    if existing:
        return {"group_memory": _project_group(existing["group_id"], None)}

    title, summary = derive_title_summary([])
    group = create_group_memory_record(
        event_id=req.event_id,
        visibility=req.visibility,
        title=title,
        summary=summary,
    )

    for memory_object_id in req.memory_object_ids:
        record = get_memory_object_record(memory_object_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Memory object '{memory_object_id}' not found",
            )
        if record["event_id"] != req.event_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Memory object '{memory_object_id}' belongs to event "
                    f"'{record['event_id']}', not '{req.event_id}'"
                ),
            )
        members = derive_members_from_memory_objects([record])
        if members:
            add_group_memory_member_record(
                group_id=group["group_id"],
                memory_object_id=memory_object_id,
                soul_id=members[0]["soul_id"],
                role_in_event=members[0]["role_in_event"],
                portrait_version_id=members[0]["portrait_version_id"],
            )

    _refresh_group_derived_fields(group["group_id"])
    return {"group_memory": _project_group(group["group_id"], None)}


@app.post("/api/v1/group-memories/auto-group")
def auto_group_memories_endpoint(event_id: str):
    """
    Deterministically group Memory Objects by exact shared event ID. Never by
    name, tag, date, or semantic similarity.
    """
    memory_objects = get_memory_objects_by_event_record(event_id)
    if not memory_objects:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No memory objects found for event '{event_id}'",
        )

    existing = get_group_memory_by_event_record(event_id)
    if existing:
        return {
            "group_memory": _project_group(existing["group_id"], None),
            "grouped": False,
            "message": "Group memory already exists for this event.",
        }

    title, summary = derive_title_summary(memory_objects)
    group = create_group_memory_record(event_id=event_id, title=title, summary=summary)
    members = derive_members_from_memory_objects(memory_objects)
    for member in members:
        add_group_memory_member_record(
            group_id=group["group_id"],
            memory_object_id=member["memory_object_id"],
            soul_id=member["soul_id"],
            role_in_event=member["role_in_event"],
            portrait_version_id=member["portrait_version_id"],
        )

    _refresh_group_derived_fields(group["group_id"])
    return {
        "group_memory": _project_group(group["group_id"], None),
        "grouped": True,
        "message": f"Grouped {len(members)} memory object(s) by exact event ID.",
    }


@app.get("/api/v1/group-memories")
def list_group_memories_endpoint(viewer_soul_id: str | None = None):
    records = list_group_memory_records()
    projected = []
    for record in records:
        view = _project_group(record["group_id"], viewer_soul_id)
        # Only surface group memories with at least one visible member.
        if view.members:
            projected.append(view)
    return {"group_memories": [g.model_dump() for g in projected]}


@app.get("/api/v1/group-memories/by-event/{event_id}")
def get_group_memory_by_event_endpoint(
    event_id: str, viewer_soul_id: str | None = None
):
    group = get_group_memory_by_event_record(event_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No group memory found for event '{event_id}'",
        )
    return {"group_memory": _project_group(group["group_id"], viewer_soul_id)}


@app.get("/api/v1/group-memories/related")
def find_related_group_memories_endpoint(
    anchor_type: str | None = None,
    anchor_ref: str | None = None,
    tag_type: str | None = None,
    tag_value: str | None = None,
    viewer_soul_id: str | None = None,
):
    results: set[str] = set()
    if anchor_type and anchor_ref:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT group_id FROM group_memory_anchors "
            "WHERE anchor_type = ? AND anchor_ref = ?",
            (anchor_type, anchor_ref),
        )
        results.update(row["group_id"] for row in cursor.fetchall())
        conn.close()
    if tag_type or tag_value:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT group_id FROM group_memory_tags WHERE 1=1"
        params: list[str] = []
        if tag_type:
            query += " AND tag_type = ?"
            params.append(tag_type)
        if tag_value:
            query += " AND value = ?"
            params.append(tag_value)
        cursor.execute(query, params)
        results.update(row["group_id"] for row in cursor.fetchall())
        conn.close()

    projected = []
    for group_id in sorted(results):
        projected.append(_project_group(group_id, viewer_soul_id))
    return {"group_memories": [g.model_dump() for g in projected]}


@app.get("/api/v1/group-memories/{group_id}")
def get_group_memory_endpoint(group_id: str, viewer_soul_id: str | None = None):
    return {"group_memory": _project_group(group_id, viewer_soul_id)}


@app.post("/api/v1/group-memories/{group_id}/members")
def attach_memory_object_endpoint(group_id: str, req: AttachMemoryObjectRequest):
    group = _resolve_group_memory(group_id)
    record = get_memory_object_record(req.memory_object_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory object '{req.memory_object_id}' not found",
        )
    if record["event_id"] != group["event_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Memory object '{req.memory_object_id}' belongs to event "
                f"'{record['event_id']}', not '{group['event_id']}'"
            ),
        )

    add_group_memory_member_record(
        group_id=group_id,
        memory_object_id=req.memory_object_id,
        soul_id=req.soul_id,
        role_in_event=req.role_in_event,
        portrait_version_id=req.portrait_version_id,
    )
    _refresh_group_derived_fields(group_id)
    return {"group_memory": _project_group(group_id, None)}


@app.delete("/api/v1/group-memories/{group_id}/members/{memory_object_id}")
def detach_memory_object_endpoint(group_id: str, memory_object_id: str):
    _resolve_group_memory(group_id)
    removed = remove_group_memory_member_record(group_id, memory_object_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory object '{memory_object_id}' is not a member of '{group_id}'",
        )
    _refresh_group_derived_fields(group_id)
    # The Memory Object itself is never deleted.
    record = get_memory_object_record(memory_object_id)
    return {
        "group_memory": _project_group(group_id, None),
        "memory_object_still_exists": record is not None,
    }


@app.post("/api/v1/group-memories/{group_id}/tags")
def add_group_tag_endpoint(group_id: str, req: AddGroupTagRequest):
    _resolve_group_memory(group_id)
    tag = add_group_memory_tag_record(
        group_id=group_id,
        tag_type=req.tag_type,
        value=req.value,
        anchor_kind=req.anchor_kind,
        anchor_id=req.anchor_id,
        is_descriptor=req.is_descriptor,
    )
    return {"tag": tag}


@app.delete("/api/v1/group-memories/{group_id}/tags/{tag_id}")
def remove_group_tag_endpoint(group_id: str, tag_id: str):
    _resolve_group_memory(group_id)
    removed = remove_group_memory_tag_record(group_id, tag_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag '{tag_id}' not found in group '{group_id}'",
        )
    return {"removed": True}


@app.post("/api/v1/group-memories/{group_id}/anchors")
def add_group_anchor_endpoint(group_id: str, req: AddGroupAnchorRequest):
    _resolve_group_memory(group_id)
    label = req.label
    entity_id = None
    entity_type = None

    if req.anchor_type == "portrait":
        portrait = get_portrait_version_record(req.anchor_ref)
        if not portrait:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Portrait version '{req.anchor_ref}' not found",
            )
        entity_id = portrait["soul_id"]
        entity_type = "portrait"
        label = label or portrait.get("label", req.anchor_ref)
    elif req.anchor_type in ("location", "relic", "phenomenon"):
        version = get_visual_entity_version_record(req.anchor_ref)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Visual entity version '{req.anchor_ref}' not found",
            )
        if version["entity_type"] != req.anchor_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Visual version '{req.anchor_ref}' is type "
                    f"'{version['entity_type']}', not '{req.anchor_type}'"
                ),
            )
        entity_id = version["entity_id"]
        entity_type = version["entity_type"]
        label = label or version.get("label", req.anchor_ref)
    elif req.anchor_type == "chronicle_painting":
        painting = get_chronicle_painting_record(req.anchor_ref)
        if not painting:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Chronicle painting '{req.anchor_ref}' not found",
            )
        entity_id = painting["memory_object_id"]
        entity_type = "chronicle_painting"
        label = label or painting.get("composition", req.anchor_ref)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported anchor type '{req.anchor_type}'",
        )

    anchor = add_group_memory_anchor_record(
        group_id=group_id,
        anchor_type=req.anchor_type,
        anchor_ref=req.anchor_ref,
        entity_id=entity_id,
        entity_type=entity_type,
        label=label,
    )
    return {"anchor": anchor}


@app.get("/api/v1/group-memories/{group_id}/anchors")
def get_group_anchors_endpoint(group_id: str):
    _resolve_group_memory(group_id)
    return {"anchors": get_group_memory_anchors_records(group_id)}


@app.get("/api/v1/group-memories/{group_id}/perspectives")
def get_group_perspectives_endpoint(group_id: str, viewer_soul_id: str | None = None):
    group = _resolve_group_memory(group_id)
    members = get_group_memory_members_records(group_id)
    comparison = build_perspective_comparison(
        group_id=group_id,
        event_id=group["event_id"],
        members=members,
        viewer_soul_id=viewer_soul_id,
    )
    return comparison


@app.get("/api/v1/group-memories/suggestions/{memory_object_id}")
def suggest_related_memories_endpoint(memory_object_id: str):
    suggestions = suggest_related_by_similarity(memory_object_id=memory_object_id)
    return {"suggestions": [s.model_dump() for s in suggestions]}


# Phase 14: Living Biography


def _project_biography(biography: dict, viewer_soul_id: str | None) -> BiographyModel:
    projected = project_biography_for_viewer(biography, viewer_soul_id)
    return BiographyModel(**projected)


@app.post("/api/v1/biographies/compile")
def compile_biography_endpoint(req: CompileBiographyRequest):
    try:
        result = compile_biography(
            soul_id=req.soul_id,
            viewer_soul_id=req.viewer_soul_id,
            visibility=req.visibility,
            scope_type=req.scope_type,
            scope_ref=req.scope_ref,
        )
    except BiographyCompilationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    biography = _project_biography(result["biography"], req.viewer_soul_id)
    return {
        "biography": biography.model_dump(),
        "guardian_report": result["guardian_report"],
    }


@app.get("/api/v1/biographies/current")
def get_current_biography_endpoint(
    soul_id: str = "Kaelen the Star-Watcher",
    viewer_soul_id: str | None = None,
):
    biography = get_current_biography_record(soul_id)
    if not biography:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No current biography found for soul '{soul_id}'.",
        )
    return {"biography": _project_biography(biography, viewer_soul_id).model_dump()}


@app.get("/api/v1/biographies/history")
def list_biography_history_endpoint(soul_id: str = "Kaelen the Star-Watcher"):
    records = list_biography_records(soul_id)
    return {"biographies": records}


@app.get("/api/v1/biographies/{biography_id}")
def get_biography_endpoint(biography_id: str, viewer_soul_id: str | None = None):
    biography = get_biography_record(biography_id)
    if not biography:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Biography '{biography_id}' not found",
        )
    return {"biography": _project_biography(biography, viewer_soul_id).model_dump()}


@app.post("/api/v1/biographies/{biography_id}/approve")
def approve_biography_endpoint(
    biography_id: str, soul_id: str = "Kaelen the Star-Watcher"
):
    try:
        biography = approve_biography_transaction(biography_id, soul_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {
        "biography": _project_biography(biography, soul_id).model_dump(),
        "message": "Biography approved as current.",
    }


@app.post("/api/v1/biographies/{biography_id}/reject")
def reject_biography_endpoint(
    biography_id: str, soul_id: str = "Kaelen the Star-Watcher"
):
    try:
        biography = reject_biography_record(biography_id, soul_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {
        "biography": _project_biography(biography, soul_id).model_dump(),
        "message": "Biography rejected. Canonical Chronicle was untouched.",
    }


@app.get("/api/v1/biographies/{biography_id}/sections/{section_id}/provenance")
def get_biography_section_provenance_endpoint(
    biography_id: str,
    section_id: str,
    viewer_soul_id: str | None = None,
):
    biography = get_biography_record(biography_id)
    if not biography:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Biography '{biography_id}' not found",
        )
    section = next(
        (s for s in biography["sections"] if s["section_id"] == section_id), None
    )
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Section '{section_id}' not found in biography '{biography_id}'",
        )
    visible = [
        ref
        for ref in section["provenance"]
        if source_visible_to(ref["source_type"], ref["source_id"], viewer_soul_id)
    ]
    return {"provenance": visible, "section": section}


# Phase 15: Art Director & World Gallery


def _resolve_art_direction_profile(
    profile_version_id: str | None, artifact_type: str
) -> tuple[str | None, str | None, ResolvedArtDirectionModel | None]:
    """
    Resolve an optional profile version into (profile_id, version_id, resolved).
    Returns (None, None, None) when no profile was requested.
    """
    if not profile_version_id:
        return None, None, None
    version_record = get_art_direction_profile_version_record(profile_version_id)
    if not version_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Art direction profile version '{profile_version_id}' not found",
        )
    version = ArtDirectionProfileVersionModel(**version_record)
    resolved = resolve_art_direction(version, artifact_type)  # type: ignore[arg-type]
    return version.profile_id, version.version_id, resolved


def _apply_art_direction_to_compiled(
    profile_version_id: str | None,
    artifact_type: str,
    compiled_prompt: str,
    canonical: dict,
) -> tuple[str | None, str | None, str]:
    """Resolve a profile and append its treatment to a compiled prompt."""
    profile_id, version_id, resolved = _resolve_art_direction_profile(
        profile_version_id, artifact_type
    )
    if resolved is None:
        return None, None, compiled_prompt
    return (
        profile_id,
        version_id,
        apply_art_direction_to_prompt(compiled_prompt, resolved),
    )


@app.post("/api/v1/art-direction/profiles")
def create_art_direction_profile_endpoint(req: CreateArtDirectionProfileRequest):
    result = create_art_direction_profile_record(
        name=req.name,
        description=req.description,
        medium_style=req.medium_style,
        palette_guidance=req.palette_guidance,
        lighting_guidance=req.lighting_guidance,
        atmosphere=req.atmosphere,
        texture_material=req.texture_material,
        camera_framing=req.camera_framing,
        composition_guidance=req.composition_guidance,
        portrait_treatment=req.portrait_treatment,
        environment_treatment=req.environment_treatment,
        relic_treatment=req.relic_treatment,
        phenomenon_treatment=req.phenomenon_treatment,
        chronicle_treatment=req.chronicle_treatment,
        negative_guidance=req.negative_guidance,
        provider_hints=req.provider_hints,
        accessibility_notes=req.accessibility_notes,
    )
    return {
        "profile": ArtDirectionProfileModel(**result["profile"]),
        "version": ArtDirectionProfileVersionModel(**result["version"]),
    }


@app.get("/api/v1/art-direction/profiles")
def list_art_direction_profiles_endpoint():
    return {
        "profiles": [
            ArtDirectionProfileModel(**p) for p in list_art_direction_profiles_records()
        ]
    }


@app.get("/api/v1/art-direction/profiles/{profile_id}")
def get_art_direction_profile_endpoint(profile_id: str):
    profile = get_art_direction_profile_record(profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Art direction profile '{profile_id}' not found",
        )
    versions = [
        ArtDirectionProfileVersionModel(**v)
        for v in list_art_direction_profile_versions_records(profile_id)
    ]
    return {
        "profile": ArtDirectionProfileModel(**profile),
        "versions": versions,
    }


@app.get("/api/v1/art-direction/profiles/{profile_id}/versions")
def list_art_direction_profile_versions_endpoint(profile_id: str):
    profile = get_art_direction_profile_record(profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Art direction profile '{profile_id}' not found",
        )
    return {
        "versions": [
            ArtDirectionProfileVersionModel(**v)
            for v in list_art_direction_profile_versions_records(profile_id)
        ]
    }


@app.post("/api/v1/art-direction/profiles/{profile_id}/versions")
def create_art_direction_profile_version_endpoint(
    profile_id: str, req: UpdateArtDirectionProfileRequest
):
    profile = get_art_direction_profile_record(profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Art direction profile '{profile_id}' not found",
        )
    version = create_art_direction_profile_version_record(
        profile_id=profile_id,
        medium_style=req.medium_style,
        palette_guidance=req.palette_guidance,
        lighting_guidance=req.lighting_guidance,
        atmosphere=req.atmosphere,
        texture_material=req.texture_material,
        camera_framing=req.camera_framing,
        composition_guidance=req.composition_guidance,
        portrait_treatment=req.portrait_treatment,
        environment_treatment=req.environment_treatment,
        relic_treatment=req.relic_treatment,
        phenomenon_treatment=req.phenomenon_treatment,
        chronicle_treatment=req.chronicle_treatment,
        negative_guidance=req.negative_guidance,
        provider_hints=req.provider_hints,
        accessibility_notes=req.accessibility_notes,
    )
    return {"version": ArtDirectionProfileVersionModel(**version)}


@app.post("/api/v1/art-direction/profiles/{profile_id}/status")
def set_art_direction_profile_status_endpoint(profile_id: str, status_value: str):
    profile = get_art_direction_profile_record(profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Art direction profile '{profile_id}' not found",
        )
    if status_value not in ("draft", "current", "superseded", "archived"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid profile status '{status_value}'",
        )
    updated = set_art_direction_profile_status_record(profile_id, status_value)
    return {"profile": ArtDirectionProfileModel(**updated)}


@app.get("/api/v1/art-direction/current")
def get_current_art_direction_endpoint():
    profile = get_current_art_direction_profile_record()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No current Art Direction Profile is set.",
        )
    version = (
        get_art_direction_profile_version_record(profile["current_version_id"])
        if profile.get("current_version_id")
        else None
    )
    return {
        "profile": ArtDirectionProfileModel(**profile),
        "version": ArtDirectionProfileVersionModel(**version) if version else None,
    }


@app.post("/api/v1/art-direction/resolve")
def resolve_art_direction_endpoint(req: ResolveArtDirectionRequest):
    version_record = get_art_direction_profile_version_record(req.profile_version_id)
    if not version_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Art direction profile version '{req.profile_version_id}' not found",
        )
    version = ArtDirectionProfileVersionModel(**version_record)
    resolved = resolve_art_direction(version, req.artifact_type, req.override)  # type: ignore[arg-type]
    return {"resolved": resolved}


@app.post("/api/v1/art-direction/preview")
def compile_art_direction_spec_endpoint(req: CompileArtDirectionSpecRequest):
    version_record = get_art_direction_profile_version_record(req.profile_version_id)
    if not version_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Art direction profile version '{req.profile_version_id}' not found",
        )
    version = ArtDirectionProfileVersionModel(**version_record)
    capabilities = get_painting_provider(None).capabilities()
    spec = compile_art_direction_spec(
        artifact_type=req.artifact_type,
        profile_version=version,
        canonical=req.canonical,
        historical_references=req.historical_references,
        provider_capabilities=capabilities,
        composition_intent=req.composition_intent,
        accessibility=req.accessibility,
        override=req.override,
    )
    return {"spec": spec}


@app.post("/api/v1/art-direction/review")
def review_style_endpoint(req: ResolveArtDirectionRequest):
    version_record = get_art_direction_profile_version_record(req.profile_version_id)
    if not version_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Art direction profile version '{req.profile_version_id}' not found",
        )
    version = ArtDirectionProfileVersionModel(**version_record)
    resolved = resolve_art_direction(version, req.artifact_type, req.override)  # type: ignore[arg-type]
    reviewer = get_art_direction_reviewer()
    result = reviewer.review(resolved=resolved)
    return {"style_review": result}


# World Gallery


@app.get("/api/v1/gallery")
def list_gallery_artifacts_endpoint(
    viewer_soul_id: str | None = None,
    mode: str = "all",
    entity_type: str | None = None,
    entity_id: str | None = None,
):
    artifacts = list_gallery_artifacts(
        viewer_soul_id=viewer_soul_id,
        mode=mode,  # type: ignore[arg-type]
        entity_type=entity_type,
        entity_id=entity_id,
    )
    return {"artifacts": [a.model_dump() for a in artifacts]}


@app.get("/api/v1/gallery/timeline")
def gallery_timeline_endpoint(
    entity_type: str, entity_id: str, viewer_soul_id: str | None = None
):
    from app.world_gallery import build_timeline

    return {
        "artifacts": [
            a.model_dump()
            for a in build_timeline(
                viewer_soul_id=viewer_soul_id,
                entity_type=entity_type,
                entity_id=entity_id,
            )
        ]
    }


@app.post("/api/v1/gallery/collections")
def create_gallery_collection_endpoint(req: CreateGalleryCollectionRequest):
    collection = create_gallery_collection_record(
        title=req.title,
        description=req.description,
        visibility=req.visibility,
        curator_soul_id=req.curator_soul_id,
    )
    return {"collection": GalleryCollectionModel(**collection)}


@app.get("/api/v1/gallery/collections")
def list_gallery_collections_endpoint():
    return {
        "collections": [
            GalleryCollectionModel(**c) for c in list_gallery_collections_records()
        ]
    }


@app.get("/api/v1/gallery/collections/{collection_id}")
def get_gallery_collection_endpoint(collection_id: str):
    collection = get_gallery_collection_record(collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{collection_id}' not found",
        )
    return {"collection": GalleryCollectionModel(**collection)}


@app.patch("/api/v1/gallery/collections/{collection_id}")
def update_gallery_collection_endpoint(
    collection_id: str, req: UpdateGalleryCollectionRequest
):
    try:
        collection = update_gallery_collection_record(
            collection_id,
            title=req.title,
            description=req.description,
            visibility=req.visibility,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return {"collection": GalleryCollectionModel(**collection)}


@app.post("/api/v1/gallery/collections/{collection_id}/items")
def add_gallery_collection_item_endpoint(
    collection_id: str, req: AddGalleryCollectionItemRequest
):
    collection = get_gallery_collection_record(collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{collection_id}' not found",
        )
    item = add_gallery_collection_item_record(
        collection_id=collection_id,
        artifact_type=req.artifact_type,
        artifact_ref=req.artifact_ref,
        caption=req.caption,
        position=req.position,
    )
    return {"item": GalleryCollectionItemModel(**item)}


@app.delete("/api/v1/gallery/collections/{collection_id}/items/{item_id}")
def remove_gallery_collection_item_endpoint(collection_id: str, item_id: str):
    removed = remove_gallery_collection_item_record(collection_id, item_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item '{item_id}' not found in collection '{collection_id}'",
        )
    return {"removed": True}


@app.post("/api/v1/gallery/collections/{collection_id}/reorder")
def reorder_gallery_collection_endpoint(
    collection_id: str, req: ReorderGalleryCollectionRequest
):
    collection = get_gallery_collection_record(collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{collection_id}' not found",
        )
    updated = reorder_gallery_collection_items_record(
        collection_id, req.ordered_item_ids
    )
    return {"collection": GalleryCollectionModel(**updated)}


# Phase 16: Legendary Figures & World Memory


def _project_world_memory(memory: dict, viewer_soul_id: str | None) -> WorldMemoryModel:
    projected = project_world_memory_for_viewer(memory, viewer_soul_id)
    return WorldMemoryModel(**projected)


@app.post("/api/v1/world-memory/compile")
def compile_world_memory_endpoint(req: CompileWorldMemoryRequest):
    try:
        result = compile_world_memory(
            subject_entity_type=req.subject_entity_type,
            subject_entity_id=req.subject_entity_id,
            culture=req.culture,
            era_context=req.era_context,
            memory_form=req.memory_form,
            interpretation_type=req.interpretation_type,
            remembrance_scale=req.remembrance_scale,
            visibility=req.visibility,
            perspective=req.perspective,
            viewer_soul_id=req.viewer_soul_id,
        )
    except WorldMemoryCompilationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    memory = _project_world_memory(result["memory"], req.viewer_soul_id)
    return {"memory": memory.model_dump(), "guardian_report": result["guardian_report"]}


@app.get("/api/v1/world-memory")
def list_world_memory_endpoint(
    viewer_soul_id: str | None = None,
    subject_entity_type: str | None = None,
    subject_entity_id: str | None = None,
    culture: str | None = None,
    era_context: str | None = None,
    memory_form: str | None = None,
    memory_state: str | None = None,
):
    records = list_world_memory_records(
        subject_entity_type=subject_entity_type,
        subject_entity_id=subject_entity_id,
        culture=culture,
        era_context=era_context,
        memory_form=memory_form,
        memory_state=memory_state,
    )
    return {
        "memories": [
            _project_world_memory(m, viewer_soul_id).model_dump()
            for m in records
            if world_memory_visible_to(m, viewer_soul_id)
        ]
    }


@app.get("/api/v1/world-memory/{memory_id}")
def get_world_memory_endpoint(memory_id: str, viewer_soul_id: str | None = None):
    memory = get_world_memory_record(memory_id)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World memory '{memory_id}' not found",
        )
    return {"memory": _project_world_memory(memory, viewer_soul_id).model_dump()}


@app.get("/api/v1/world-memory/{memory_id}/versions")
def list_world_memory_versions_endpoint(
    memory_id: str, viewer_soul_id: str | None = None
):
    memory = get_world_memory_record(memory_id)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World memory '{memory_id}' not found",
        )
    versions = list_world_memory_versions_records(
        memory["subject_entity_type"],
        memory["subject_entity_id"],
        memory["culture"],
        memory["memory_form"],
    )
    return {
        "versions": [
            _project_world_memory(v, viewer_soul_id).model_dump() for v in versions
        ]
    }


@app.get("/api/v1/world-memory/{memory_id}/deviations")
def get_world_memory_deviations_endpoint(
    memory_id: str, viewer_soul_id: str | None = None
):
    memory = get_world_memory_record(memory_id)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World memory '{memory_id}' not found",
        )
    if not world_memory_visible_to(memory, viewer_soul_id):
        return {"deviations": [], "provenance": []}
    return {
        "deviations": [WorldMemoryDeviationModel(**d) for d in memory["deviations"]],
        "provenance": memory["source_refs"],
    }


@app.get("/api/v1/world-memory/query")
def query_world_memory_endpoint(
    subject_entity_type: str,
    subject_entity_id: str,
    culture: str | None = None,
    era_context: str | None = None,
    viewer_soul_id: str | None = None,
):
    records = list_world_memory_records(
        subject_entity_type=subject_entity_type,
        subject_entity_id=subject_entity_id,
        culture=culture,
        era_context=era_context,
    )
    return {
        "memories": [
            _project_world_memory(m, viewer_soul_id).model_dump()
            for m in records
            if world_memory_visible_to(m, viewer_soul_id)
        ]
    }


@app.post("/api/v1/world-memory/{memory_id}/approve")
def approve_world_memory_endpoint(memory_id: str, viewer_soul_id: str | None = None):
    try:
        memory = approve_world_memory_record(memory_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {
        "memory": _project_world_memory(memory, viewer_soul_id).model_dump(),
        "message": "World Memory approved as current. Canonical Chronicle was untouched.",
    }


@app.post("/api/v1/world-memory/{memory_id}/reject")
def reject_world_memory_endpoint(memory_id: str, viewer_soul_id: str | None = None):
    try:
        memory = reject_world_memory_record(memory_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {
        "memory": _project_world_memory(memory, viewer_soul_id).model_dump(),
        "message": "World Memory rejected. Canonical Chronicle was untouched.",
    }


@app.post("/api/v1/world-memory/{memory_id}/mark-state")
def mark_world_memory_state_endpoint(
    memory_id: str, req: MarkMemoryStateRequest, viewer_soul_id: str | None = None
):
    try:
        memory = mark_world_memory_state_record(memory_id, req.new_state, req.reason)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {
        "memory": _project_world_memory(memory, viewer_soul_id).model_dump(),
        "message": f"World Memory state marked '{req.new_state}'. Canon was not deleted.",
    }


@app.get("/api/v1/world-memory/{memory_id}/state-history")
def get_world_memory_state_history_endpoint(memory_id: str):
    memory = get_world_memory_record(memory_id)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World memory '{memory_id}' not found",
        )
    return {"history": get_world_memory_state_history_records(memory_id)}


@app.post("/api/v1/world-memory/{memory_id}/placements")
def place_world_memory_endpoint(memory_id: str, req: PlaceWorldMemoryRequest):
    memory = get_world_memory_record(memory_id)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World memory '{memory_id}' not found",
        )
    placement = create_world_memory_placement_record(
        memory_id=memory_id,
        placement_type=req.placement_type,
        placement_ref=req.placement_ref,
        visibility=req.visibility,
    )
    return {"placement": WorldMemoryPlacementModel(**placement)}


@app.get("/api/v1/world-memory/{memory_id}/placements")
def list_world_memory_placements_endpoint(memory_id: str):
    memory = get_world_memory_record(memory_id)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World memory '{memory_id}' not found",
        )
    return {
        "placements": [
            WorldMemoryPlacementModel(**p)
            for p in list_world_memory_placements_records(memory_id)
        ]
    }


@app.post("/api/v1/world-memory/npc-knowledge")
def project_npc_knowledge_endpoint(req: NPCKnowledgeRequest):
    records = list_world_memory_records(
        subject_entity_type=req.subject_entity_type,
        subject_entity_id=req.subject_entity_id,
    )
    projection = project_npc_knowledge(
        subject_entity_type=req.subject_entity_type,
        subject_entity_id=req.subject_entity_id,
        npc=req,
        memories=records,
    )
    return {"knowledge": projection.model_dump()}


@app.post("/api/v1/legendary-figures/promote")
def promote_legendary_figure_endpoint(req: PromoteLegendaryFigureRequest):
    from app.world_memory import evaluate_legendary_eligibility

    gathered = gather_world_memory_sources(
        subject_entity_type=req.subject_entity_type,
        subject_entity_id=req.subject_entity_id,
        viewer_soul_id=None,
    )
    eligible, scale, rationale = evaluate_legendary_eligibility(
        subject_entity_type=req.subject_entity_type,
        subject_entity_id=req.subject_entity_id,
        memory_objects=gathered["memory_objects"],
        group_significance=gathered["group_significance"],
    )
    if not eligible:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Subject '{req.subject_entity_id}' is not eligible for "
            "Legendary Figure status. " + rationale,
        )
    figure = create_legendary_figure_record(
        subject_soul_id=req.subject_soul_id,
        subject_entity_type=req.subject_entity_type,
        subject_entity_id=req.subject_entity_id,
        figure_title=req.figure_title,
        later_cultural_titles=req.later_cultural_titles,
        remembrance_scale=req.remembrance_scale or scale,
        memory_state=req.memory_state,
        eligibility_rationale=rationale,
    )
    # Link canonical identity/portrait/biography sources without copying them.
    for ref in gathered["source_refs"]:
        add_legendary_figure_link_record(
            figure_id=figure["figure_id"],
            link_type=_link_type_for_source(ref.source_type),
            link_ref=ref.source_id,
            link_label=ref.source_type,
            is_canonical=True,
        )
    for title in req.later_cultural_titles:
        add_legendary_figure_link_record(
            figure_id=figure["figure_id"],
            link_type="monument",
            link_ref=title,
            link_label=title,
            is_canonical=False,
        )
    return {
        "figure": LegendaryFigureModel(
            **get_legendary_figure_record(figure["figure_id"])
        )
    }


def _link_type_for_source(source_type: str) -> str:
    return {
        "memory_object": "chronicle_event",
        "biography": "biography",
        "portrait_version": "portrait",
        "story_mark": "story_mark",
        "relic_event": "relic",
        "chronicle_painting": "artwork",
    }.get(source_type, "identity")


@app.get("/api/v1/legendary-figures")
def list_legendary_figures_endpoint():
    return {
        "figures": [LegendaryFigureModel(**f) for f in list_legendary_figures_records()]
    }


@app.get("/api/v1/legendary-figures/{figure_id}")
def get_legendary_figure_endpoint(figure_id: str):
    figure = get_legendary_figure_record(figure_id)
    if not figure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Legendary figure '{figure_id}' not found",
        )
    return {"figure": LegendaryFigureModel(**figure)}


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


# Phase 17: Campaign Orchestrator endpoints. These coordinate existing systems;
# they never re-implement domain rules or mutate canon directly.


def _orchestrator_error(exc: CampaignOrchestratorError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@app.post("/api/v1/campaign/session")
def start_campaign_session(req: StartSessionRequest):
    return start_or_resume_session(soul_id=req.soul_id, campaign_id=req.campaign_id)


@app.get("/api/v1/campaign/session/{session_id}")
def get_campaign_session(session_id: str):
    try:
        state = get_session_state(session_id)
    except CampaignOrchestratorError as exc:
        raise _orchestrator_error(exc)
    return {
        "session": CampaignSessionModel(**state["session"]).model_dump(),
        "opportunities": [
            CampaignOpportunityModel(**o).model_dump() for o in state["opportunities"]
        ],
        "transitions": [
            CampaignTransitionModel(**t).model_dump() for t in state["transitions"]
        ],
    }


@app.post("/api/v1/campaign/opportunities/evaluate")
def evaluate_campaign_opportunities(req: EvaluateOpportunitiesRequest):
    try:
        result = evaluate_opportunities(
            session_id=req.session_id, include_encounter=req.include_encounter
        )
    except CampaignOrchestratorError as exc:
        raise _orchestrator_error(exc)
    return {
        "session_id": result["session_id"],
        "silence": result["silence"],
        "opportunities": [
            CampaignOpportunityModel(**o).model_dump() for o in result["opportunities"]
        ],
    }


@app.post("/api/v1/campaign/opportunities/{opportunity_id}/resolve")
def resolve_campaign_opportunity(opportunity_id: str, req: ResolveOpportunityRequest):
    session = _session_for_opportunity(opportunity_id)
    try:
        result = resolve_opportunity(
            session_id=session,
            opportunity_id=opportunity_id,
            decision=req.decision,
            recognition=req.recognition,
            player_intent=req.player_intent,
            note=req.note,
        )
    except CampaignOrchestratorError as exc:
        raise _orchestrator_error(exc)
    return {
        "transition": CampaignTransitionModel(**result["transition"]).model_dump(),
        "opportunity": CampaignOpportunityModel(**result["opportunity"]).model_dump(),
        "idempotent": result["idempotent"],
    }


def _session_for_opportunity(opportunity_id: str) -> str:
    from app.db import get_campaign_opportunity_record

    opportunity = get_campaign_opportunity_record(opportunity_id)
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunity '{opportunity_id}' not found",
        )
    return opportunity["session_id"]


@app.post("/api/v1/campaign/commit")
def commit_campaign_event(req: CommitEventRequest):
    try:
        result = commit_canonical_event(
            session_id=req.session_id, event_id=req.event_id
        )
    except CampaignOrchestratorError as exc:
        raise _orchestrator_error(exc)
    return {
        "transition": CampaignTransitionModel(**result["transition"]).model_dump(),
        "opportunities": [
            CampaignOpportunityModel(**o).model_dump() for o in result["opportunities"]
        ],
        "idempotent": result["idempotent"],
    }


@app.get("/api/v1/campaign/transitions/{transition_id}/provenance")
def get_campaign_transition_provenance(transition_id: str):
    try:
        return get_transition_provenance(transition_id)
    except CampaignOrchestratorError as exc:
        raise _orchestrator_error(exc)


@app.get("/api/v1/campaign/session/{session_id}/reviews")
def get_campaign_pending_reviews(session_id: str):
    try:
        reviews = get_pending_reviews(session_id)
    except CampaignOrchestratorError as exc:
        raise _orchestrator_error(exc)
    return {
        "pending_reviews": [
            CampaignOpportunityModel(**o).model_dump()
            for o in reviews["pending_reviews"]
        ]
    }


@app.get("/api/v1/campaign/session/{session_id}/aftermath")
def get_campaign_aftermath(session_id: str):
    try:
        return get_aftermath(session_id)
    except CampaignOrchestratorError as exc:
        raise _orchestrator_error(exc)


@app.get("/api/v1/campaign/opportunities/{opportunity_id}/inspect")
def inspect_campaign_opportunity(opportunity_id: str):
    try:
        return inspect_opportunity(opportunity_id)
    except CampaignOrchestratorError as exc:
        raise _orchestrator_error(exc)
