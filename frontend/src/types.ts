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
