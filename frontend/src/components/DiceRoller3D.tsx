import React, { useEffect, useMemo, useRef, useState } from 'react';
import type { CanonicalDiceRead, DiceInterpretation } from '../types';
import { apiClient } from '../lib/api';
import { RefreshCw, Eye, BookOpen, Layers, Box, Sliders, Palette, EyeOff, Gauge, Sparkles } from 'lucide-react';
import * as THREE from 'three';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { createDiceEnvironment } from '../three/createDiceEnvironment';
import { createDiceLighting } from '../three/createDiceLighting';
import { createDiceShadows } from '../three/createDiceShadows';
import { createDiceBodyMaterial, createFresnelShellMaterial } from '../three/diceMaterials';
import { prepareDiceGeometry } from '../three/prepareDiceGeometry';
import { createParticlePool } from '../three/particlePool';
import { createDiceMotionState, beginDieRollMotion, updateDieMotion } from '../three/diceMotion';
import { emitDiceAudioEvent, mapReadToResonance, type DiceRole } from '../three/resonanceEffects';
import { resolveQualityProfile, type DiceQualityMode } from '../three/diceQualityProfiles';
import { disposeSceneResources } from '../three/disposeSceneResources';

interface DiceRoller3DProps {
  currentRead: CanonicalDiceRead;
  onRollComplete: (newRead: CanonicalDiceRead) => void;
  isRolling: boolean;
  setIsRolling: (rolling: boolean) => void;
}

type DiceMaterialMode = 'resin' | 'crystal' | 'gemstone' | 'performance';

const PRESET_COLORS = [
  { name: 'Sapphire', hex: '#1e5285' },
  { name: 'Ruby', hex: '#991b1b' },
  { name: 'Amethyst', hex: '#6b21a8' },
  { name: 'Emerald', hex: '#065f46' },
  { name: 'Amber', hex: '#b45309' },
  { name: 'Obsidian', hex: '#111318' }
];

const DIE_ROLE_META: Record<keyof DiceInterpretation, { category: string; poly: string; stlPath: string; icon: string; discovery: string }> = {
  spark: { category: 'WHAT', poly: 'd20', stlPath: '/art/stl/d20.stl', icon: '/art/dice/d20.png', discovery: 'What You Discover' },
  domain: { category: 'WHERE', poly: 'd12', stlPath: '/art/stl/d12.stl', icon: '/art/dice/d12.png', discovery: 'Where It Happens' },
  pressure: { category: 'HOW VIVID', poly: 'd10', stlPath: '/art/stl/d10.stl', icon: '/art/dice/d10.png', discovery: 'Intensity & Load' },
  aim: { category: 'RARITY', poly: 'd%', stlPath: '/art/stl/d10.stl', icon: '/art/dice/d%.png', discovery: 'Probability' },
  approach: { category: 'WHO', poly: 'd8', stlPath: '/art/stl/d8.stl', icon: '/art/dice/d8.png', discovery: 'Who You Encounter' },
  verdict: { category: 'ELEMENT', poly: 'd6', stlPath: '/art/stl/d6.stl', icon: '/art/dice/d6.png', discovery: 'Energy & Power' },
  thread: { category: 'OUTCOME', poly: 'd4', stlPath: '/art/stl/d4.stl', icon: '/art/dice/d4.png', discovery: 'Outcome Twist' }
};

interface RuntimeDice {
  mesh: THREE.Mesh;
  motion: ReturnType<typeof createDiceMotionState>;
  numeralSprite: THREE.Sprite;
  labelSprite: THREE.Sprite;
  fresnelShell: THREE.Mesh | null;
}

interface RuntimeState {
  renderer: THREE.WebGLRenderer;
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  composer: EffectComposer | null;
  diceByRole: Record<DiceRole, RuntimeDice>;
  particlePool: ReturnType<typeof createParticlePool> | null;
  resonanceUntil: number;
  resonanceColor: THREE.Color;
  resonanceIntensity: number;
  environmentDispose: () => void;
  disposeAll: () => void;
  clock: THREE.Clock;
  fpsFrames: number;
  fpsAccum: number;
  avgFps: number;
}

const getNumericForRole = (read: CanonicalDiceRead, role: DiceRole): number => {
  const numericValue = {
    spark: read.raw.d20,
    domain: read.raw.d12,
    pressure: read.raw.d10,
    aim: read.raw.percentile,
    approach: read.raw.d8,
    verdict: read.raw.d6,
    thread: read.raw.d4
  } as const;
  return numericValue[role];
};

const buildReadSignature = (read: CanonicalDiceRead): string => {
  return `${read.raw.d20}-${read.raw.d12}-${read.raw.d10}-${read.raw.percentile}-${read.raw.d8}-${read.raw.d6}-${read.raw.d4}`;
};

const createStaticFloatingLabelTexture = (category: string, poly: string, rolledValue: string, discovery: string): THREE.CanvasTexture => {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 320;
  const ctx = canvas.getContext('2d');
  if (!ctx) {
    return new THREE.CanvasTexture(canvas);
  }

  ctx.fillStyle = 'rgba(8, 12, 20, 0.82)';
  ctx.strokeStyle = 'rgba(203, 167, 102, 0.33)';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.roundRect(14, 16, 484, 286, 24);
  ctx.fill();
  ctx.stroke();

  ctx.font = 'bold 34px JetBrains Mono, monospace';
  ctx.fillStyle = '#8ad6f2';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  ctx.fillText(`${category} (${poly})`, 256, 42);

  ctx.shadowColor = 'rgba(255, 255, 255, 0.7)';
  ctx.shadowBlur = 8;
  ctx.fillStyle = '#f7f3e7';
  ctx.font = '700 60px Cinzel, serif';
  ctx.fillText(rolledValue, 256, 106);

  ctx.shadowBlur = 0;
  ctx.font = 'italic 31px EB Garamond, serif';
  ctx.fillStyle = '#ece3cf';
  ctx.fillText(discovery, 256, 214);

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.needsUpdate = true;
  return texture;
};

const createNumeralBadgeTexture = (numericValue: number): THREE.CanvasTexture => {
  const canvas = document.createElement('canvas');
  canvas.width = 256;
  canvas.height = 256;
  const ctx = canvas.getContext('2d');
  if (!ctx) {
    return new THREE.CanvasTexture(canvas);
  }

  const gradient = ctx.createRadialGradient(128, 118, 20, 128, 128, 110);
  gradient.addColorStop(0, 'rgba(252, 248, 235, 0.97)');
  gradient.addColorStop(1, 'rgba(236, 225, 198, 0.93)');
  ctx.fillStyle = gradient;
  ctx.beginPath();
  ctx.arc(128, 128, 90, 0, Math.PI * 2);
  ctx.fill();

  ctx.strokeStyle = 'rgba(164, 127, 69, 0.78)';
  ctx.lineWidth = 4;
  ctx.stroke();

  ctx.fillStyle = '#1f1a12';
  ctx.font = '700 72px Cinzel, serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(String(numericValue), 128, 136);

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.needsUpdate = true;
  return texture;
};

const getMotionPreference = (): boolean => {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
};

export const DiceRoller3D: React.FC<DiceRoller3DProps> = ({
  currentRead,
  onRollComplete,
  isRolling,
  setIsRolling
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const runtimeRef = useRef<RuntimeState | null>(null);
  const animationRef = useRef<number | null>(null);
  const previousReadSignatureRef = useRef<string>(buildReadSignature(currentRead));

  const [activeDie, setActiveDie] = useState<keyof DiceInterpretation>('spark');
  const [showDestinyChart, setShowDestinyChart] = useState(false);
  const [stlLoadedCount, setStlLoadedCount] = useState(0);
  const [isTransparentMode, setIsTransparentMode] = useState(true);
  const [customHex, setCustomHex] = useState('#1e5285');
  const [opacityLevel, setOpacityLevel] = useState(0.6);
  const [showColorControls, setShowColorControls] = useState(false);
  const [diceMaterialMode, setDiceMaterialMode] = useState<DiceMaterialMode>('resin');
  const [qualityMode, setQualityMode] = useState<DiceQualityMode>('high');
  const [magicalEffectsEnabled, setMagicalEffectsEnabled] = useState(true);
  const [postProcessingEnabled, setPostProcessingEnabled] = useState(true);
  const [reducedEffectsEnabled, setReducedEffectsEnabled] = useState(false);
  const [debugStatsVisible, setDebugStatsVisible] = useState(false);
  const [creaseAngleDeg, setCreaseAngleDeg] = useState(35);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(getMotionPreference);
  const [avgFps, setAvgFps] = useState(0);

  const qualityProfile = useMemo(() => {
    return resolveQualityProfile(qualityMode, {
      devicePixelRatio: window.devicePixelRatio || 1,
      hardwareConcurrency: navigator.hardwareConcurrency,
      isWebGL2: !!window.WebGL2RenderingContext
    });
  }, [qualityMode]);

  const reducedMotionActive = prefersReducedMotion || reducedEffectsEnabled;

  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handler = () => setPrefersReducedMotion(media.matches);
    media.addEventListener('change', handler);
    return () => media.removeEventListener('change', handler);
  }, []);

  const handleRollAll = async () => {
    if (isRolling) return;
    setIsRolling(true);
    emitDiceAudioEvent('roll_start');

    try {
      const data = await apiClient.rollDice();

      setTimeout(() => {
        onRollComplete(data);
        setIsRolling(false);
      }, reducedMotionActive ? 520 : 1120);
    } catch {
      setTimeout(() => {
        onRollComplete(generateFallbackRoll());
        setIsRolling(false);
      }, reducedMotionActive ? 520 : 1120);
    }
  };

  const generateFallbackRoll = (): CanonicalDiceRead => {
    const sparks = ['Heart', 'Mind', 'Shadow', 'Wild', 'Wound', 'Wonder'];
    const domains = ['Self', 'Ally', 'Foe', 'Place', 'Relic', 'Omen'];
    const pressures = ['Time', 'Fear', 'Debt', 'Exposure', 'Corruption', 'Scarcity'];
    const aims = ['Seek', 'Protect', 'Bind', 'Break', 'Reveal', 'Transform'];
    const approaches = ['Edge', 'Grace', 'Guile', 'Lore', 'Empathy', 'Craft'];
    const verdicts = ['Ascend', 'Scar', 'Stall', 'Twist', 'Reveal', 'Collapse'];
    const threads = ['Bond', 'Memory', 'Mark', 'Prophecy'];

    const pick = (arr: string[]) => arr[Math.floor(Math.random() * arr.length)];
    const interpretation = {
      spark: pick(sparks),
      domain: pick(domains),
      pressure: pick(pressures),
      aim: pick(aims),
      approach: pick(approaches),
      verdict: pick(verdicts),
      thread: pick(threads)
    };

    return {
      raw: {
        d20: Math.ceil(Math.random() * 20),
        d12: Math.ceil(Math.random() * 12),
        d10: Math.ceil(Math.random() * 10),
        percentile: Math.ceil(Math.random() * 100),
        d8: Math.ceil(Math.random() * 8),
        d6: Math.ceil(Math.random() * 6),
        d4: Math.ceil(Math.random() * 4)
      },
      grammar_version: '1.0.0',
      interpretation,
      grammar_sentence: `Driven by [${interpretation.spark}], the Soul attempts to [${interpretation.aim}] upon [${interpretation.domain}] using [${interpretation.approach}] against the pressure of [${interpretation.pressure}].`
    };
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = qualityProfile.mode === 'high' ? 1.02 : 0.96;
    renderer.shadowMap.enabled = qualityProfile.shadowMapEnabled;
    renderer.shadowMap.type = qualityProfile.mode === 'high' ? THREE.PCFSoftShadowMap : THREE.PCFShadowMap;
    if ('useLegacyLights' in renderer) {
      (renderer as unknown as { useLegacyLights: boolean }).useLegacyLights = false;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, qualityProfile.maxPixelRatio));
    renderer.setSize(canvas.clientWidth, canvas.clientHeight, false);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(37, canvas.clientWidth / canvas.clientHeight, 0.1, 120);
    camera.position.set(0, 1.5, 9.2);
    scene.add(camera);

    const environment = createDiceEnvironment(renderer);
    scene.environment = environment.texture;

    createDiceLighting(scene);
    createDiceShadows(scene);

    const composer = postProcessingEnabled && qualityProfile.useBloom
      ? new EffectComposer(renderer)
      : null;

    if (composer) {
      composer.setPixelRatio(Math.min(window.devicePixelRatio || 1, qualityProfile.maxPixelRatio));
      composer.setSize(canvas.clientWidth, canvas.clientHeight);
      composer.addPass(new RenderPass(scene, camera));
      composer.addPass(new UnrealBloomPass(new THREE.Vector2(canvas.clientWidth, canvas.clientHeight), 0.25, 0.55, 1.05));
    }

    const stlLoader = new STLLoader();
    const diceGroup = new THREE.Group();
    scene.add(diceGroup);

    const roleOrder = Object.keys(DIE_ROLE_META) as DiceRole[];
    const spacing = 2.05;
    const startX = -spacing * 3;

    const diceByRole = {} as Record<DiceRole, RuntimeDice>;
    let loadedCounter = 0;

    const baseOpacity = isTransparentMode ? opacityLevel : 1;

    roleOrder.forEach((role, idx) => {
      const meta = DIE_ROLE_META[role];
      const posX = startX + idx * spacing;
      const numericValue = getNumericForRole(currentRead, role);
      const interpretedValue = currentRead.interpretation[role];

      stlLoader.load(
        meta.stlPath,
        (rawGeometry) => {
          const geometry = prepareDiceGeometry(rawGeometry, {
            targetRadius: 0.86,
            creaseAngleDeg
          });

          const material = createDiceBodyMaterial({
            mode: diceMaterialMode,
            colorHex: customHex,
            opacity: baseOpacity,
            transparent: isTransparentMode,
            quality: qualityProfile
          });

          const mesh = new THREE.Mesh(geometry, material);
          mesh.position.set(posX, 0.7, 0);
          mesh.castShadow = true;
          mesh.receiveShadow = false;

          const fresnelShell = qualityProfile.useFresnel
            ? new THREE.Mesh(geometry.clone(), createFresnelShellMaterial(customHex))
            : null;

          if (fresnelShell) {
            fresnelShell.scale.setScalar(1.017);
            fresnelShell.renderOrder = 2;
            mesh.add(fresnelShell);
          }

          const numeralTexture = createNumeralBadgeTexture(numericValue);
          const numeralSprite = new THREE.Sprite(new THREE.SpriteMaterial({
            map: numeralTexture,
            transparent: true,
            depthWrite: false,
            opacity: 0.96
          }));
          numeralSprite.position.set(0, 1.1, 0);
          numeralSprite.scale.set(0.54, 0.54, 1);
          mesh.add(numeralSprite);

          const labelTexture = createStaticFloatingLabelTexture(meta.category, meta.poly, interpretedValue, meta.discovery);
          const labelSprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: labelTexture, transparent: true, depthWrite: false }));
          labelSprite.scale.set(1.92, 1.16, 1);
          labelSprite.position.set(posX, -1.3, 0);
          scene.add(labelSprite);

          diceGroup.add(mesh);
          diceByRole[role] = {
            mesh,
            motion: createDiceMotionState(),
            numeralSprite,
            labelSprite,
            fresnelShell
          };

          loadedCounter += 1;
          setStlLoadedCount(loadedCounter);
        },
        undefined,
        () => {
          const fallbackGeometry = new THREE.IcosahedronGeometry(0.84);
          const fallbackMaterial = createDiceBodyMaterial({
            mode: qualityProfile.mode === 'low' ? 'performance' : diceMaterialMode,
            colorHex: customHex,
            opacity: baseOpacity,
            transparent: isTransparentMode,
            quality: qualityProfile
          });
          const fallbackMesh = new THREE.Mesh(fallbackGeometry, fallbackMaterial);
          fallbackMesh.position.set(posX, 0.7, 0);
          fallbackMesh.castShadow = true;
          diceGroup.add(fallbackMesh);
          diceByRole[role] = {
            mesh: fallbackMesh,
            motion: createDiceMotionState(),
            numeralSprite: new THREE.Sprite(),
            labelSprite: new THREE.Sprite(),
            fresnelShell: null
          };
          loadedCounter += 1;
          setStlLoadedCount(loadedCounter);
        }
      );
    });

    const particlePool = qualityProfile.useParticles && magicalEffectsEnabled && !reducedMotionActive
      ? createParticlePool()
      : null;

    if (particlePool) {
      scene.add(particlePool.points);
    }

    const runtime: RuntimeState = {
      renderer,
      scene,
      camera,
      composer,
      diceByRole,
      particlePool,
      resonanceUntil: 0,
      resonanceColor: new THREE.Color('#ffffff'),
      resonanceIntensity: 0,
      environmentDispose: environment.dispose,
      disposeAll: () => {
        if (particlePool) {
          scene.remove(particlePool.points);
          particlePool.dispose();
        }

        disposeSceneResources(scene);
        composer?.dispose();
        environment.dispose();
        renderer.dispose();
      },
      clock: new THREE.Clock(),
      fpsFrames: 0,
      fpsAccum: 0,
      avgFps: 0
    };

    runtimeRef.current = runtime;

    const animate = (): void => {
      const activeRuntime = runtimeRef.current;
      if (!activeRuntime) return;

      const delta = activeRuntime.clock.getDelta();
      const elapsed = activeRuntime.clock.elapsedTime;
      const nowMs = performance.now();

      roleOrder.forEach((role) => {
        const runtimeDie = activeRuntime.diceByRole[role];
        if (!runtimeDie) return;

        updateDieMotion(runtimeDie.mesh, runtimeDie.motion, elapsed, 0.7, reducedMotionActive);
        runtimeDie.labelSprite.position.y = -1.32 + Math.sin(elapsed * 1.2 + role.length) * 0.018;
      });

      if (activeRuntime.resonanceUntil > nowMs) {
        const progress = 1 - (activeRuntime.resonanceUntil - nowMs) / 1600;
        const pulse = Math.sin(progress * Math.PI * 6) * (1 - progress);
        roleOrder.forEach((role) => {
          const runtimeDie = activeRuntime.diceByRole[role];
          if (!runtimeDie) return;
          const material = runtimeDie.mesh.material;
          if (material instanceof THREE.MeshPhysicalMaterial || material instanceof THREE.MeshStandardMaterial) {
            material.emissive = activeRuntime.resonanceColor;
            material.emissiveIntensity = Math.max(0, activeRuntime.resonanceIntensity * pulse);
          }
          runtimeDie.numeralSprite.material.opacity = THREE.MathUtils.clamp(0.85 + pulse * 0.25, 0.7, 1);
        });
      }

      if (activeRuntime.particlePool) {
        activeRuntime.particlePool.update(delta);
      }

      if (activeRuntime.composer) {
        activeRuntime.composer.render();
      } else {
        activeRuntime.renderer.render(activeRuntime.scene, activeRuntime.camera);
      }

      activeRuntime.fpsFrames += 1;
      activeRuntime.fpsAccum += delta;
      if (activeRuntime.fpsAccum >= 0.75) {
        activeRuntime.avgFps = Math.round(activeRuntime.fpsFrames / activeRuntime.fpsAccum);
        setAvgFps(activeRuntime.avgFps);
        activeRuntime.fpsFrames = 0;
        activeRuntime.fpsAccum = 0;
      }

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    const handleResize = () => {
      const activeRuntime = runtimeRef.current;
      const activeCanvas = canvasRef.current;
      if (!activeRuntime || !activeCanvas) return;

      activeRuntime.camera.aspect = activeCanvas.clientWidth / activeCanvas.clientHeight;
      activeRuntime.camera.updateProjectionMatrix();
      activeRuntime.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, qualityProfile.maxPixelRatio));
      activeRuntime.renderer.setSize(activeCanvas.clientWidth, activeCanvas.clientHeight, false);
      activeRuntime.composer?.setSize(activeCanvas.clientWidth, activeCanvas.clientHeight);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (animationRef.current !== null) {
        cancelAnimationFrame(animationRef.current);
      }
      runtime.disposeAll();
      runtimeRef.current = null;
    };
  }, [currentRead, customHex, diceMaterialMode, isTransparentMode, magicalEffectsEnabled, opacityLevel, postProcessingEnabled, qualityProfile, creaseAngleDeg, reducedMotionActive]);

  useEffect(() => {
    if (!isRolling) {
      return;
    }

    const runtime = runtimeRef.current;
    if (!runtime) {
      return;
    }

    const roles = Object.keys(DIE_ROLE_META) as DiceRole[];
    roles.forEach((role) => {
      const runtimeDie = runtime.diceByRole[role];
      if (!runtimeDie) return;
      beginDieRollMotion(runtimeDie.motion, role, getNumericForRole(currentRead, role), runtime.clock.elapsedTime);
    });

    emitDiceAudioEvent('dice_collision');
  }, [currentRead, isRolling]);

  useEffect(() => {
    const signature = buildReadSignature(currentRead);
    const previousSignature = previousReadSignatureRef.current;
    previousReadSignatureRef.current = signature;

    if (signature === previousSignature || !magicalEffectsEnabled) {
      return;
    }

    const runtime = runtimeRef.current;
    if (!runtime) {
      return;
    }

    const resonance = mapReadToResonance(currentRead);
    const now = performance.now();

    let strongest = 0;
    let strongestColor = '#fffaf2';

    const roles = Object.keys(DIE_ROLE_META) as DiceRole[];
    roles.forEach((role) => {
      const runtimeDie = runtime.diceByRole[role];
      if (!runtimeDie) return;

      const effect = resonance.perRole[role];
      const scaledIntensity = effect.emissiveIntensity * qualityProfile.resonanceScale;
      if (scaledIntensity > strongest) {
        strongest = scaledIntensity;
        strongestColor = effect.color;
      }

      if (runtime.particlePool && !reducedMotionActive && effect.particleStyle) {
        const worldPosition = new THREE.Vector3();
        runtimeDie.mesh.getWorldPosition(worldPosition);
        runtime.particlePool.spawnBurst(worldPosition, effect.color, effect.pulseCount * 4);
      }
    });

    runtime.resonanceUntil = now + (resonance.globalPulse?.durationMs ?? 980);
    runtime.resonanceColor.set(resonance.globalPulse?.color ?? strongestColor);
    runtime.resonanceIntensity = resonance.globalPulse?.emissiveIntensity ?? strongest;

    emitDiceAudioEvent('resonance_trigger', { rarity: currentRead.raw.percentile });
    if (resonance.globalPulse) {
      emitDiceAudioEvent('legendary_pulse', { percentile: currentRead.raw.percentile });
    }

    emitDiceAudioEvent('dice_land');
  }, [currentRead, magicalEffectsEnabled, qualityProfile.resonanceScale, reducedMotionActive]);

  return (
    <div className="space-y-8">
      <div className="relative rounded-3xl overflow-hidden artifact-frame border border-[var(--line)] bg-[#05040a] flex flex-col items-center justify-center p-4 md:p-6">
        <div className="w-full max-w-4xl max-h-72 md:max-h-80 overflow-hidden flex items-center justify-center">
          <img
            src="/art/soulsmith.png"
            alt="SoulSmith Mythic Key Art"
            className="w-full h-full object-contain object-center max-h-72 md:max-h-80"
          />
        </div>

        <div className="w-full pt-4 flex flex-col justify-end text-center items-center">
          <div className="portal mb-3" />

          <p className="eyebrow center mb-1">
            A collaborative mythology game of memory, choice, and consequence
          </p>

          <h2 className="text-2xl md:text-4xl font-black font-cinzel tracking-wide mb-2">
            <span className="shimmer">The dice spark it.</span> You write the legend.
          </h2>

          <p className="font-body text-sm md:text-base text-[var(--parchment)] max-w-2xl italic opacity-90 leading-relaxed">
            Roll seven dice, decode one encounter, and let your choices reshape a world that remembers what happened.
          </p>
        </div>
      </div>

      <div className="mythic-card p-6 md:p-8 relative overflow-hidden text-center">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4 border-b border-[var(--line)] pb-4">
          <div className="text-left">
            <p className="eyebrow mb-0.5 flex items-center gap-1.5">
              <Box size={14} className="text-[var(--spark)]" /> Premium STL Dice Render Sanctum
            </p>
            <h3 className="text-3xl font-black font-cinzel text-[var(--gold)]">
              Seven Dice of Destiny Sanctuary
            </h3>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => setIsTransparentMode(!isTransparentMode)}
              className={`px-3 py-1.5 rounded-xl text-xs font-mono flex items-center gap-1.5 transition ${
                isTransparentMode
                  ? 'bg-[var(--spark)] text-[var(--void)] font-bold shadow-md'
                  : 'bg-[var(--deep)] text-[var(--parchment)] border border-[var(--line)]'
              }`}
            >
              {isTransparentMode ? <Eye size={14} /> : <EyeOff size={14} />}
              {isTransparentMode ? 'Transparency: ON' : 'Transparency: OFF'}
            </button>

            <button
              onClick={() => setShowColorControls(!showColorControls)}
              className="btn-glass text-xs flex items-center gap-1.5"
            >
              <Palette size={14} className="text-[var(--gold)]" />
              Render Controls
            </button>

            <button
              onClick={() => setShowDestinyChart(!showDestinyChart)}
              className="btn-glass text-xs flex items-center gap-1.5"
            >
              <BookOpen size={14} className="text-[var(--gold)]" />
              {showDestinyChart ? 'Hide Chart' : 'Show Destiny Chart'}
            </button>
          </div>
        </div>

        {showColorControls && (
          <div className="p-5 rounded-2xl bg-[var(--deep)] border border-[var(--line)] space-y-4 mb-5 text-left">
            <div className="grid gap-3 md:grid-cols-2">
              <label className="text-xs font-mono text-[var(--parchment)] flex flex-col gap-1">
                Dice Material
                <select
                  value={diceMaterialMode}
                  onChange={(event) => setDiceMaterialMode(event.target.value as DiceMaterialMode)}
                  className="bg-[var(--void)] border border-[var(--line)] rounded-lg px-3 py-2"
                >
                  <option value="resin">Polished Resin</option>
                  <option value="crystal">Crystal / Glass</option>
                  <option value="gemstone">Opaque Gemstone</option>
                  <option value="performance">Performance Mode</option>
                </select>
              </label>

              <label className="text-xs font-mono text-[var(--parchment)] flex flex-col gap-1">
                Graphics Quality
                <select
                  value={qualityMode}
                  onChange={(event) => setQualityMode(event.target.value as DiceQualityMode)}
                  className="bg-[var(--void)] border border-[var(--line)] rounded-lg px-3 py-2"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="auto">Auto</option>
                </select>
              </label>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-mono text-[var(--parchment)] opacity-75 mr-2">Presets:</span>
              {PRESET_COLORS.map((preset) => (
                <button
                  key={preset.name}
                  onClick={() => setCustomHex(preset.hex)}
                  className="px-3 py-1.5 rounded-xl text-xs font-mono flex items-center gap-2 border border-[var(--line)] bg-[var(--void)] hover:border-[var(--gold)] transition"
                >
                  <span className="w-3.5 h-3.5 rounded-full border border-white/40" style={{ backgroundColor: preset.hex }} />
                  <span>{preset.name}</span>
                </button>
              ))}
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <label className="text-xs font-mono text-[var(--parchment)] flex flex-col gap-2">
                Dice Color
                <input
                  type="color"
                  value={customHex}
                  onChange={(event) => setCustomHex(event.target.value)}
                  className="w-12 h-10 rounded-lg bg-transparent border border-[var(--line)] cursor-pointer"
                />
              </label>

              <label className="text-xs font-mono text-[var(--parchment)] flex flex-col gap-2">
                Crease Normals Angle ({creaseAngleDeg}°)
                <input
                  type="range"
                  min={25}
                  max={45}
                  step={1}
                  value={creaseAngleDeg}
                  onChange={(event) => setCreaseAngleDeg(parseInt(event.target.value, 10))}
                  className="accent-[var(--spark)]"
                />
              </label>
            </div>

            {isTransparentMode && (
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pt-2 border-t border-[var(--line)]">
                <div className="flex items-center gap-2">
                  <Sliders size={14} className="text-[var(--spark)]" />
                  <span className="text-xs font-mono text-[var(--parchment)]">Opacity:</span>
                </div>
                <div className="flex items-center gap-3 w-full sm:w-64">
                  <input
                    type="range"
                    min={0.15}
                    max={0.95}
                    step={0.05}
                    value={opacityLevel}
                    onChange={(event) => setOpacityLevel(parseFloat(event.target.value))}
                    className="w-full accent-[var(--spark)] cursor-pointer"
                  />
                  <span className="text-xs font-mono text-[var(--spark)] font-bold w-12 text-right">
                    {(opacityLevel * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            )}

            <div className="grid gap-2 md:grid-cols-2 text-xs font-mono text-[var(--parchment)]">
              <label className="flex items-center gap-2"><input type="checkbox" checked={magicalEffectsEnabled} onChange={(event) => setMagicalEffectsEnabled(event.target.checked)} /> Magical resonance</label>
              <label className="flex items-center gap-2"><input type="checkbox" checked={postProcessingEnabled} onChange={(event) => setPostProcessingEnabled(event.target.checked)} /> Bloom post-processing</label>
              <label className="flex items-center gap-2"><input type="checkbox" checked={reducedEffectsEnabled} onChange={(event) => setReducedEffectsEnabled(event.target.checked)} /> Reduced effects</label>
              <label className="flex items-center gap-2"><input type="checkbox" checked={debugStatsVisible} onChange={(event) => setDebugStatsVisible(event.target.checked)} /> Debug stats</label>
            </div>
          </div>
        )}

        <div className="flex justify-between items-center text-xs font-mono mb-3 text-left">
          <span className="text-[var(--spark)]">
            ✦ 3D STL Dice Models: {stlLoadedCount} / 7
          </span>
          <span className="mythic-pill border-[var(--gold-dim)] text-[var(--gold)] flex items-center gap-1.5">
            <Gauge size={12} /> {qualityProfile.mode.toUpperCase()}
          </span>
        </div>

        {debugStatsVisible && (
          <div className="mb-3 text-left text-[11px] font-mono text-[var(--parchment)]/80 flex flex-wrap gap-3">
            <span>FPS: {avgFps}</span>
            <span>DPR cap: {qualityProfile.maxPixelRatio}</span>
            <span>Bloom: {qualityProfile.useBloom && postProcessingEnabled ? 'on' : 'off'}</span>
            <span>Particles: {qualityProfile.useParticles && magicalEffectsEnabled && !reducedMotionActive ? 'on' : 'off'}</span>
            <span>Reduced motion: {reducedMotionActive ? 'on' : 'off'}</span>
          </div>
        )}

        <div className="w-full h-72 md:h-80 relative rounded-2xl overflow-hidden bg-gradient-to-b from-[#070a14] via-[#091322] to-[#070a14] border border-[var(--line)] mb-6 shadow-2xl">
          <canvas ref={canvasRef} className="w-full h-full block" />
        </div>

        <div className="flex flex-wrap justify-center items-center gap-3 md:gap-4 mb-6">
          {(Object.keys(DIE_ROLE_META) as Array<keyof DiceInterpretation>).map((role) => {
            const meta = DIE_ROLE_META[role];
            const value = currentRead.interpretation[role];
            const numericValue = getNumericForRole(currentRead, role);
            const isSelected = activeDie === role;

            return (
              <div
                key={role}
                onClick={() => setActiveDie(role)}
                className={`cursor-pointer text-center w-28 p-3 rounded-2xl transition-all duration-300 flex flex-col items-center justify-between ${
                  isSelected
                    ? 'scale-105 bg-[var(--deep)] shadow-2xl border-2 border-[var(--gold)]'
                    : 'hover:scale-102 opacity-90 border border-[var(--line)] bg-[var(--panel)]'
                } ${isRolling ? 'animate-pulse' : ''}`}
              >
                <span className="font-mono text-[10px] uppercase tracking-widest text-[var(--spark)] block mb-1">
                  {meta.category} ({meta.poly})
                </span>

                <div className="h-16 flex items-center justify-center my-1 relative">
                  <img
                    src={meta.icon}
                    alt={meta.poly}
                    className="h-14 w-auto object-contain filter drop-shadow-[0_4px_12px_rgba(255,255,255,0.35)]"
                  />
                  <span className="absolute inset-0 flex items-center justify-center font-cinzel text-lg font-black text-white drop-shadow-[0_1px_5px_rgba(255,255,255,0.6)]">
                    {numericValue}
                  </span>
                </div>

                <span className="font-cinzel text-sm font-black text-white drop-shadow-[0_1px_4px_rgba(255,255,255,0.7)] mt-1 truncate w-full">
                  {value}
                </span>

                <span className="font-mono text-[10px] text-[var(--parchment)] opacity-75 block mt-1">
                  {meta.discovery}
                </span>
              </div>
            );
          })}
        </div>

        <div className="pt-2">
          <button
            onClick={handleRollAll}
            disabled={isRolling}
            className={`btn-spark ${isRolling ? 'opacity-50 animate-pulse' : ''}`}
          >
            <RefreshCw className={isRolling ? 'animate-spin' : ''} size={18} />
            {isRolling ? 'Casting STL Dice...' : 'Roll All 7 STL 3D Dice'}
          </button>
        </div>

        <div className="p-4 rounded-xl bg-[var(--deep)]/90 border border-[var(--line)] max-w-xl mx-auto flex items-center justify-between text-left text-xs font-mono text-[var(--parchment)] mt-6">
          <div className="flex items-center gap-3">
            <img src={DIE_ROLE_META[activeDie].icon} alt={activeDie} className="h-10 w-auto object-contain" />
            <div>
              <span className="text-[var(--spark)] font-bold">{DIE_ROLE_META[activeDie].category} ({DIE_ROLE_META[activeDie].poly})</span> →{' '}
              <span className="font-cinzel text-base text-white font-black">{currentRead.interpretation[activeDie]}</span>
              <div className="text-[10px] opacity-75 text-[var(--parchment)] italic">{DIE_ROLE_META[activeDie].discovery}</div>
            </div>
          </div>
          <span className="text-[11px] opacity-75 flex items-center gap-1 text-white font-bold">
            <Sparkles size={12} className="text-white" /> Narratively Resonant
          </span>
        </div>
      </div>

      {showDestinyChart && (
        <div className="mythic-card p-6 space-y-4">
          <div className="flex justify-between items-center border-b border-[var(--line)] pb-3">
            <span className="eyebrow flex items-center gap-1.5">
              <Layers size={14} /> Official Reference Chart
            </span>
            <h3 className="text-xl font-bold font-cinzel text-[var(--gold)]">The 7 Dice of Destiny Reference</h3>
          </div>

          <div className="artifact-frame overflow-hidden">
            <img
              src="/art/dice-destiny-chart.png"
              alt="The 7 Dice of Destiny Chart"
              className="w-full h-auto object-contain"
            />
          </div>
        </div>
      )}
    </div>
  );
};
