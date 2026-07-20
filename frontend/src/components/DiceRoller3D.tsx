import React, { useRef, useState, useEffect } from 'react';
import type { CanonicalDiceRead, DiceInterpretation } from '../types';
import { apiClient } from '../lib/api';
import { RefreshCw, Eye, BookOpen, Layers, Box, Sliders, Palette, EyeOff } from 'lucide-react';
import * as THREE from 'three';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';

interface DiceRoller3DProps {
  currentRead: CanonicalDiceRead;
  onRollComplete: (newRead: CanonicalDiceRead) => void;
  isRolling: boolean;
  setIsRolling: (rolling: boolean) => void;
}

const PRESET_COLORS = [
  { name: 'Sapphire', hex: '#1e5285', emissive: '#0d2d4d' },
  { name: 'Ruby', hex: '#991b1b', emissive: '#450a0a' },
  { name: 'Amethyst', hex: '#6b21a8', emissive: '#3b0764' },
  { name: 'Emerald', hex: '#065f46', emissive: '#022c22' },
  { name: 'Amber', hex: '#b45309', emissive: '#451a03' },
  { name: 'Celestial Cyan', hex: '#0284c7', emissive: '#0c4a6e' },
  { name: 'Obsidian', hex: '#12121c', emissive: '#05050a' }
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

export const DiceRoller3D: React.FC<DiceRoller3DProps> = ({
  currentRead,
  onRollComplete,
  isRolling,
  setIsRolling
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [activeDie, setActiveDie] = useState<keyof DiceInterpretation>('spark');
  const [showDestinyChart, setShowDestinyChart] = useState(false);
  const [stlLoadedCount, setStlLoadedCount] = useState(0);

  // Transparent Mode & Custom Color Chooser State
  const [isTransparentMode, setIsTransparentMode] = useState(true);
  const [customHex, setCustomHex] = useState('#1e5285');
  const [customEmissive, setCustomEmissive] = useState('#0d2d4d');
  const [opacityLevel, setOpacityLevel] = useState(0.60);
  const [showColorControls, setShowColorControls] = useState(false);

  const handleRollAll = async () => {
    if (isRolling) return;
    setIsRolling(true);

    try {
      const data = await apiClient.rollDice();

      setTimeout(() => {
        onRollComplete(data);
        setIsRolling(false);
      }, 1100);
    } catch {
      setTimeout(() => {
        onRollComplete(generateFallbackRoll());
        setIsRolling(false);
      }, 1100);
    }
  };

  const generateFallbackRoll = (): CanonicalDiceRead => {
    const sparks = ["Heart", "Mind", "Shadow", "Wild", "Wound", "Wonder"];
    const domains = ["Self", "Ally", "Foe", "Place", "Relic", "Omen"];
    const pressures = ["Time", "Fear", "Debt", "Exposure", "Corruption", "Scarcity"];
    const aims = ["Seek", "Protect", "Bind", "Break", "Reveal", "Transform"];
    const approaches = ["Edge", "Grace", "Guile", "Lore", "Empathy", "Craft"];
    const verdicts = ["Ascend", "Scar", "Stall", "Twist", "Reveal", "Collapse"];
    const threads = ["Bond", "Memory", "Mark", "Prophecy"];

    const pick = (arr: string[]) => arr[Math.floor(Math.random() * arr.length)];
    const interpretation = {
      spark: pick(sparks), domain: pick(domains), pressure: pick(pressures), aim: pick(aims),
      approach: pick(approaches), verdict: pick(verdicts), thread: pick(threads)
    };
    return {
      raw: { d20: Math.ceil(Math.random() * 20), d12: Math.ceil(Math.random() * 12), d10: Math.ceil(Math.random() * 10), percentile: Math.ceil(Math.random() * 100), d8: Math.ceil(Math.random() * 8), d6: Math.ceil(Math.random() * 6), d4: Math.ceil(Math.random() * 4) },
      grammar_version: '1.0.0',
      interpretation,
      grammar_sentence: `Driven by [${interpretation.spark}], the Soul attempts to [${interpretation.aim}] upon [${interpretation.domain}] using [${interpretation.approach}] against the pressure of [${interpretation.pressure}].`
    };
  };

  // Helper to create STATIC, camera-facing floating label sprite for underneath dice
  const createStaticFloatingLabelSprite = (category: string, poly: string, rolledValue: string, discovery: string) => {
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 320;
    const ctx = canvas.getContext('2d');
    if (!ctx) return new THREE.CanvasTexture(canvas);

    // Dark glass backing badge for high contrast
    ctx.fillStyle = 'rgba(7, 10, 18, 0.75)';
    ctx.strokeStyle = 'rgba(203, 167, 102, 0.4)';
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.roundRect(16, 16, 480, 288, 24);
    ctx.fill();
    ctx.stroke();

    // Category title (Cyan)
    ctx.font = 'bold 36px font-mono, monospace';
    ctx.fillStyle = '#6FD3F2';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText(`${category} (${poly})`, 256, 40);

    // Embossed Pure White Rolled Value (WHITE)
    ctx.shadowColor = '#ffffff';
    ctx.shadowBlur = 18;
    ctx.fillStyle = '#ffffff';
    ctx.font = 'black bold 64px "Cinzel", serif';
    ctx.fillText(rolledValue, 256, 105);

    // Discovery description (Parchment italic)
    ctx.shadowBlur = 0;
    ctx.font = 'italic 32px "EB Garamond", serif';
    ctx.fillStyle = '#EEE6D2';
    ctx.fillText(discovery, 256, 215);

    const texture = new THREE.CanvasTexture(canvas);
    texture.needsUpdate = true;
    return texture;
  };

  // Three.js STL Mesh Loader Canvas Engine
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(canvas.clientWidth, canvas.clientHeight, false);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(38, canvas.clientWidth / canvas.clientHeight, 0.1, 100);
    camera.position.set(0, 0.3, 10);

    // Multi-angle Studio Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.5);
    scene.add(ambientLight);

    const frontLight = new THREE.DirectionalLight(0xffffff, 2.8);
    frontLight.position.set(2, 4, 8);
    scene.add(frontLight);

    const cyanRim = new THREE.PointLight(0x6FD3F2, 3.5, 40);
    cyanRim.position.set(-6, 5, 5);
    scene.add(cyanRim);

    const goldRim = new THREE.PointLight(0xF5D77F, 3.0, 40);
    goldRim.position.set(6, -4, 5);
    scene.add(goldRim);

    const targetOpacity = isTransparentMode ? opacityLevel : 0.96;

    const diceMaterial = new THREE.MeshPhongMaterial({
      color: new THREE.Color(customHex),
      emissive: new THREE.Color(customEmissive),
      specular: new THREE.Color('#ffffff'),
      shininess: 95,
      transparent: true,
      opacity: targetOpacity,
      flatShading: true
    });

    const edgeMaterial = new THREE.LineBasicMaterial({
      color: new THREE.Color('#ffffff'),
      transparent: true,
      opacity: 0.95,
      linewidth: 2
    });

    const stlLoader = new STLLoader();
    const diceGroup = new THREE.Group();
    const meshList: THREE.Mesh[] = [];
    const staticLabelSprites: THREE.Sprite[] = [];

    const spacing = 2.05;
    const startX = -spacing * 3;

    const dieRoles = Object.keys(DIE_ROLE_META) as Array<keyof DiceInterpretation>;
    let loadedCounter = 0;

    dieRoles.forEach((role, idx) => {
      const meta = DIE_ROLE_META[role];
      const actualRolledValue = currentRead.interpretation[role];
      const posX = startX + idx * spacing;

      stlLoader.load(
        meta.stlPath,
        (geometry) => {
          geometry.center();
          geometry.computeVertexNormals();

          geometry.computeBoundingSphere();
          const radius = geometry.boundingSphere?.radius || 1;
          const targetScale = 0.85 / radius;
          geometry.scale(targetScale, targetScale, targetScale);

          const mesh = new THREE.Mesh(geometry, diceMaterial.clone());
          const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geometry, 15), edgeMaterial);
          mesh.add(edges);
          mesh.position.set(posX, 0.7, 0); // Position die slightly higher

          diceGroup.add(mesh);
          meshList[idx] = mesh;

          // Create STATIC Camera-Facing Floating Label Sprite positioned STATICALLY under each die!
          const labelTex = createStaticFloatingLabelSprite(meta.category, meta.poly, actualRolledValue, meta.discovery);
          const spriteMat = new THREE.SpriteMaterial({ map: labelTex, transparent: true });
          const labelSprite = new THREE.Sprite(spriteMat);
          labelSprite.scale.set(1.9, 1.2, 1);
          labelSprite.position.set(posX, -1.35, 0); // Static position underneath the die

          scene.add(labelSprite);
          staticLabelSprites[idx] = labelSprite;

          loadedCounter++;
          setStlLoadedCount(loadedCounter);
        },
        undefined,
        () => {
          const fallbackGeo = new THREE.IcosahedronGeometry(0.85);
          const mesh = new THREE.Mesh(fallbackGeo, diceMaterial.clone());
          mesh.position.set(posX, 0.7, 0);
          diceGroup.add(mesh);
          meshList[idx] = mesh;
        }
      );
    });

    scene.add(diceGroup);

    let animId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      const elapsedTime = clock.getElapsedTime();

      meshList.forEach((mesh, idx) => {
        if (!mesh) return;
        mesh.rotation.x = elapsedTime * (0.35 + idx * 0.04);
        mesh.rotation.y = elapsedTime * (0.45 + idx * 0.04);
        mesh.position.y = 0.7 + Math.sin(elapsedTime * 1.5 + idx) * 0.12; // Floating 3D mesh
      });

      // Keep static label sprites floating subtly without rotating!
      staticLabelSprites.forEach((sprite, idx) => {
        if (!sprite) return;
        sprite.position.y = -1.35 + Math.sin(elapsedTime * 1.5 + idx) * 0.04;
      });

      renderer.render(scene, camera);
      animId = requestAnimationFrame(animate);
    };

    animate();

    const handleResize = () => {
      if (!canvas) return;
      camera.aspect = canvas.clientWidth / canvas.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(canvas.clientWidth, canvas.clientHeight, false);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
    };
  }, [customHex, customEmissive, isTransparentMode, opacityLevel, currentRead]);

  return (
    <div className="space-y-8">
      {/* Official Spinning Portal Hero Banner */}
      <div className="relative rounded-3xl overflow-hidden artifact-frame border border-[var(--line)] bg-[#05040a] flex flex-col items-center justify-center p-4 md:p-6">
        <div className="w-full max-w-4xl max-h-72 md:max-h-80 overflow-hidden flex items-center justify-center">
          <img
            src="/art/soulsmith.png"
            alt="SoulSmith Mythic Key Art"
            className="w-full h-full object-contain object-center max-h-72 md:max-h-80"
          />
        </div>

        <div className="w-full pt-4 flex flex-col justify-end text-center items-center">
          {/* Spinning Portal Ring */}
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

      {/* Real Translucent Sapphire 3D STL Canvas Tray with Static Floating Descriptions */}
      <div className="mythic-card p-6 md:p-8 relative overflow-hidden text-center">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4 border-b border-[var(--line)] pb-4">
          <div className="text-left">
            <p className="eyebrow mb-0.5 flex items-center gap-1.5">
              <Box size={14} className="text-[var(--spark)]" /> Static Camera-Facing Descriptions Underneath 3D Dice
            </p>
            <h3 className="text-3xl font-black font-cinzel text-[var(--gold)]">
              Seven Dice of Destiny Sanctuary
            </h3>
          </div>

          {/* Controls Bar */}
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
              {isTransparentMode ? 'Transparent Glass: ON' : 'Transparent Glass: OFF'}
            </button>

            <button
              onClick={() => setShowColorControls(!showColorControls)}
              className="btn-glass text-xs flex items-center gap-1.5"
            >
              <Palette size={14} className="text-[var(--gold)]" />
              Custom Color Chooser
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

        {/* Color Palette Chooser Drawer */}
        {showColorControls && (
          <div className="p-5 rounded-2xl bg-[var(--deep)] border border-[var(--line)] space-y-4 mb-5 text-left">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-[var(--line)] pb-3">
              <div>
                <span className="text-xs font-mono uppercase text-[var(--gold)] font-bold flex items-center gap-1.5">
                  <Palette size={14} /> Translucent Resin Color & Glass Optics
                </span>
                <p className="text-xs font-body text-[var(--parchment)] opacity-75">
                  Select a preset gem color or pick a custom hex color and fine-tune glass transparency.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-[var(--parchment)] opacity-80">Custom Color:</span>
                <input
                  type="color"
                  value={customHex}
                  onChange={(e) => {
                    setCustomHex(e.target.value);
                    setCustomEmissive(e.target.value);
                  }}
                  className="w-9 h-9 rounded-lg bg-transparent border border-[var(--line)] cursor-pointer"
                />
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-mono text-[var(--parchment)] opacity-75 mr-2">Presets:</span>
              {PRESET_COLORS.map((preset) => (
                <button
                  key={preset.name}
                  onClick={() => {
                    setCustomHex(preset.hex);
                    setCustomEmissive(preset.emissive);
                  }}
                  className="px-3 py-1.5 rounded-xl text-xs font-mono flex items-center gap-2 border border-[var(--line)] bg-[var(--void)] hover:border-[var(--gold)] transition"
                >
                  <span className="w-3.5 h-3.5 rounded-full border border-white/40" style={{ backgroundColor: preset.hex }} />
                  <span>{preset.name}</span>
                </button>
              ))}
            </div>

            {isTransparentMode && (
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pt-2 border-t border-[var(--line)]">
                <div className="flex items-center gap-2">
                  <Sliders size={14} className="text-[var(--spark)]" />
                  <span className="text-xs font-mono text-[var(--parchment)]">Glass Transparency Opacity:</span>
                </div>
                <div className="flex items-center gap-3 w-full sm:w-64">
                  <input
                    type="range"
                    min={0.15}
                    max={0.95}
                    step={0.05}
                    value={opacityLevel}
                    onChange={(e) => setOpacityLevel(parseFloat(e.target.value))}
                    className="w-full accent-[var(--spark)] cursor-pointer"
                  />
                  <span className="text-xs font-mono text-[var(--spark)] font-bold w-12 text-right">
                    {(opacityLevel * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Status */}
        <div className="flex justify-between items-center text-xs font-mono mb-3 text-left">
          <span className="text-[var(--spark)]">
            ✦ 3D STL Dice Models: {stlLoadedCount} / 7 (Static Descriptions Floating Underneath)
          </span>
          <span className="mythic-pill border-[var(--gold-dim)] text-[var(--gold)]">
            Static Under-Dice Labels
          </span>
        </div>

        {/* Real Translucent 3D WebGL Canvas with Static Floating Underneath Descriptions */}
        <div className="w-full h-72 md:h-80 relative rounded-2xl overflow-hidden bg-gradient-to-b from-[#070a14] via-[#091322] to-[#070a14] border border-[var(--line)] mb-6 shadow-2xl">
          <canvas ref={canvasRef} className="w-full h-full block" />
        </div>

        {/* 7 Rolled Dice Outcome Cards displaying White Embossed Numbers */}
        <div className="flex flex-wrap justify-center items-center gap-3 md:gap-4 mb-6">
          {(Object.keys(DIE_ROLE_META) as Array<keyof DiceInterpretation>).map((role) => {
            const meta = DIE_ROLE_META[role];
            const value = currentRead.interpretation[role];
            const numericValue = ({ spark: currentRead.raw.d20, domain: currentRead.raw.d12, pressure: currentRead.raw.d10, aim: currentRead.raw.percentile, approach: currentRead.raw.d8, verdict: currentRead.raw.d6, thread: currentRead.raw.d4 } as const)[role];
            const isSelected = activeDie === role;

            return (
              <div
                key={role}
                onClick={() => setActiveDie(role)}
                className={`cursor-pointer text-center w-28 p-3 rounded-2xl transition-all duration-300 flex flex-col items-center justify-between ${
                  isSelected
                    ? 'scale-105 bg-[var(--deep)] shadow-2xl border-2 border-[var(--gold)]'
                    : 'hover:scale-102 opacity-90 border border-[var(--line)] bg-[var(--panel)]'
                } ${isRolling ? 'animate-bounce' : ''}`}
              >
                <span className="font-mono text-[10px] uppercase tracking-widest text-[var(--spark)] block mb-1">
                  {meta.category} ({meta.poly})
                </span>

                <div className="h-16 flex items-center justify-center my-1 relative">
                  <img
                    src={meta.icon}
                    alt={meta.poly}
                    className="h-14 w-auto object-contain filter drop-shadow-[0_4px_12px_rgba(255,255,255,0.5)]"
                  />
                  <span className="absolute inset-0 flex items-center justify-center font-cinzel text-lg font-black text-white drop-shadow-[0_2px_8px_rgba(255,255,255,0.95)]">
                    {numericValue}
                  </span>
                </div>

                <span className="font-cinzel text-sm font-black text-white drop-shadow-[0_1px_4px_rgba(255,255,255,0.8)] mt-1 truncate w-full">
                  {value}
                </span>

                <span className="font-mono text-[10px] text-[var(--parchment)] opacity-75 block mt-1">
                  {meta.discovery}
                </span>
              </div>
            );
          })}
        </div>

        {/* Roll Button */}
        <div className="pt-2">
          <button
            onClick={handleRollAll}
            disabled={isRolling}
            className={`btn-spark ${isRolling ? 'opacity-50 animate-pulse' : ''}`}
          >
            <RefreshCw className={isRolling ? 'animate-spin' : ''} size={18} />
            {isRolling ? 'Casting 3D STL Dice...' : 'Roll All 7 STL 3D Dice'}
          </button>
        </div>

        {/* Selected Die Inspector */}
        <div className="p-4 rounded-xl bg-[var(--deep)]/90 border border-[var(--line)] max-w-xl mx-auto flex items-center justify-between text-left text-xs font-mono text-[var(--parchment)] mt-6">
          <div className="flex items-center gap-3">
            <img src={DIE_ROLE_META[activeDie].icon} alt={activeDie} className="h-10 w-auto object-contain" />
            <div>
              <span className="text-[var(--spark)] font-bold">{DIE_ROLE_META[activeDie].category} ({DIE_ROLE_META[activeDie].poly})</span> →{' '}
              <span className="font-cinzel text-base text-white font-black drop-shadow-[0_1px_4px_rgba(255,255,255,0.9)]">{currentRead.interpretation[activeDie]}</span>
              <div className="text-[10px] opacity-75 text-[var(--parchment)] italic">{DIE_ROLE_META[activeDie].discovery}</div>
            </div>
          </div>
          <span className="text-[11px] opacity-75 flex items-center gap-1 text-white font-bold">
            <Eye size={12} className="text-white" /> Static Underneath Description
          </span>
        </div>
      </div>

      {/* 7 Dice of Destiny Reference Chart from dice.png */}
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
