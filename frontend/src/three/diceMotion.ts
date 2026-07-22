import * as THREE from 'three';
import type { DiceRole } from './resonanceEffects';

export interface DiceMotionState {
  rollStartedAt: number;
  rolling: boolean;
  seed: number;
  targetQuaternion: THREE.Quaternion;
}

export const createDiceMotionState = (): DiceMotionState => ({
  rollStartedAt: 0,
  rolling: false,
  seed: 0,
  targetQuaternion: new THREE.Quaternion()
});

const hashSeed = (role: DiceRole, rolledValue: number): number => {
  let hash = 2166136261;
  const seedSource = `${role}:${rolledValue}`;

  for (let index = 0; index < seedSource.length; index += 1) {
    hash ^= seedSource.charCodeAt(index);
    hash += (hash << 1) + (hash << 4) + (hash << 7) + (hash << 8) + (hash << 24);
  }

  return Math.abs(hash % 100000);
};

const seededUnit = (seed: number): number => {
  return (Math.sin(seed * 12.9898) * 43758.5453) % 1;
};

export const beginDieRollMotion = (
  state: DiceMotionState,
  role: DiceRole,
  rolledValue: number,
  nowSeconds: number
): void => {
  state.rollStartedAt = nowSeconds;
  state.rolling = true;
  state.seed = hashSeed(role, rolledValue);

  const axis = new THREE.Vector3(
    0.35 + Math.abs(seededUnit(state.seed + 7)),
    0.55 + Math.abs(seededUnit(state.seed + 17)),
    0.3 + Math.abs(seededUnit(state.seed + 29))
  ).normalize();

  const yaw = (Math.PI * 2 * (Math.abs(seededUnit(state.seed + 43)) % 1));
  state.targetQuaternion.setFromAxisAngle(axis, yaw);
};

export const updateDieMotion = (
  mesh: THREE.Mesh,
  state: DiceMotionState,
  nowSeconds: number,
  baseY: number,
  reducedMotion: boolean
): void => {
  if (!state.rolling) {
    mesh.position.y = baseY + Math.sin(nowSeconds * 0.8 + state.seed) * 0.03;
    return;
  }

  const phaseTime = Math.max(0, nowSeconds - state.rollStartedAt);
  const anticipation = reducedMotion ? 0.06 : 0.12;
  const tumble = reducedMotion ? 0.3 : 0.82;
  const settle = reducedMotion ? 0.16 : 0.45;

  if (phaseTime <= anticipation) {
    const t = phaseTime / anticipation;
    mesh.position.y = baseY + Math.sin(t * Math.PI) * 0.16;
    return;
  }

  if (phaseTime <= anticipation + tumble) {
    const t = (phaseTime - anticipation) / tumble;
    const spinVelocity = reducedMotion ? 5.2 : 9.4;
    mesh.rotateX((0.08 + (state.seed % 5) * 0.008) * spinVelocity);
    mesh.rotateY((0.1 + (state.seed % 7) * 0.007) * spinVelocity);
    mesh.position.y = baseY + 0.08 + Math.sin(t * Math.PI * 2) * 0.05;
    return;
  }

  if (phaseTime <= anticipation + tumble + settle) {
    const t = (phaseTime - anticipation - tumble) / settle;
    const damp = Math.exp(-6.5 * t);
    mesh.position.y = baseY + damp * Math.sin(t * Math.PI * 6) * (reducedMotion ? 0.03 : 0.08);
    mesh.quaternion.slerp(state.targetQuaternion, THREE.MathUtils.clamp(t * 1.12, 0, 1));
    return;
  }

  mesh.position.y = baseY;
  mesh.quaternion.copy(state.targetQuaternion);
  state.rolling = false;
};
