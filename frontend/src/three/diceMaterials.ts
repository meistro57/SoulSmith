import * as THREE from 'three';
import type { DiceQualityProfile } from './diceQualityProfiles';

export type DiceMaterialMode = 'resin' | 'crystal' | 'gemstone' | 'performance';

export interface DiceMaterialSettings {
  mode: DiceMaterialMode;
  colorHex: string;
  opacity: number;
  transparent: boolean;
  quality: DiceQualityProfile;
}

const clampOpacity = (opacity: number): number => THREE.MathUtils.clamp(opacity, 0.15, 1);

export const createDiceBodyMaterial = (settings: DiceMaterialSettings): THREE.Material => {
  const color = new THREE.Color(settings.colorHex);
  const baseTransparent = settings.transparent || settings.mode === 'crystal';
  const materialCommon = {
    color,
    transparent: baseTransparent,
    opacity: baseTransparent ? clampOpacity(settings.opacity) : 1,
    envMapIntensity: settings.quality.environmentIntensity,
    metalness: 0,
    side: THREE.FrontSide
  } as const;

  if (settings.mode === 'performance' || settings.quality.mode === 'low') {
    return new THREE.MeshStandardMaterial({
      ...materialCommon,
      roughness: 0.26
    });
  }

  if (settings.mode === 'crystal') {
    return new THREE.MeshPhysicalMaterial({
      ...materialCommon,
      roughness: 0.06,
      clearcoat: 1,
      clearcoatRoughness: 0.02,
      transmission: settings.quality.useTransmission ? THREE.MathUtils.clamp(settings.opacity + 0.2, 0.85, 1) : 0,
      ior: 1.5,
      thickness: 0.6,
      attenuationColor: color.clone().lerp(new THREE.Color('#ffffff'), 0.45),
      attenuationDistance: 1.4,
      depthWrite: !baseTransparent
    });
  }

  if (settings.mode === 'gemstone') {
    return new THREE.MeshPhysicalMaterial({
      ...materialCommon,
      roughness: 0.2,
      clearcoat: 0.92,
      clearcoatRoughness: 0.07,
      transmission: 0,
      ior: 1.45,
      thickness: 0.45,
      emissive: color.clone().multiplyScalar(0.03),
      depthWrite: true
    });
  }

  return new THREE.MeshPhysicalMaterial({
    ...materialCommon,
    roughness: 0.18,
    clearcoat: 1,
    clearcoatRoughness: 0.05,
    transmission: settings.quality.useTransmission ? THREE.MathUtils.clamp(settings.opacity * 0.6, 0.2, 0.55) : 0,
    ior: 1.45,
    thickness: 0.5,
    attenuationColor: color.clone().lerp(new THREE.Color('#f3f7ff'), 0.22),
    attenuationDistance: 1.8,
    depthWrite: !baseTransparent
  });
};

export const createNumeralMaterial = (): THREE.SpriteMaterial => {
  return new THREE.SpriteMaterial({
    transparent: true,
    depthTest: true,
    depthWrite: false
  });
};

export const createFresnelShellMaterial = (colorHex: string): THREE.ShaderMaterial => {
  const color = new THREE.Color(colorHex).lerp(new THREE.Color('#ffffff'), 0.5);
  return new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    side: THREE.BackSide,
    uniforms: {
      uColor: { value: color },
      uPower: { value: 2.6 },
      uBias: { value: 0.09 },
      uScale: { value: 0.62 }
    },
    vertexShader: `
      varying vec3 vNormal;
      varying vec3 vViewDir;
      void main() {
        vec4 worldPosition = modelMatrix * vec4(position, 1.0);
        vNormal = normalize(mat3(modelMatrix) * normal);
        vViewDir = normalize(cameraPosition - worldPosition.xyz);
        gl_Position = projectionMatrix * viewMatrix * worldPosition;
      }
    `,
    fragmentShader: `
      uniform vec3 uColor;
      uniform float uPower;
      uniform float uBias;
      uniform float uScale;
      varying vec3 vNormal;
      varying vec3 vViewDir;
      void main() {
        float fresnel = uBias + uScale * pow(1.0 - max(dot(normalize(vNormal), normalize(vViewDir)), 0.0), uPower);
        gl_FragColor = vec4(uColor, clamp(fresnel, 0.0, 0.35));
      }
    `
  });
};
