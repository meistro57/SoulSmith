import type { CanonicalDiceRead, EncounterFrame, IntegrationEvent, LocalThread, NumericDiceRoll, OpenQuestion, ResolvedScene, Seed, SoulResources, SoulprintProfile } from '../types';

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '');

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
  });
  if (!response.ok) throw new Error(`SoulSmith API ${response.status}: ${response.statusText}`);
  return response.json() as Promise<T>;
}

export const apiClient = {
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
};
