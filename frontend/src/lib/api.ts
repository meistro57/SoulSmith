import type { AlternateSceneResult, Aspect, AuthResponse, AwakeningStage, CanonicalDiceRead, Constellation, ConstellationStageInfo, CrossAspectBond, EncounterFrame, IntegrationEvent, LocalThread, ManifestationType, NumericDiceRoll, OpenQuestion, ProbablePath, ProbablePathStatus, Relic, RelicEvent, ResolvedScene, Seed, SoulResources, SoulprintProfile, User } from '../types';

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '');
const AUTH_TOKEN_KEY = 'soulsmith_auth_token';

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
};
