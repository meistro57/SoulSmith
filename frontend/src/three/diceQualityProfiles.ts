export type DiceQualityMode = 'low' | 'medium' | 'high' | 'auto';

export interface DiceQualityProfile {
  mode: Exclude<DiceQualityMode, 'auto'>;
  maxPixelRatio: number;
  useTransmission: boolean;
  useBloom: boolean;
  useFresnel: boolean;
  useParticles: boolean;
  shadowMapEnabled: boolean;
  shadowMapSize: number;
  environmentIntensity: number;
  resonanceScale: number;
}

export interface QualityAutoInputs {
  devicePixelRatio: number;
  hardwareConcurrency?: number;
  isWebGL2: boolean;
  averageFps?: number;
}

const PROFILES: Record<Exclude<DiceQualityMode, 'auto'>, DiceQualityProfile> = {
  low: {
    mode: 'low',
    maxPixelRatio: 1,
    useTransmission: false,
    useBloom: false,
    useFresnel: false,
    useParticles: false,
    shadowMapEnabled: true,
    shadowMapSize: 1024,
    environmentIntensity: 0.45,
    resonanceScale: 0.65
  },
  medium: {
    mode: 'medium',
    maxPixelRatio: 1.5,
    useTransmission: true,
    useBloom: false,
    useFresnel: false,
    useParticles: false,
    shadowMapEnabled: true,
    shadowMapSize: 1536,
    environmentIntensity: 0.8,
    resonanceScale: 0.85
  },
  high: {
    mode: 'high',
    maxPixelRatio: 2,
    useTransmission: true,
    useBloom: true,
    useFresnel: true,
    useParticles: true,
    shadowMapEnabled: true,
    shadowMapSize: 2048,
    environmentIntensity: 1.1,
    resonanceScale: 1
  }
};

export const pickAutoQualityMode = (input: QualityAutoInputs): Exclude<DiceQualityMode, 'auto'> => {
  if (!input.isWebGL2) {
    return 'low';
  }

  const concurrency = input.hardwareConcurrency ?? 4;
  const fps = input.averageFps ?? 60;

  if (concurrency <= 4 || input.devicePixelRatio >= 2.5 || fps < 45) {
    return 'low';
  }

  if (concurrency <= 8 || fps < 57) {
    return 'medium';
  }

  return 'high';
};

export const resolveQualityProfile = (
  mode: DiceQualityMode,
  input: QualityAutoInputs
): DiceQualityProfile => {
  if (mode === 'auto') {
    return PROFILES[pickAutoQualityMode(input)];
  }
  return PROFILES[mode];
};
