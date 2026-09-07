import type { AlternateSceneResult, ArtDirectionProfile, ArtDirectionProfileVersion, ArtDirectionSpec, ArtifactType, Aspect, AuthResponse, AvatarIdentity, AwakeningStage, Biography, BiographyGuardianReport, BiographySection, BiographySourceRef, CampaignOpportunity, CampaignSession, CampaignTransition, CanonStatus, CanonicalDiceRead, ChroniclePainting, CommunitySymbol, Constellation, ConstellationStageInfo, CrossAspectBond, EncounterFrame, GalleryArtifact, GalleryCollection, GalleryCollectionItem, GatheringContribution, GatheringSession, GenerationType, GroupAnchorType, GroupMemory, GroupMemoryAnchor, GroupMemoryTag, GroupTagType, IntegrationEvent, LegendaryFigure, LocalThread, ManifestationType, MemoryObject, NarrativeGeneration, NarrativeIntensity, NPCKnowledgeProjection, NumericDiceRoll, OpenQuestion, ParticipantRef, PerspectiveComparison, PlayerPreferences, PortraitGenerationCandidate, PortraitVersion, PrivateNote, ProbablePath, ProbablePathStatus, PromptCompilationResult, ProviderCapabilities, RecognitionDecision, ReflectionSession, RelatedMemorySuggestion, Relic, RelicEvent, ResolvedArtDirection, ResolvedScene, Seed, SoulResources, SoulprintProfile, SpiritualFraming, StoryMark, StyleReviewResult, User, VisualAvatarProfile, VisualEntityVersion, WorldEntityType, WorldMemory, WorldMemoryPlacement, WorldVisualCandidate } from '../types';

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '');
const AUTH_TOKEN_KEY = 'soulsmith_auth_token';

/**
 * Resolve a SoulSmith-owned asset path (e.g. "/assets/portraits/candidates/x.png")
 * against the backend origin so generated images load regardless of which origin
 * serves the frontend. Absolute and data URLs are passed through unchanged.
 */
export function resolveAssetUrl(path: string | null | undefined): string {
  if (!path) return '';
  if (/^https?:\/\//i.test(path) || path.startsWith('data:') || path.startsWith('blob:')) {
    return path;
  }
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
}

export function getStoredAuthToken(): string | null {
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

export function setStoredAuthToken(token: string): void {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function removeStoredAuthToken(): void {
  localStorage.removeItem(AUTH_TOKEN_KEY);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getStoredAuthToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init?.headers as Record<string, string> ?? {}),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `SoulSmith API ${response.status}: ${response.statusText}`;
    try {
      const errBody = await response.json();
      if (errBody?.detail) errorDetail = errBody.detail;
    } catch {
      // fallback
    }
    throw new Error(errorDetail);
  }
  return response.json() as Promise<T>;
}

export const apiClient = {
  // Auth
  signup: (payload: { email: string; username: string; password: string; display_name: string }) => request<AuthResponse>('/api/v1/auth/signup', { method: 'POST', body: JSON.stringify(payload) }),
  login: (payload: { username_or_email: string; password: string }) => request<AuthResponse>('/api/v1/auth/login', { method: 'POST', body: JSON.stringify(payload) }),
  getMe: () => request<User>('/api/v1/auth/me'),

  // Game Engine
  rollDice: (seed?: number | string) => request<CanonicalDiceRead>('/api/v1/dice/roll', { method: 'POST', body: JSON.stringify(seed === undefined ? {} : { seed }) }),
  interpretDice: (roll: NumericDiceRoll) => request<CanonicalDiceRead>('/api/v1/dice/interpret', { method: 'POST', body: JSON.stringify(roll) }),
  frameEncounter: (payload: { dice_read: CanonicalDiceRead; soul_name: string; world_context?: string[] }) => request<EncounterFrame>('/api/v1/encounters/frame', { method: 'POST', body: JSON.stringify(payload) }),
  ingestDicePhoto: <T>() => request<T>('/api/v1/dice/photo-ingest', { method: 'POST', body: JSON.stringify({ expected_set: 'standard_mythic_v1' }) }),
  resolveScene: (payload: { dice_read: CanonicalDiceRead; chosen_approach: string; resonance_spent: number; strain_accepted: number; player_intent: string; soul_name: string; resources: SoulResources }) => request<ResolvedScene>('/api/v1/scenes/resolve', { method: 'POST', body: JSON.stringify(payload) }),
  previewSoulprint: (payload: unknown) => request<SoulprintProfile>('/api/v1/soulprints/preview', { method: 'POST', body: JSON.stringify(payload) }),
  listPhenomena: <T>() => request<T>('/api/v1/phenomena'),
  listSeeds: () => request<{ seeds: Seed[] }>('/api/v1/curiosity/seeds'),
  plantSeed: (payload: { symbol: string; thread_type: string; narrative_context: string; soul_id?: string; initial_question?: string }) => request<Seed>('/api/v1/curiosity/seeds/plant', { method: 'POST', body: JSON.stringify(payload) }),
  listQuestions: () => request<{ questions: OpenQuestion[] }>('/api/v1/curiosity/questions'),
  resolveQuestion: (payload: { question_id: string; resolution_notes: string; status?: string }) => request<{ success: boolean }>('/api/v1/curiosity/questions/resolve', { method: 'POST', body: JSON.stringify(payload) }),
  listThreads: (soulName = 'Unbound Soul') => request<{ threads: LocalThread[] }>(`/api/v1/curiosity/threads?soul_name=${encodeURIComponent(soulName)}`),
  integrateThread: (payload: { thread_id: string; soul_name: string; choice_made: string; target_relic_id?: string }) => request<IntegrationEvent>('/api/v1/curiosity/integrate', { method: 'POST', body: JSON.stringify(payload) }),
  getConstellation: () => request<{ constellation: Constellation; stage_info: ConstellationStageInfo }>('/api/v1/constellation'),
  createAspect: (payload: { constellation_id: string; aspect_name: string; calling: string; origin: string; era_or_world: string }) => request<{ aspect: Aspect }>('/api/v1/constellation/aspects/create', { method: 'POST', body: JSON.stringify(payload) }),
  createCrossAspectBond: (payload: { constellation_id: string; source_aspect_id: string; target_aspect_id: string; bond_type: string; description: string }) => request<{ bond: CrossAspectBond }>('/api/v1/constellation/bonds/create', { method: 'POST', body: JSON.stringify(payload) }),
  advanceAwakening: (payload: { constellation_id: string; target_stage?: AwakeningStage }) => request<{ awakening_stage: AwakeningStage }>('/api/v1/constellation/advance', { method: 'POST', body: JSON.stringify(payload) }),
  listProbablePaths: (soulName = 'Kaelen the Star-Watcher') => request<{ probable_paths: ProbablePath[] }>(`/api/v1/probable-paths?soul_id=${encodeURIComponent(soulName)}`),
  logProbablePath: (payload: { soul_id: string; path_title: string; chosen_path: string; unchosen_approach: string; potential_outcome_class?: string; manifestation_type?: ManifestationType; provenance_summary?: string }) => request<{ probable_path: ProbablePath }>('/api/v1/probable-paths/log', { method: 'POST', body: JSON.stringify(payload) }),
  manifestProbablePath: (payload: { path_id: string; manifestation_type: ManifestationType; status?: ProbablePathStatus }) => request<{ probable_path: ProbablePath }>('/api/v1/probable-paths/manifest', { method: 'POST', body: JSON.stringify(payload) }),
  exploreProbablePath: (payload: { path_id: string; soul_name: string }) => request<{ alternate_scene: AlternateSceneResult }>('/api/v1/probable-paths/explore', { method: 'POST', body: JSON.stringify(payload) }),

  // Relic Recognition
  listRelics: (soulId = 'Kaelen the Star-Watcher') => request<{ relics: Relic[] }>(`/api/v1/relics?soul_id=${encodeURIComponent(soulId)}`),
  getRelicHistory: (relicId: string) => request<{ history: RelicEvent[] }>(`/api/v1/relics/${relicId}/history`),
  attuneRelicNarrative: (payload: { relic_id: string; soul_id?: string; narrative_condition_met: string; chronicle_evidence_summary: string }) => request<{ relic: Relic; relic_event: RelicEvent }>('/api/v1/relics/attune-narrative', { method: 'POST', body: JSON.stringify(payload) }),
  overdrawRelic: (payload: { relic_id: string; soul_id?: string; intensity_boost?: string }) => request<{ relic: Relic; relic_event: RelicEvent }>('/api/v1/relics/overdraw', { method: 'POST', body: JSON.stringify(payload) }),
  repairRelic: (payload: { relic_id: string; soul_id?: string; repair_evidence_summary: string }) => request<{ relic: Relic; relic_event: RelicEvent }>('/api/v1/relics/repair', { method: 'POST', body: JSON.stringify(payload) }),
  transfigureRelic: (payload: { relic_id: string; soul_id?: string; anchor_name: string; transfigured_form: string }) => request<{ relic: Relic; relic_event: RelicEvent }>('/api/v1/relics/transfigure', { method: 'POST', body: JSON.stringify(payload) }),

  // Convergence & Community Mythology
  listCommunitySymbols: () => request<{ symbols: CommunitySymbol[] }>('/api/v1/convergence/symbols'),
  createCommunitySymbol: (payload: { symbol_name: string; description: string; contributing_souls?: string[]; canon_status?: CanonStatus }) => request<{ symbol: CommunitySymbol }>('/api/v1/convergence/symbols/create', { method: 'POST', body: JSON.stringify(payload) }),
  getGatheringSession: (roomId = 'convergence_alpha', phenomenonName = 'Awakening of the Salt Spire') => request<{ gathering: GatheringSession }>(`/api/v1/convergence/gatherings/${encodeURIComponent(roomId)}?phenomenon_name=${encodeURIComponent(phenomenonName)}`),
  contributeToGathering: (payload: { gathering_id: string; contributor_soul: string; role: 'Focus' | 'Anchor' | 'Witness' | 'Tempest'; resonance_amount: number; notes: string }) => request<{ gathering: GatheringSession; latest_contribution: GatheringContribution }>('/api/v1/convergence/gatherings/contribute', { method: 'POST', body: JSON.stringify(payload) }),
  mergeSharedCanon: (payload: { gathering_id: string; symbol_name: string; description: string; consenting_souls: string[] }) => request<{ success: boolean; canon_merge_summary: string; symbol: CommunitySymbol }>('/api/v1/convergence/canon/merge', { method: 'POST', body: JSON.stringify(payload) }),
  forkPrivateCanon: (payload: { gathering_id: string; forking_soul: string; reason: string }) => request<{ success: boolean; fork_summary: string }>('/api/v1/convergence/canon/fork', { method: 'POST', body: JSON.stringify(payload) }),

  // Reflection & Accessibility
  getPlayerPreferences: (soulId = 'Kaelen the Star-Watcher') => request<{ preferences: PlayerPreferences }>(`/api/v1/reflection/preferences?soul_id=${encodeURIComponent(soulId)}`),
  updatePlayerPreferences: (payload: { soul_id?: string; narrative_intensity?: NarrativeIntensity; spiritual_framing?: SpiritualFraming; reduced_motion?: boolean; high_contrast?: boolean; allow_ai_indexing_default?: boolean }) => request<{ preferences: PlayerPreferences }>('/api/v1/reflection/preferences', { method: 'POST', body: JSON.stringify(payload) }),
  listReflectionSessions: (soulId = 'Kaelen the Star-Watcher') => request<{ sessions: ReflectionSession[] }>(`/api/v1/reflection/sessions?soul_id=${encodeURIComponent(soulId)}`),
  createReflectionSession: (payload: { soul_id?: string; prompt_question: string; player_reflection: string; share_with_ai?: boolean }) => request<{ session: ReflectionSession }>('/api/v1/reflection/sessions/create', { method: 'POST', body: JSON.stringify(payload) }),
  listPrivateNotes: (soulId = 'Kaelen the Star-Watcher') => request<{ notes: PrivateNote[] }>(`/api/v1/reflection/notes?soul_id=${encodeURIComponent(soulId)}`),
  createPrivateNote: (payload: { soul_id?: string; title: string; content: string; allow_ai_indexing?: boolean }) => request<{ note: PrivateNote }>('/api/v1/reflection/notes/create', { method: 'POST', body: JSON.stringify(payload) }),

  // Visual Identity Foundation & Memory Objects
  getVisualAvatarProfile: (soulId = 'Kaelen the Star-Watcher') => request<VisualAvatarProfile>(`/api/v1/visual/avatar/${encodeURIComponent(soulId)}`),
  createAvatarIdentity: (payload: { soul_id?: string; face?: string; hair?: string; body?: string; species?: string; eyes?: string }) => request<{ identity: AvatarIdentity }>('/api/v1/visual/avatar/create', { method: 'POST', body: JSON.stringify(payload) }),
  addStoryMark: (payload: { soul_id?: string; mark_type: string; location: string; origin_event_id: string; acquired_at?: string; visibility?: string; status?: string }) => request<{ story_mark: StoryMark }>('/api/v1/visual/story-marks/add', { method: 'POST', body: JSON.stringify(payload) }),
  createPortraitSnapshot: (payload: { soul_id?: string; label: string; image_url?: string }) => request<{ portrait: PortraitVersion }>('/api/v1/visual/portraits/snapshot', { method: 'POST', body: JSON.stringify(payload) }),
  compileMemoryObject: (payload: { event_id: string; event_title: string; participants: ParticipantRef[]; location_environment: string; relics_involved?: string[]; emotional_tone: string; action_composition: string; lasting_consequence: string; privacy_consent_scope?: string }) => request<{ memory_object: MemoryObject }>('/api/v1/visual/memory-objects/compile', { method: 'POST', body: JSON.stringify(payload) }),
  listMemoryObjects: () => request<{ memory_objects: MemoryObject[] }>('/api/v1/visual/memory-objects'),

  // Phase 10: Portrait Generation & Continuity
  compilePortraitPrompt: (payload: { soul_id?: string; source_portrait_version_id?: string; generation_type?: GenerationType; emotional_state?: string; style_preset?: string }) => request<PromptCompilationResult>('/api/v1/visual-memory/portraits/compile', { method: 'POST', body: JSON.stringify(payload) }),
  createPortraitCandidate: (payload: { soul_id?: string; source_portrait_version_id?: string; generation_type?: GenerationType; emotional_state?: string; style_preset?: string }) => request<{ candidate: PortraitGenerationCandidate }>('/api/v1/visual-memory/portraits/candidates', { method: 'POST', body: JSON.stringify(payload) }),
  generateCandidate: (candidateId: string, payload?: { provider_type?: string; seed?: number }) => request<{ candidate: PortraitGenerationCandidate }>(`/api/v1/visual-memory/portraits/candidates/${encodeURIComponent(candidateId)}/generate`, { method: 'POST', body: JSON.stringify(payload || {}) }),
  approveCandidate: (candidateId: string, payload: { soul_id?: string; label?: string }) => request<{ portrait_version: PortraitVersion; candidate: PortraitGenerationCandidate; message: string }>(`/api/v1/visual-memory/portraits/candidates/${encodeURIComponent(candidateId)}/approve`, { method: 'POST', body: JSON.stringify(payload) }),
  rejectCandidate: (candidateId: string, payload: { soul_id?: string; reason?: string }) => request<{ candidate: PortraitGenerationCandidate; message: string }>(`/api/v1/visual-memory/portraits/candidates/${encodeURIComponent(candidateId)}/reject`, { method: 'POST', body: JSON.stringify(payload) }),
  listPortraitCandidates: (soulId = 'Kaelen the Star-Watcher') => request<{ candidates: PortraitGenerationCandidate[] }>(`/api/v1/visual-memory/portraits/candidates?soul_id=${encodeURIComponent(soulId)}`),
  getPortraitCandidate: (candidateId: string) => request<{ candidate: PortraitGenerationCandidate }>(`/api/v1/visual-memory/portraits/candidates/${encodeURIComponent(candidateId)}`),
  listPortraitVersions: (soulId = 'Kaelen the Star-Watcher') => request<{ portrait_versions: PortraitVersion[] }>(`/api/v1/visual-memory/portraits/versions?soul_id=${encodeURIComponent(soulId)}`),
  getPortraitVersion: (versionId: string) => request<{ portrait_version: PortraitVersion }>(`/api/v1/visual-memory/portraits/versions/${encodeURIComponent(versionId)}`),

  // Phase 4: Visual Worldsmith
  createWorldVisualCandidate: (payload: { entity_type: WorldEntityType; entity_id: string; name: string; canonical_state: Record<string, any>; generation_type?: string; source_visual_version_id?: string; style?: string }) => request<{ candidate: WorldVisualCandidate }>('/api/v1/visual-world/candidates', { method: 'POST', body: JSON.stringify(payload) }),
  generateWorldVisualCandidate: (candidateId: string, payload?: { provider_type?: string; seed?: number }) => request<{ candidate: WorldVisualCandidate }>(`/api/v1/visual-world/candidates/${encodeURIComponent(candidateId)}/generate`, { method: 'POST', body: JSON.stringify(payload || {}) }),
  approveWorldVisualCandidate: (candidateId: string) => request<{ visual_version: VisualEntityVersion; candidate: WorldVisualCandidate; message: string }>(`/api/v1/visual-world/candidates/${encodeURIComponent(candidateId)}/approve`, { method: 'POST', body: JSON.stringify({}) }),
  rejectWorldVisualCandidate: (candidateId: string) => request<{ candidate: WorldVisualCandidate; message: string }>(`/api/v1/visual-world/candidates/${encodeURIComponent(candidateId)}/reject`, { method: 'POST', body: JSON.stringify({}) }),
  listWorldVisualVersions: (entityType: WorldEntityType, entityId: string) => request<{ versions: VisualEntityVersion[] }>(`/api/v1/visual-world/${encodeURIComponent(entityType)}/${encodeURIComponent(entityId)}/versions`),
  listWorldVisualCandidates: (entityType: WorldEntityType, entityId: string) => request<{ candidates: WorldVisualCandidate[] }>(`/api/v1/visual-world/${encodeURIComponent(entityType)}/${encodeURIComponent(entityId)}/candidates`),

  // Phase 12: Chronicle Paintings + Visual Canon Guardian
  createChroniclePainting: (payload: { memory_object_id: string; generation_type?: ChroniclePainting['generation_type']; source_painting_id?: string; composition?: string; style?: string }) => request<{ painting: ChroniclePainting }>('/api/v1/chronicle-paintings', { method: 'POST', body: JSON.stringify(payload) }),
  generateChroniclePainting: (paintingId: string, payload?: { provider_type?: string; seed?: number }) => request<{ painting: ChroniclePainting }>(`/api/v1/chronicle-paintings/${encodeURIComponent(paintingId)}/generate`, { method: 'POST', body: JSON.stringify(payload || {}) }),
  approveChroniclePainting: (paintingId: string) => request<{ painting: ChroniclePainting; message: string }>(`/api/v1/chronicle-paintings/${encodeURIComponent(paintingId)}/approve`, { method: 'POST', body: JSON.stringify({}) }),
  rejectChroniclePainting: (paintingId: string) => request<{ painting: ChroniclePainting; message: string }>(`/api/v1/chronicle-paintings/${encodeURIComponent(paintingId)}/reject`, { method: 'POST', body: JSON.stringify({}) }),
  getChroniclePainting: (paintingId: string) => request<{ painting: ChroniclePainting }>(`/api/v1/chronicle-paintings/${encodeURIComponent(paintingId)}`),
  listChroniclePaintings: (memoryObjectId?: string) => request<{ paintings: ChroniclePainting[] }>(memoryObjectId ? `/api/v1/chronicle-paintings?memory_object_id=${encodeURIComponent(memoryObjectId)}` : '/api/v1/chronicle-paintings'),
  listApprovedChroniclePaintings: () => request<{ paintings: ChroniclePainting[] }>('/api/v1/chronicle-paintings/gallery'),
  getChroniclePaintingProviderCapabilities: () => request<{ capabilities: ProviderCapabilities }>('/api/v1/chronicle-paintings/providers/capabilities'),

  // Phase 13: Group Memories & Tags
  createGroupMemory: (payload: { event_id: string; visibility?: string; memory_object_ids?: string[] }) => request<{ group_memory: GroupMemory }>('/api/v1/group-memories', { method: 'POST', body: JSON.stringify(payload) }),
  autoGroupMemories: (eventId: string) => request<{ group_memory: GroupMemory; grouped: boolean; message: string }>(`/api/v1/group-memories/auto-group?event_id=${encodeURIComponent(eventId)}`, { method: 'POST' }),
  listGroupMemories: (viewerSoulId?: string) => request<{ group_memories: GroupMemory[] }>(`/api/v1/group-memories${viewerSoulId ? `?viewer_soul_id=${encodeURIComponent(viewerSoulId)}` : ''}`),
  getGroupMemory: (groupId: string, viewerSoulId?: string) => request<{ group_memory: GroupMemory }>(`/api/v1/group-memories/${encodeURIComponent(groupId)}${viewerSoulId ? `?viewer_soul_id=${encodeURIComponent(viewerSoulId)}` : ''}`),
  getGroupMemoryByEvent: (eventId: string, viewerSoulId?: string) => request<{ group_memory: GroupMemory }>(`/api/v1/group-memories/by-event/${encodeURIComponent(eventId)}${viewerSoulId ? `?viewer_soul_id=${encodeURIComponent(viewerSoulId)}` : ''}`),
  attachGroupMember: (groupId: string, payload: { memory_object_id: string; soul_id: string; role_in_event?: string; portrait_version_id?: string }) => request<{ group_memory: GroupMemory }>(`/api/v1/group-memories/${encodeURIComponent(groupId)}/members`, { method: 'POST', body: JSON.stringify(payload) }),
  detachGroupMember: (groupId: string, memoryObjectId: string) => request<{ group_memory: GroupMemory; memory_object_still_exists: boolean }>(`/api/v1/group-memories/${encodeURIComponent(groupId)}/members/${encodeURIComponent(memoryObjectId)}`, { method: 'DELETE' }),
  addGroupTag: (groupId: string, payload: { tag_type: GroupTagType; value: string; anchor_kind?: GroupAnchorType; anchor_id?: string; is_descriptor?: boolean }) => request<{ tag: GroupMemoryTag }>(`/api/v1/group-memories/${encodeURIComponent(groupId)}/tags`, { method: 'POST', body: JSON.stringify(payload) }),
  removeGroupTag: (groupId: string, tagId: string) => request<{ removed: boolean }>(`/api/v1/group-memories/${encodeURIComponent(groupId)}/tags/${encodeURIComponent(tagId)}`, { method: 'DELETE' }),
  addGroupAnchor: (groupId: string, payload: { anchor_type: GroupAnchorType; anchor_ref: string; label?: string }) => request<{ anchor: GroupMemoryAnchor }>(`/api/v1/group-memories/${encodeURIComponent(groupId)}/anchors`, { method: 'POST', body: JSON.stringify(payload) }),
  getGroupAnchors: (groupId: string) => request<{ anchors: GroupMemoryAnchor[] }>(`/api/v1/group-memories/${encodeURIComponent(groupId)}/anchors`),
  getGroupPerspectives: (groupId: string, viewerSoulId?: string) => request<PerspectiveComparison>(`/api/v1/group-memories/${encodeURIComponent(groupId)}/perspectives${viewerSoulId ? `?viewer_soul_id=${encodeURIComponent(viewerSoulId)}` : ''}`),
  findRelatedGroupMemories: (params: { anchor_type?: GroupAnchorType; anchor_ref?: string; tag_type?: GroupTagType; tag_value?: string; viewer_soul_id?: string }) => request<{ group_memories: GroupMemory[] }>(`/api/v1/group-memories/related?${new URLSearchParams(params as Record<string, string>).toString()}`),
  suggestRelatedMemories: (memoryObjectId: string) => request<{ suggestions: RelatedMemorySuggestion[] }>(`/api/v1/group-memories/suggestions/${encodeURIComponent(memoryObjectId)}`),

  // Phase 14: Living Biography
  compileBiography: (payload: { soul_id?: string; scope_type?: string; scope_ref?: string; visibility?: string; viewer_soul_id?: string }) => request<{ biography: Biography; guardian_report: BiographyGuardianReport }>('/api/v1/biographies/compile', { method: 'POST', body: JSON.stringify(payload) }),
  getCurrentBiography: (soulId = 'Kaelen the Star-Watcher', viewerSoulId?: string) => request<{ biography: Biography }>(`/api/v1/biographies/current?soul_id=${encodeURIComponent(soulId)}${viewerSoulId ? `&viewer_soul_id=${encodeURIComponent(viewerSoulId)}` : ''}`),
  listBiographyHistory: (soulId = 'Kaelen the Star-Watcher') => request<{ biographies: Biography[] }>(`/api/v1/biographies/history?soul_id=${encodeURIComponent(soulId)}`),
  getBiography: (biographyId: string, viewerSoulId?: string) => request<{ biography: Biography }>(`/api/v1/biographies/${encodeURIComponent(biographyId)}${viewerSoulId ? `?viewer_soul_id=${encodeURIComponent(viewerSoulId)}` : ''}`),
  approveBiography: (biographyId: string, soulId = 'Kaelen the Star-Watcher') => request<{ biography: Biography; message: string }>(`/api/v1/biographies/${encodeURIComponent(biographyId)}/approve?soul_id=${encodeURIComponent(soulId)}`, { method: 'POST' }),
  rejectBiography: (biographyId: string, soulId = 'Kaelen the Star-Watcher') => request<{ biography: Biography; message: string }>(`/api/v1/biographies/${encodeURIComponent(biographyId)}/reject?soul_id=${encodeURIComponent(soulId)}`, { method: 'POST' }),
  getBiographySectionProvenance: (biographyId: string, sectionId: string, viewerSoulId?: string) => request<{ provenance: BiographySourceRef[]; section: BiographySection }>(`/api/v1/biographies/${encodeURIComponent(biographyId)}/sections/${encodeURIComponent(sectionId)}/provenance${viewerSoulId ? `?viewer_soul_id=${encodeURIComponent(viewerSoulId)}` : ''}`),

  // Phase 15: Art Director & World Gallery
  createArtDirectionProfile: (payload: { name: string; description?: string; medium_style?: string; palette_guidance?: string; lighting_guidance?: string; atmosphere?: string; texture_material?: string; camera_framing?: string; composition_guidance?: string; portrait_treatment?: string; environment_treatment?: string; relic_treatment?: string; phenomenon_treatment?: string; chronicle_treatment?: string; negative_guidance?: string; provider_hints?: Record<string, any>; accessibility_notes?: string }) => request<{ profile: ArtDirectionProfile; version: ArtDirectionProfileVersion }>('/api/v1/art-direction/profiles', { method: 'POST', body: JSON.stringify(payload) }),
  listArtDirectionProfiles: () => request<{ profiles: ArtDirectionProfile[] }>('/api/v1/art-direction/profiles'),
  getArtDirectionProfile: (profileId: string) => request<{ profile: ArtDirectionProfile; versions: ArtDirectionProfileVersion[] }>(`/api/v1/art-direction/profiles/${encodeURIComponent(profileId)}`),
  createArtDirectionProfileVersion: (profileId: string, payload: { name?: string; description?: string; medium_style?: string; palette_guidance?: string; lighting_guidance?: string; atmosphere?: string; texture_material?: string; camera_framing?: string; composition_guidance?: string; portrait_treatment?: string; environment_treatment?: string; relic_treatment?: string; phenomenon_treatment?: string; chronicle_treatment?: string; negative_guidance?: string; provider_hints?: Record<string, any>; accessibility_notes?: string }) => request<{ version: ArtDirectionProfileVersion }>(`/api/v1/art-direction/profiles/${encodeURIComponent(profileId)}/versions`, { method: 'POST', body: JSON.stringify(payload) }),
  setArtDirectionProfileStatus: (profileId: string, status: string) => request<{ profile: ArtDirectionProfile }>(`/api/v1/art-direction/profiles/${encodeURIComponent(profileId)}/status?status_value=${encodeURIComponent(status)}`, { method: 'POST' }),
  getCurrentArtDirection: () => request<{ profile: ArtDirectionProfile; version: ArtDirectionProfileVersion | null }>('/api/v1/art-direction/current'),
  resolveArtDirection: (payload: { profile_version_id: string; artifact_type: ArtifactType; override?: Record<string, string> }) => request<{ resolved: ResolvedArtDirection }>('/api/v1/art-direction/resolve', { method: 'POST', body: JSON.stringify(payload) }),
  compileArtDirectionSpec: (payload: { profile_version_id: string; artifact_type: ArtifactType; canonical?: Record<string, any>; historical_references?: Record<string, any>[]; composition_intent?: string; accessibility?: string[]; override?: Record<string, string> }) => request<{ spec: ArtDirectionSpec }>('/api/v1/art-direction/preview', { method: 'POST', body: JSON.stringify(payload) }),
  reviewStyle: (payload: { profile_version_id: string; artifact_type: ArtifactType; override?: Record<string, string> }) => request<{ style_review: StyleReviewResult }>('/api/v1/art-direction/review', { method: 'POST', body: JSON.stringify(payload) }),

  listGalleryArtifacts: (params?: { viewer_soul_id?: string; mode?: string; entity_type?: string; entity_id?: string }) => request<{ artifacts: GalleryArtifact[] }>(`/api/v1/gallery?${new URLSearchParams((params ?? {}) as Record<string, string>).toString()}`),
  getGalleryTimeline: (entityType: string, entityId: string, viewerSoulId?: string) => request<{ artifacts: GalleryArtifact[] }>(`/api/v1/gallery/timeline?entity_type=${encodeURIComponent(entityType)}&entity_id=${encodeURIComponent(entityId)}${viewerSoulId ? `&viewer_soul_id=${encodeURIComponent(viewerSoulId)}` : ''}`),
  createGalleryCollection: (payload: { title: string; description?: string; visibility?: 'public_canon' | 'private'; curator_soul_id?: string }) => request<{ collection: GalleryCollection }>('/api/v1/gallery/collections', { method: 'POST', body: JSON.stringify(payload) }),
  listGalleryCollections: () => request<{ collections: GalleryCollection[] }>('/api/v1/gallery/collections'),
  getGalleryCollection: (collectionId: string) => request<{ collection: GalleryCollection }>(`/api/v1/gallery/collections/${encodeURIComponent(collectionId)}`),
  addGalleryCollectionItem: (collectionId: string, payload: { artifact_type: GalleryArtifact['artifact_type']; artifact_ref: string; caption?: string; position?: number }) => request<{ item: GalleryCollectionItem }>(`/api/v1/gallery/collections/${encodeURIComponent(collectionId)}/items`, { method: 'POST', body: JSON.stringify(payload) }),
  removeGalleryCollectionItem: (collectionId: string, itemId: string) => request<{ removed: boolean }>(`/api/v1/gallery/collections/${encodeURIComponent(collectionId)}/items/${encodeURIComponent(itemId)}`, { method: 'DELETE' }),
  reorderGalleryCollection: (collectionId: string, orderedItemIds: string[]) => request<{ collection: GalleryCollection }>(`/api/v1/gallery/collections/${encodeURIComponent(collectionId)}/reorder`, { method: 'POST', body: JSON.stringify({ ordered_item_ids: orderedItemIds }) }),

  // Phase 16: Legendary Figures & World Memory
  compileWorldMemory: (payload: { subject_entity_type: string; subject_entity_id: string; culture?: string; era_context?: string; memory_form?: string; interpretation_type?: string; remembrance_scale?: string; visibility?: string; perspective?: string; viewer_soul_id?: string }) => request<{ memory: WorldMemory; guardian_report: Record<string, any> }>('/api/v1/world-memory/compile', { method: 'POST', body: JSON.stringify(payload) }),
  listWorldMemories: (params?: { viewer_soul_id?: string; subject_entity_type?: string; subject_entity_id?: string; culture?: string; era_context?: string; memory_form?: string; memory_state?: string }) => request<{ memories: WorldMemory[] }>(`/api/v1/world-memory?${new URLSearchParams((params ?? {}) as Record<string, string>).toString()}`),
  getWorldMemory: (memoryId: string, viewerSoulId?: string) => request<{ memory: WorldMemory }>(`/api/v1/world-memory/${encodeURIComponent(memoryId)}${viewerSoulId ? `?viewer_soul_id=${encodeURIComponent(viewerSoulId)}` : ''}`),
  queryWorldMemories: (subjectEntityType: string, subjectEntityId: string, culture?: string, eraContext?: string) => request<{ memories: WorldMemory[] }>(`/api/v1/world-memory/query?subject_entity_type=${encodeURIComponent(subjectEntityType)}&subject_entity_id=${encodeURIComponent(subjectEntityId)}${culture ? `&culture=${encodeURIComponent(culture)}` : ''}${eraContext ? `&era_context=${encodeURIComponent(eraContext)}` : ''}`),
  approveWorldMemory: (memoryId: string) => request<{ memory: WorldMemory; message: string }>(`/api/v1/world-memory/${encodeURIComponent(memoryId)}/approve`, { method: 'POST' }),
  rejectWorldMemory: (memoryId: string) => request<{ memory: WorldMemory; message: string }>(`/api/v1/world-memory/${encodeURIComponent(memoryId)}/reject`, { method: 'POST' }),
  markWorldMemoryState: (memoryId: string, newState: string, reason = '') => request<{ memory: WorldMemory; message: string }>(`/api/v1/world-memory/${encodeURIComponent(memoryId)}/mark-state`, { method: 'POST', body: JSON.stringify({ new_state: newState, reason }) }),
  placeWorldMemory: (memoryId: string, payload: { placement_type: string; placement_ref: string; visibility?: string }) => request<{ placement: WorldMemoryPlacement }>(`/api/v1/world-memory/${encodeURIComponent(memoryId)}/placements`, { method: 'POST', body: JSON.stringify(payload) }),
  projectNPCKnowledge: (payload: { subject_entity_type: string; subject_entity_id: string; culture?: string; location?: string; era_context?: string; social_role?: string; access_to_archives?: boolean; education_level?: string; local_tradition?: boolean; direct_relationship?: boolean; secrecy_aware?: boolean }) => request<{ knowledge: NPCKnowledgeProjection }>('/api/v1/world-memory/npc-knowledge', { method: 'POST', body: JSON.stringify(payload) }),
  promoteLegendaryFigure: (payload: { subject_entity_type: string; subject_entity_id: string; subject_soul_id?: string; figure_title: string; later_cultural_titles?: string[]; remembrance_scale?: string; memory_state?: string }) => request<{ figure: LegendaryFigure }>('/api/v1/legendary-figures/promote', { method: 'POST', body: JSON.stringify(payload) }),
  listLegendaryFigures: () => request<{ figures: LegendaryFigure[] }>('/api/v1/legendary-figures'),
  getLegendaryFigure: (figureId: string) => request<{ figure: LegendaryFigure }>(`/api/v1/legendary-figures/${encodeURIComponent(figureId)}`),

  // Phase 17: Campaign Orchestrator
  startCampaignSession: (payload: { soul_id?: string; campaign_id?: string }) => request<{ session: CampaignSession; resumed: boolean }>('/api/v1/campaign/session', { method: 'POST', body: JSON.stringify(payload) }),
  getCampaignSession: (sessionId: string) => request<{ session: CampaignSession; opportunities: CampaignOpportunity[]; transitions: CampaignTransition[] }>(`/api/v1/campaign/session/${encodeURIComponent(sessionId)}`),
  evaluateCampaignOpportunities: (sessionId: string, includeEncounter = true) => request<{ session_id: string; silence: boolean; opportunities: CampaignOpportunity[] }>('/api/v1/campaign/opportunities/evaluate', { method: 'POST', body: JSON.stringify({ session_id: sessionId, include_encounter: includeEncounter }) }),
  resolveCampaignOpportunity: (opportunityId: string, payload: { decision?: string; recognition?: RecognitionDecision; player_intent?: string; note?: string }) => request<{ transition: CampaignTransition; opportunity: CampaignOpportunity; idempotent: boolean }>(`/api/v1/campaign/opportunities/${encodeURIComponent(opportunityId)}/resolve`, { method: 'POST', body: JSON.stringify(payload) }),
  commitCampaignEvent: (sessionId: string, eventId: string) => request<{ transition: CampaignTransition; opportunities: CampaignOpportunity[]; idempotent: boolean }>('/api/v1/campaign/commit', { method: 'POST', body: JSON.stringify({ session_id: sessionId, event_id: eventId }) }),
  getCampaignTransitionProvenance: (transitionId: string) => request<{ transition_id: string; transition_type: string; canonical_event_id?: string; systems_invoked: string[]; outcomes: Array<Record<string, any>>; provenance: Array<Record<string, any>>; canonical_change: boolean; provider_failure?: string }>(`/api/v1/campaign/transitions/${encodeURIComponent(transitionId)}/provenance`),
  getCampaignPendingReviews: (sessionId: string) => request<{ pending_reviews: CampaignOpportunity[] }>(`/api/v1/campaign/session/${encodeURIComponent(sessionId)}/reviews`),
  getCampaignAftermath: (sessionId: string) => request<Record<string, any>>(`/api/v1/campaign/session/${encodeURIComponent(sessionId)}/aftermath`),
  inspectCampaignOpportunity: (opportunityId: string) => request<Record<string, any>>(`/api/v1/campaign/opportunities/${encodeURIComponent(opportunityId)}/inspect`),

  // Phase 18: Soulkeeper Narrative Engine
  getCampaignNarrativeStatus: () => request<Record<string, any>>('/api/v1/campaign/narrative/status'),
  selectCampaignNarrativeProvider: (provider: string) => request<{ requested: string; effective: string; model: string; narration_source: string }>('/api/v1/campaign/narrative/select', { method: 'POST', body: JSON.stringify({ provider }) }),
  previewCampaignNarrativeContext: (opportunityId: string) => request<Record<string, any>>('/api/v1/campaign/narrative/preview-context', { method: 'POST', body: JSON.stringify({ opportunity_id: opportunityId }) }),
  getCampaignOpportunityNarrative: (opportunityId: string) => request<{ opportunity_id: string; narration?: string; narration_source: string; generations: NarrativeGeneration[] }>(`/api/v1/campaign/opportunities/${encodeURIComponent(opportunityId)}/narrative`),
  regenerateCampaignOpportunityNarrative: (opportunityId: string) => request<{ opportunity_id: string; narration: Record<string, any> | null; failure: string | null; canonical_state: string }>(`/api/v1/campaign/opportunities/${encodeURIComponent(opportunityId)}/regenerate`, { method: 'POST' }),
};
