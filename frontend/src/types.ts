// frontend/src/types.ts
export interface NumericDiceRoll {
  d20: number;
  d12: number;
  d10: number;
  percentile: number;
  d8: number;
  d6: number;
  d4: number;
  grammar_version: string;
}

export interface DiceInterpretation {
  spark: string;
  domain: string;
  pressure: string;
  aim: string;
  approach: string;
  verdict: string;
  thread: string;
}

/** @deprecated Use DiceInterpretation for symbols and CanonicalDiceRead for canonical records. */
export type DiceRollRead = DiceInterpretation;

export interface CanonicalDiceRead {
  raw: Omit<NumericDiceRoll, 'grammar_version'>;
  grammar_version: string;
  interpretation: DiceInterpretation;
  grammar_sentence: string;
}


export interface EncounterFrame {
  title: string;
  phenomenon_type: string;
  visible_situation: string;
  hidden_need: string;
  stakes: string;
  pressure_clock: number;
  questions: string[];
  suggested_actions: string[];
}

export interface SoulResources { resonance: number; strain: number; thread_count: number; }
export interface Relic { id: string; name: string; stage: 'Dormant' | 'Remembered' | 'Awakened' | 'Overdrawn' | 'Fractured' | 'Transfigured'; effect: string; overdraw_consequence: string; }
export interface SoulSheet { name: string; calling: string; origin: string; desire: string; fear: string; wound: string; resources: SoulResources; relics: Relic[]; bonds: string[]; scars: string[]; }
export interface CanonGuardianAudit { passed: boolean; gate_name: string; details: string; }
export interface SoulkeeperNarration { title: string; prose: string; tone: string; scene_beats: string[]; canon_writeback: string[]; guardian_audit: CanonGuardianAudit[]; }
export interface ResolveOutcome { outcome_class: 'ascendancy' | 'marked_success' | 'revelatory_failure' | 'collapse'; outcome_title: string; rules_summary: string; resonance_delta: number; strain_delta: number; thread_delta: number; new_resources: SoulResources; fracture_triggered: boolean; canon_facts: string[]; }
export interface ResolvedScene { outcome: ResolveOutcome; narration: SoulkeeperNarration; event_id: string; timestamp?: string; dice_read?: CanonicalDiceRead; }
export interface Seed { id: string; world_id: string; soul_id?: string; symbol: string; thread_type: string; stage: 'planted' | 'echoed' | 'recognized' | 'integrated' | 'retired'; echo_count: number; narrative_context: string; created_at?: string; updated_at?: string; }
export interface OpenQuestion { id: string; seed_id?: string; question_text: string; stakes?: string; status: 'open' | 'investigated' | 'resolved' | 'reinterpreted'; evidence_event_ids: string[]; created_at?: string; }
export interface LocalThread { id: string; soul_id: string; name: string; thread_type: string; status: 'active' | 'pattern_recognized' | 'integrated' | 'dormant'; evidence_count: number; evidence_summary: string; created_at?: string; }
export interface IntegrationEvent { id: string; soul_id: string; thread_id: string; choice_made: string; relic_awakened_id?: string; transformation_summary: string; created_at?: string; }

export type AwakeningStage = 'veiled' | 'echoing' | 'recognizing' | 'resonant' | 'woven' | 'lucid';

export interface Aspect {
  id: string;
  constellation_id: string;
  aspect_name: string;
  calling: string;
  origin: string;
  era_or_world: string;
  sheet?: Record<string, unknown>;
  created_at?: string;
}

export interface Anchor {
  id: string;
  constellation_id: string;
  anchor_name: string;
  relic_id?: string;
  connected_aspect_ids: string[];
  relic_form: string;
  status: string;
  created_at?: string;
}

export interface CrossAspectBond {
  id: string;
  constellation_id: string;
  source_aspect_id: string;
  target_aspect_id: string;
  bond_type: string;
  description: string;
  created_at?: string;
}

export interface Constellation {
  id: string;
  name: string;
  unresolved_pattern: string;
  awakening_stage: AwakeningStage;
  deep_threads: string[];
  aspects: Aspect[];
  anchors: Anchor[];
  bonds: CrossAspectBond[];
  created_at?: string;
  updated_at?: string;
}

export interface ConstellationStageInfo {
  title: string;
  description: string;
}

export type ManifestationType = 'dream' | 'rumor' | 'alternate_scene' | 'echo_aspect';
export type ProbablePathStatus = 'dormant' | 'echoing' | 'manifested' | 'reconciled';

export interface ProbablePath {
  id: string;
  event_id?: string;
  soul_id: string;
  path_title: string;
  chosen_path: string;
  unchosen_approach: string;
  potential_outcome_class: string;
  manifestation_type: ManifestationType;
  status: ProbablePathStatus;
  provenance_summary: string;
  created_at?: string;
}

export interface User {
  id: string;
  email: string;
  username: string;
  display_name: string;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export type RelicStage = 'Dormant' | 'Remembered' | 'Awakened' | 'Overdrawn' | 'Fractured' | 'Transfigured';

export interface Relic {
  id: string;
  soul_id: string;
  constellation_id?: string;
  name: string;
  stage: RelicStage;
  effect: string;
  overdraw_consequence: string;
  evocative_question: string;
  required_thread_type?: string;
  cross_aspect_forms: Record<string, string>;
  is_anchor: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface RelicEvent {
  id: string;
  relic_id: string;
  soul_id: string;
  action: string;
  previous_stage: RelicStage;
  new_stage: RelicStage;
  narrative_condition_met: string;
  chronicle_evidence_summary: string;
  created_at?: string;
}

export interface AlternateSceneResult {
  path_id: string;
  path_title: string;
  unchosen_approach: string;
  alternate_prose: string;
  divergence_notes: string;
  canonical_integrity_preserved: boolean;
  suggested_insights: string[];
}

export type CanonStatus = 'private' | 'opt_in_shared' | 'public_canon';

export interface CommunitySymbol {
  id: string;
  symbol_name: string;
  world_id: string;
  description: string;
  significance_score: number;
  contributing_souls: string[];
  canon_status: CanonStatus;
  created_at?: string;
}

export interface GatheringContribution {
  id: string;
  contributor_soul: string;
  role: 'Focus' | 'Anchor' | 'Witness' | 'Tempest';
  resonance_amount: number;
  notes: string;
  timestamp?: string;
}

export interface GatheringSession {
  id: string;
  room_id: string;
  phenomenon_name: string;
  target_resonance: number;
  current_resonance: number;
  roles: Record<string, string>;
  contributions: GatheringContribution[];
  status: 'active' | 'reconciled' | 'diverged';
  outcome_summary?: string;
}

export type NarrativeIntensity = 'gentle' | 'balanced' | 'deep_mythic' | 'unfiltered';
export type SpiritualFraming = 'secular_mythology' | 'opt_in_spiritual';

export interface PlayerPreferences {
  soul_id: string;
  narrative_intensity: NarrativeIntensity;
  spiritual_framing: SpiritualFraming;
  reduced_motion: boolean;
  high_contrast: boolean;
  allow_ai_indexing_default: boolean;
  updated_at?: string;
}

export interface ReflectionSession {
  id: string;
  soul_id: string;
  prompt_question: string;
  player_reflection: string;
  share_with_ai: boolean;
  created_at?: string;
}

export interface PrivateNote {
  id: string;
  soul_id: string;
  title: string;
  content: string;
  allow_ai_indexing: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface AvatarIdentity {
  soul_id: string;
  face: string;
  hair: string;
  body: string;
  species: string;
  eyes: string;
}

export interface StoryMark {
  id: string;
  soul_id: string;
  mark_type: string;
  location: string;
  origin_event_id: string;
  acquired_at: string;
  visibility: 'prominent' | 'subtle' | 'hidden_under_armor';
  status: 'permanent' | 'fading' | 'magically_sealed';
}

export interface EquipmentAppearance {
  soul_id: string;
  armor: string;
  clothing: string;
  weapons: string[];
  relics: string[];
  backpacks_cloaks: string;
}

export interface PortraitVersion {
  version_id: string;
  soul_id: string;
  version_number: number;
  label: string;
  image_url: string;
  story_marks_snapshot: StoryMark[];
  equipment_snapshot?: EquipmentAppearance;
  created_at?: string;
}

export interface ConsentSettings {
  soul_id: string;
  allow_shared_gallery: boolean;
  allow_character_tagging: boolean;
  allow_real_person_tagging: boolean;
  real_person_photo_url?: string;
  real_person_display_name?: string;
}

export interface ParticipantRef {
  soul_id: string;
  character_name: string;
  portrait_version_id: string;
  role_in_event: string;
  real_person_tag_opt_in?: boolean;
}

export interface MemoryObject {
  id: string;
  event_id: string;
  event_title: string;
  participants: ParticipantRef[];
  location_environment: string;
  relics_involved: string[];
  emotional_tone: string;
  action_composition: string;
  lasting_consequence: string;
  privacy_consent_scope: string;
  visual_generation_status: 'pending' | 'compiled' | 'painting_approved' | 'rejected';
  painting_image_url?: string;
  created_at?: string;
}

export interface VisualAvatarProfile {
  identity: AvatarIdentity;
  story_marks: StoryMark[];
  equipment: EquipmentAppearance;
  portraits: PortraitVersion[];
  consent: ConsentSettings;
}

export type CandidateStatus = 'pending' | 'generated' | 'approved' | 'rejected' | 'failed';
export type GenerationType = 'initial' | 'story_mark_update' | 'equipment_update' | 'age_update' | 'manual_regeneration';

export interface PortraitGenerationCandidate {
  candidate_id: string;
  soul_id: string;
  source_portrait_version_id?: string;
  generation_type: GenerationType;
  compiled_prompt: string;
  negative_prompt?: string;
  provider: string;
  provider_model: string;
  provider_request_id?: string;
  generation_seed?: number;
  reference_image_url?: string;
  generated_image_url?: string;
  canonical_identity_snapshot: AvatarIdentity;
  story_marks_snapshot: StoryMark[];
  equipment_snapshot?: EquipmentAppearance;
  status: CandidateStatus;
  failure_reason?: string;
  resulting_portrait_version_id?: string;
  art_direction_profile_id?: string;
  art_direction_profile_version_id?: string;
  created_at?: string;
  reviewed_at?: string;
}

export interface PromptCompilationResult {
  subject_identity: string;
  continuity_requirements: string[];
  story_marks: string[];
  equipment: Record<string, any>;
  expression: string;
  composition: string;
  lighting: string;
  style: string;
  negative_constraints: string[];
  compiled_prompt: string;
}

// Phase 4: Visual Worldsmith
export type WorldEntityType = 'location' | 'relic' | 'phenomenon';
export type WorldCandidateStatus = 'pending' | 'generated' | 'approved' | 'rejected' | 'failed';

export interface VisualEntityVersion {
  version_id: string;
  entity_id: string;
  entity_type: WorldEntityType;
  version_number: number;
  label: string;
  canonical_snapshot: Record<string, any>;
  image_url: string;
  source_version_id?: string;
  provider: string;
  provider_model?: string;
  created_at?: string;
}

export interface WorldVisualCandidate {
  candidate_id: string;
  entity_id: string;
  entity_type: WorldEntityType;
  source_visual_version_id?: string;
  generation_type: string;
  canonical_snapshot: Record<string, any>;
  canonical_delta: Record<string, string[]>;
  compiled_prompt: string;
  negative_prompt?: string;
  reference_image_url?: string;
  workflow_role?: string;
  provider: string;
  provider_model?: string;
  provider_request_id?: string;
  generation_seed?: number;
  generated_image_url?: string;
  status: WorldCandidateStatus;
  failure_reason?: string;
  resulting_visual_version_id?: string;
  art_direction_profile_id?: string;
  art_direction_profile_version_id?: string;
  created_at?: string;
  reviewed_at?: string;
}

// Phase 12: Chronicle Paintings + Visual Canon Guardian
export type PaintingStatus = 'candidate' | 'approved' | 'rejected' | 'superseded' | 'failed';
export type GuardianStatus = 'pending' | 'generating' | 'reviewing' | 'passed' | 'retry' | 'blocked' | 'failed';
export type PaintingGenerationType = 'initial' | 'retry' | 'composition_change' | 'style_change' | 'reference_upgrade' | 'manual_regeneration';
export type GuardianVerdict = 'pass' | 'retry' | 'block';
export type ViolationSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface GuardianViolation {
  type: string;
  severity: ViolationSeverity;
  description: string;
  canonical_expected: string;
  observed: string;
}

export interface GuardianReport {
  status: GuardianVerdict;
  confidence: number;
  violations: GuardianViolation[];
  correction_instructions: string[];
}

export interface ProviderCapabilities {
  provider: string;
  text_to_image: boolean;
  single_reference: boolean;
  multiple_references: boolean;
  identity_conditioning: boolean;
  regional_conditioning: boolean;
  deterministic_seed: boolean;
  aspect_ratio_control: boolean;
}

export interface ParticipantAppearance {
  soul_id: string;
  character_name: string;
  role_in_event: string;
  portrait_version_id?: string;
  identity_strategy: string;
  portrait_image_url?: string;
  story_marks: StoryMark[];
  equipment?: EquipmentAppearance;
}

export interface ChroniclePainting {
  painting_id: string;
  memory_object_id: string;
  source_painting_id?: string;
  generation_type: PaintingGenerationType;
  status: PaintingStatus;
  guardian_status: GuardianStatus;
  compiler_version: string;
  scene_spec: Record<string, any>;
  composition: string;
  historical_participant_refs: Record<string, any>[];
  compiled_prompt: string;
  negative_prompt?: string;
  provider: string;
  provider_model?: string;
  provider_request_id?: string;
  generation_seed?: number;
  quarantined_image_url?: string;
  image_url?: string;
  guardian_report?: GuardianReport;
  failure_reason?: string;
  retry_count: number;
  art_direction_profile_id?: string;
  art_direction_profile_version_id?: string;
  created_at?: string;
  reviewed_at?: string;
  approved_at?: string;
  memory_event_id?: string;
  memory_event_title?: string;
}

// Phase 13: Group Memories & Tags
export type GroupTagType = 'person' | 'location' | 'relic' | 'phenomenon' | 'faction' | 'relationship' | 'emotional_theme' | 'event_type' | 'recurring_motif' | 'consequence' | 'thread';
export type GroupAnchorType = 'portrait' | 'location' | 'relic' | 'phenomenon' | 'chronicle_painting';
export type GroupSignificanceTier = 'personal' | 'relationship' | 'community' | 'world' | 'legendary';

export interface GroupMemoryMember {
  memory_object_id: string;
  soul_id: string;
  role_in_event?: string;
  portrait_version_id?: string;
}

export interface GroupMemoryTag {
  tag_id: string;
  tag_type: GroupTagType;
  value: string;
  anchor_kind?: GroupAnchorType;
  anchor_id?: string;
  is_descriptor: boolean;
}

export interface GroupMemoryAnchor {
  anchor_type: GroupAnchorType;
  anchor_ref: string;
  entity_id?: string;
  entity_type?: string;
  label: string;
}

export interface GroupMemory {
  group_id: string;
  event_id: string;
  title: string;
  summary: string;
  visibility: string;
  group_significance: GroupSignificanceTier;
  group_significance_score: number;
  group_significance_rationale?: string;
  members: GroupMemoryMember[];
  tags: GroupMemoryTag[];
  anchors: GroupMemoryAnchor[];
  created_at?: string;
  updated_at?: string;
}

export interface ParticipantPerspective {
  soul_id: string;
  character_name: string;
  role_in_event?: string;
  memory_object_id: string;
  event_title: string;
  location_environment: string;
  emotional_tone?: string;
  action_composition?: string;
  lasting_consequence?: string;
  is_self: boolean;
  is_public: boolean;
}

export interface PerspectiveComparison {
  group_id: string;
  event_id: string;
  perspectives: ParticipantPerspective[];
  shared_facts: string[];
  disagreements: Record<string, any>[];
}

export interface RelatedMemorySuggestion {
  memory_object_id: string;
  event_id: string;
  reason: string;
  canonical: boolean;
}

// Phase 14: Living Biography
export type BiographyStatus = 'draft' | 'current' | 'superseded' | 'rejected' | 'failed';
export type BiographyGuardianStatus = 'pending' | 'passed' | 'failed';
export type BiographyClaimKind = 'canonical_fact' | 'participant_perspective' | 'shared_perspective' | 'inferred_theme' | 'narrative_connective' | 'unresolved';
export type BiographySectionType = 'origins' | 'formative_moments' | 'bonds' | 'discoveries' | 'trials' | 'relics' | 'story_marks' | 'places' | 'phenomena' | 'shared_memories' | 'consequences' | 'unresolved_threads' | 'current_chapter';
export type BiographySourceType = 'memory_object' | 'group_memory' | 'portrait_version' | 'visual_entity_version' | 'chronicle_painting' | 'story_mark' | 'relic' | 'probable_path';

export interface BiographySourceRef {
  source_type: BiographySourceType;
  source_id: string;
  claim_kind: BiographyClaimKind;
  note?: string;
}

export interface BiographySection {
  section_id: string;
  biography_id: string;
  section_type: BiographySectionType;
  position: number;
  title: string;
  narrative: string;
  claim_kind: BiographyClaimKind;
  perspective_of?: string;
  visual_reference?: string;
  provenance: BiographySourceRef[];
  created_at?: string;
}

export interface BiographyGuardianReport {
  status: 'pass' | 'fail';
  confidence: number;
  violations: Array<{ type: string; severity: string; description: string; canonical_expected: string; observed: string }>;
  correction_instructions: string[];
}

export interface Biography {
  biography_id: string;
  soul_id: string;
  version_number: number;
  status: BiographyStatus;
  title: string;
  current_chapter?: string;
  scope_type: string;
  scope_ref?: string;
  visibility: string;
  source_snapshot: Record<string, any>;
  provider: string;
  provider_model?: string;
  compiler_version: string;
  guardian_status: BiographyGuardianStatus;
  guardian_report?: BiographyGuardianReport;
  sections: BiographySection[];
  created_at?: string;
  updated_at?: string;
}

// Phase 15: Art Director & World Gallery
export type ArtDirectionProfileStatus = 'draft' | 'current' | 'superseded' | 'archived';
export type ArtifactType = 'portrait' | 'location' | 'relic' | 'phenomenon' | 'chronicle_painting';

export interface ArtDirectionProfile {
  profile_id: string;
  name: string;
  description: string;
  status: ArtDirectionProfileStatus;
  current_version_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ArtDirectionProfileVersion {
  version_id: string;
  profile_id: string;
  version_number: number;
  medium_style: string;
  palette_guidance: string;
  lighting_guidance: string;
  atmosphere: string;
  texture_material: string;
  camera_framing: string;
  composition_guidance: string;
  portrait_treatment: string;
  environment_treatment: string;
  relic_treatment: string;
  phenomenon_treatment: string;
  chronicle_treatment: string;
  negative_guidance: string;
  provider_hints: Record<string, any>;
  accessibility_notes: string;
  created_at?: string;
}

export interface ResolvedArtDirection {
  profile_id: string;
  version_id: string;
  artifact_type: ArtifactType;
  medium_style: string;
  palette_guidance: string;
  lighting_guidance: string;
  atmosphere: string;
  texture_material: string;
  camera_framing: string;
  composition_guidance: string;
  treatment: string;
  negative_guidance: string;
  provider_hints: Record<string, any>;
  accessibility_notes: string;
  override_applied: Record<string, string>;
}

export interface ArtDirectionSpec {
  artifact_type: string;
  profile_id: string;
  profile_version_id: string;
  canonical: Record<string, any>;
  historical_references: Record<string, any>[];
  style: ResolvedArtDirection;
  provider_capabilities: Record<string, any>;
  composition_intent: string;
  accessibility: string[];
  limitations: string[];
  provider_prompt: string;
}

export interface StyleReviewResult {
  status: 'pass' | 'retry';
  style_confidence: number;
  style_deviations: string[];
  correction_instructions: string[];
}

export type GalleryArtifactType = 'portrait' | 'visual_entity' | 'chronicle_painting' | 'biography_illustration';

export interface GalleryProvenance {
  source_type: string;
  source_id: string;
  label: string;
}

export interface GalleryArtifact {
  artifact_id: string;
  artifact_type: GalleryArtifactType;
  image_url: string;
  title: string;
  caption: string;
  alt_text: string;
  provenance: GalleryProvenance[];
  art_direction?: { profile_id?: string; profile_version_id?: string };
  guardian_status?: string;
  chronology_label?: string;
  entity_id?: string;
  entity_type?: string;
  created_at?: string;
}

export interface GalleryCollectionItem {
  item_id: string;
  collection_id: string;
  artifact_type: GalleryArtifactType;
  artifact_ref: string;
  position: number;
  caption: string;
  created_at?: string;
}

export interface GalleryCollection {
  collection_id: string;
  title: string;
  description: string;
  visibility: 'public_canon' | 'private';
  curator_soul_id?: string;
  items: GalleryCollectionItem[];
  created_at?: string;
  updated_at?: string;
}

export interface SoulprintProfile { sun_sign: string; moon_sign: string; ascendant_sign: string; elemental_balance: Record<string, number>; motifs: Array<{ tag: string; weight: number; description: string }>; favored_domains: string[]; favored_threads: string[]; narrative_hooks: string[]; privacy_notice: string; }

export const DIE_LIMITS = { d20: 20, d12: 12, d10: 10, percentile: 100, d8: 8, d6: 6, d4: 4 } as const;

export const isNumericDiceRoll = (value: unknown): value is NumericDiceRoll => {
  if (!value || typeof value !== 'object') return false;
  const candidate = value as Record<string, unknown>;
  return Object.entries(DIE_LIMITS).every(([die, limit]) => Number.isInteger(candidate[die]) && (candidate[die] as number) >= 1 && (candidate[die] as number) <= limit) && typeof candidate.grammar_version === 'string';
};

export const isCanonicalDiceRead = (value: unknown): value is CanonicalDiceRead => {
  if (!value || typeof value !== 'object') return false;
  const candidate = value as CanonicalDiceRead;
  return Boolean(candidate.raw && candidate.interpretation && candidate.grammar_version && candidate.grammar_sentence);
};

export const toNumericDiceRoll = (raw: CanonicalDiceRead['raw'], grammarVersion: string): NumericDiceRoll => ({ ...raw, grammar_version: grammarVersion });
// Phase 16: Legendary Figures & World Memory
export type WorldMemoryForm =
  | 'legend'
  | 'historical_account'
  | 'folk_tale'
  | 'rumor'
  | 'oral_tradition'
  | 'song_ballad'
  | 'inscription'
  | 'memorial'
  | 'monument_statue'
  | 'displayed_artwork'
  | 'archival_document'
  | 'festival_tradition'
  | 'place_name_inheritance'
  | 'relic_legend'
  | 'lineage_tradition'
  | 'religious_mythic_interpretation'
  | 'forgotten_fragment';

export type InterpretationType =
  | 'faithful'
  | 'simplified'
  | 'selective'
  | 'symbolic'
  | 'exaggerated'
  | 'contradictory'
  | 'corrupted'
  | 'fragmented'
  | 'mythologized'
  | 'disputed'
  | 'unknown';

export type MemoryState =
  | 'widely_remembered'
  | 'locally_remembered'
  | 'archived_obscure'
  | 'fragmented'
  | 'misattributed'
  | 'suppressed'
  | 'forgotten'
  | 'rediscovered';

export type RemembranceScale = 'personal' | 'local' | 'regional' | 'world_famous' | 'forgotten';

export interface WorldMemorySourceRef {
  source_type: string;
  source_id: string;
  claim_kind: string;
  note?: string;
}

export interface WorldMemoryDeviation {
  deviation_id: string;
  memory_id: string;
  deviation_kind: string;
  canon_supports: string;
  legend_claims: string;
  entry_note: string;
  created_at?: string;
}

export interface WorldMemoryGuardianReport {
  status: string;
  confidence: number;
  violations: Array<Record<string, any>>;
  diagnostics: string[];
  correction_instructions: string[];
}

export interface WorldMemory {
  memory_id: string;
  subject_entity_type: string;
  subject_entity_id: string;
  culture: string;
  era_context: string;
  memory_form: WorldMemoryForm;
  interpretation_type: InterpretationType;
  title: string;
  narrative: string;
  memory_state: MemoryState;
  remembrance_scale: RemembranceScale;
  visibility: string;
  perspective: string;
  status: string;
  guardian_status: string;
  guardian_report?: WorldMemoryGuardianReport;
  version_number: number;
  compiler_version: string;
  provider: string;
  provider_model?: string;
  significance_rationale: string;
  source_refs: WorldMemorySourceRef[];
  deviations: WorldMemoryDeviation[];
  created_at?: string;
  updated_at?: string;
}

export interface LegendaryFigureLink {
  link_id: string;
  figure_id: string;
  link_type: string;
  link_ref: string;
  link_label: string;
  is_canonical: boolean;
  created_at?: string;
}

export interface LegendaryFigure {
  figure_id: string;
  subject_soul_id?: string;
  subject_entity_type: string;
  subject_entity_id: string;
  figure_title: string;
  later_cultural_titles: string[];
  remembrance_scale: RemembranceScale;
  memory_state: MemoryState;
  eligibility_rationale: string;
  status: string;
  links: LegendaryFigureLink[];
  created_at?: string;
  updated_at?: string;
}

export interface WorldMemoryPlacement {
  placement_id: string;
  memory_id: string;
  placement_type: string;
  placement_ref: string;
  visibility: string;
  created_at?: string;
}

export interface NPCKnowledgeEntry {
  memory: WorldMemory;
  fidelity: string;
  canonical_truth_visible: boolean;
  reason: string;
}

export interface NPCKnowledgeProjection {
  npc: Record<string, any>;
  subject_entity_type: string;
  subject_entity_id: string;
  entries: NPCKnowledgeEntry[];
  canonical_truth_accessible: boolean;
}

// Phase 17: Campaign Orchestrator

export interface CampaignSourceEvidence {
  source_type: string;
  source_id: string;
  claim_kind?: string;
  note?: string;
}

export interface CampaignInvolvedEntity {
  entity_type: string;
  entity_id: string;
  label?: string;
}

export type RecognitionDecisionKind = 'recognize' | 'reject' | 'rename' | 'reinterpret' | 'postpone' | 'hide';

export interface RecognitionDecision {
  decision: RecognitionDecisionKind;
  new_name?: string;
  reinterpretation?: string;
}

export interface CampaignSession {
  session_id: string;
  campaign_id: string;
  soul_id: string;
  constellation_id?: string;
  status: string;
  current_opportunity_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface CampaignOpportunity {
  opportunity_id: string;
  session_id: string;
  opportunity_type: string;
  eligibility_rule: string;
  source_evidence: CampaignSourceEvidence[];
  involved_entities: CampaignInvolvedEntity[];
  visibility_scope: string;
  urgency_class: string;
  participation: string;
  lifecycle_state: string;
  cooldown_key?: string;
  cooldown_until?: string;
  domain_action: string;
  domain_action_payload: Record<string, any>;
  reasoning: Record<string, any>;
  narration?: string;
  narration_source: string;
  created_at?: string;
  resolved_at?: string;
}

export interface CampaignReaction {
  reaction_id: string;
  transition_id: string;
  system_name: string;
  result_kind: string;
  details: Record<string, any>;
  created_at?: string;
}

export interface CampaignTransition {
  transition_id: string;
  session_id: string;
  opportunity_id?: string;
  canonical_event_id?: string;
  transition_type: string;
  systems_invoked: string[];
  outcomes: Array<Record<string, any>>;
  reactions: CampaignReaction[];
  canonical_change: boolean;
  provider_failure?: string;
  rejected_invalid_transition: boolean;
  created_at?: string;
}

// Phase 18: Soulkeeper Narrative Engine

export interface NarrativeDialogue {
  speaker: string;
  line: string;
  kind: string;
}

export interface NarrativeQuestion {
  prompt: string;
  kind: string;
  choice_hint?: string;
}

export interface NarrativeGeneration {
  generation_id: string;
  session_id?: string;
  opportunity_id?: string;
  transition_id?: string;
  provider: string;
  provider_model: string;
  template_version: string;
  generation_timestamp?: string;
  retry_count: number;
  validation_outcome: string;
  latency_ms?: number;
  used_fallback: boolean;
  context_stats: Record<string, any>;
  output: Record<string, any>;
  error?: string;
}
