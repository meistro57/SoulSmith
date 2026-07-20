export interface DiceRollRead {
  spark: string;
  domain: string;
  pressure: string;
  aim: string;
  approach: string;
  verdict: string;
  thread: string;
}

export interface SoulResources {
  resonance: number;
  strain: number;
  thread_count: number;
}

export interface Relic {
  id: string;
  name: string;
  stage: 'Dormant' | 'Remembered' | 'Awakened' | 'Overdrawn' | 'Fractured' | 'Transfigured';
  effect: string;
  overdraw_consequence: string;
}

export interface SoulSheet {
  name: string;
  calling: string;
  origin: string;
  desire: string;
  fear: string;
  wound: string;
  resources: SoulResources;
  relics: Relic[];
  bonds: string[];
  scars: string[];
}

export interface CanonGuardianAudit {
  passed: boolean;
  gate_name: string;
  details: string;
}

export interface SoulkeeperNarration {
  title: string;
  prose: string;
  tone: string;
  scene_beats: string[];
  canon_writeback: string[];
  guardian_audit: CanonGuardianAudit[];
}

export interface ResolveOutcome {
  outcome_class: 'ascendancy' | 'marked_success' | 'revelatory_failure' | 'collapse';
  outcome_title: string;
  rules_summary: string;
  resonance_delta: number;
  strain_delta: number;
  thread_delta: number;
  new_resources: SoulResources;
  fracture_triggered: boolean;
  canon_facts: string[];
}

export interface ResolvedScene {
  outcome: ResolveOutcome;
  narration: SoulkeeperNarration;
  event_id: string;
  timestamp?: string;
  dice_read?: DiceRollRead;
}

export interface SoulprintProfile {
  sun_sign: string;
  moon_sign: string;
  ascendant_sign: string;
  elemental_balance: Record<string, number>;
  motifs: Array<{ tag: string; weight: number; description: string }>;
  favored_domains: string[];
  favored_threads: string[];
  narrative_hooks: string[];
  privacy_notice: string;
}
