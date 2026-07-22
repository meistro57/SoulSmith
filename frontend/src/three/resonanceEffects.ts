import type { CanonicalDiceRead, DiceInterpretation } from '../types';

export type DiceRole = keyof DiceInterpretation;

export interface ResonanceEffect {
  color: string;
  emissiveIntensity: number;
  durationMs: number;
  pulseCount: number;
  particleStyle?: 'dust' | 'ember' | 'ripple' | 'wisp' | 'spark';
  edgeGlow?: boolean;
  numeralGlow?: boolean;
}

export interface ResonanceBundle {
  globalPulse: ResonanceEffect | null;
  perRole: Record<DiceRole, ResonanceEffect>;
}

const rarityFromPercentile = (value: number): 'common' | 'rare' | 'legendary' | 'world' => {
  if (value >= 96) return 'world';
  if (value >= 85) return 'legendary';
  if (value >= 60) return 'rare';
  return 'common';
};

const roleDefaults: Record<DiceRole, ResonanceEffect> = {
  spark: { color: '#f6d792', emissiveIntensity: 0.42, durationMs: 1200, pulseCount: 2, numeralGlow: true },
  domain: { color: '#8fc1ff', emissiveIntensity: 0.26, durationMs: 1400, pulseCount: 1, edgeGlow: true },
  pressure: { color: '#f3a472', emissiveIntensity: 0.34, durationMs: 900, pulseCount: 2 },
  aim: { color: '#ded2ff', emissiveIntensity: 0.2, durationMs: 850, pulseCount: 1 },
  approach: { color: '#9ee7d2', emissiveIntensity: 0.28, durationMs: 1100, pulseCount: 1, particleStyle: 'dust' },
  verdict: { color: '#ffbc89', emissiveIntensity: 0.3, durationMs: 1000, pulseCount: 2 },
  thread: { color: '#f2d6aa', emissiveIntensity: 0.25, durationMs: 800, pulseCount: 1 }
};

export const mapReadToResonance = (read: CanonicalDiceRead): ResonanceBundle => {
  const rarity = rarityFromPercentile(read.raw.percentile);

  const perRole: Record<DiceRole, ResonanceEffect> = {
    ...roleDefaults,
    pressure: {
      ...roleDefaults.pressure,
      emissiveIntensity: 0.22 + (read.raw.d10 / 10) * 0.28,
      pulseCount: read.raw.d10 > 7 ? 3 : 2
    },
    verdict: {
      ...roleDefaults.verdict,
      particleStyle:
        read.interpretation.verdict === 'Ascend' ? 'spark'
          : read.interpretation.verdict === 'Collapse' ? 'wisp'
            : read.interpretation.verdict === 'Reveal' ? 'ripple'
              : 'ember'
    }
  };

  const globalPulse = rarity === 'world'
    ? { color: '#f5e9bf', emissiveIntensity: 0.44, durationMs: 1700, pulseCount: 1, edgeGlow: true, numeralGlow: true }
    : rarity === 'legendary'
      ? { color: '#efdab2', emissiveIntensity: 0.32, durationMs: 1250, pulseCount: 1, edgeGlow: true }
      : rarity === 'rare'
        ? { color: '#d8ccff', emissiveIntensity: 0.24, durationMs: 900, pulseCount: 1 }
        : null;

  return { globalPulse, perRole };
};

export type DiceAudioEventName = 'roll_start' | 'dice_collision' | 'dice_land' | 'resonance_trigger' | 'legendary_pulse';

export const emitDiceAudioEvent = (name: DiceAudioEventName, detail?: Record<string, unknown>): void => {
  window.dispatchEvent(new CustomEvent('soulsmith:dice-audio', { detail: { name, ...detail } }));
};
