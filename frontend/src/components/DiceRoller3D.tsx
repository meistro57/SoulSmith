import React, { useRef, useState, useEffect } from 'react';
import type { DiceRollRead } from '../types';
import { Dices, Sparkles, RefreshCw, Eye } from 'lucide-react';

interface DiceRoller3DProps {
  currentRead: DiceRollRead;
  onRollComplete: (newRead: DiceRollRead) => void;
  isRolling: boolean;
  setIsRolling: (rolling: boolean) => void;
}

const DIE_COLOR_MAP: Record<keyof DiceRollRead, { label: string; poly: string; color: string; border: string; bg: string }> = {
  spark: { label: 'Spark (d20)', poly: '20-sided', color: '#f59e0b', border: 'rgba(245, 158, 11, 0.7)', bg: 'linear-gradient(135deg, rgba(245, 158, 11, 0.25) 0%, rgba(15, 13, 26, 0.9) 100%)' },
  domain: { label: 'Domain (d12)', poly: '12-sided', color: '#38bdf8', border: 'rgba(56, 189, 248, 0.7)', bg: 'linear-gradient(135deg, rgba(56, 189, 248, 0.25) 0%, rgba(15, 13, 26, 0.9) 100%)' },
  pressure: { label: 'Pressure (d10)', poly: '10-sided', color: '#f43f5e', border: 'rgba(244, 63, 94, 0.7)', bg: 'linear-gradient(135deg, rgba(244, 63, 94, 0.25) 0%, rgba(15, 13, 26, 0.9) 100%)' },
  aim: { label: 'Aim (d%)', poly: '100-percentile', color: '#c084fc', border: 'rgba(192, 132, 252, 0.7)', bg: 'linear-gradient(135deg, rgba(192, 132, 252, 0.25) 0%, rgba(15, 13, 26, 0.9) 100%)' },
  approach: { label: 'Approach (d8)', poly: '8-sided', color: '#0ea5e9', border: 'rgba(14, 165, 233, 0.7)', bg: 'linear-gradient(135deg, rgba(14, 165, 233, 0.25) 0%, rgba(15, 13, 26, 0.9) 100%)' },
  verdict: { label: 'Verdict (d6)', poly: '6-sided', color: '#10b981', border: 'rgba(16, 185, 129, 0.7)', bg: 'linear-gradient(135deg, rgba(16, 185, 129, 0.25) 0%, rgba(15, 13, 26, 0.9) 100%)' },
  thread: { label: 'Thread (d4)', poly: '4-sided', color: '#f472b6', border: 'rgba(244, 114, 182, 0.7)', bg: 'linear-gradient(135deg, rgba(244, 114, 182, 0.25) 0%, rgba(15, 13, 26, 0.9) 100%)' }
};

export const DiceRoller3D: React.FC<DiceRoller3DProps> = ({
  currentRead,
  onRollComplete,
  isRolling,
  setIsRolling
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [activeDie, setActiveDie] = useState<keyof DiceRollRead>('spark');

  const handleRollAll = async () => {
    if (isRolling) return;
    setIsRolling(true);

    try {
      const res = await fetch('http://localhost:8000/api/v1/dice/roll', { method: 'POST' });
      const data: DiceRollRead = res.ok ? await res.json() : generateFallbackRoll();

      setTimeout(() => {
        onRollComplete(data);
        setIsRolling(false);
      }, 1200);
    } catch {
      setTimeout(() => {
        onRollComplete(generateFallbackRoll());
        setIsRolling(false);
      }, 1200);
    }
  };

  const generateFallbackRoll = (): DiceRollRead => {
    const sparks = ["Heart", "Mind", "Shadow", "Wild", "Wound", "Wonder"];
    const domains = ["Self", "Ally", "Foe", "Place", "Relic", "Omen"];
    const pressures = ["Time", "Fear", "Debt", "Exposure", "Corruption", "Scarcity"];
    const aims = ["Seek", "Protect", "Bind", "Break", "Reveal", "Transform"];
    const approaches = ["Edge", "Grace", "Guile", "Lore", "Empathy", "Craft"];
    const verdicts = ["Ascend", "Scar", "Stall", "Twist", "Reveal", "Collapse"];
    const threads = ["Bond", "Memory", "Mark", "Debt", "Portal", "Prophecy"];

    const pick = (arr: string[]) => arr[Math.floor(Math.random() * arr.length)];
    return {
      spark: pick(sparks),
      domain: pick(domains),
      pressure: pick(pressures),
      aim: pick(aims),
      approach: pick(approaches),
      verdict: pick(verdicts),
      thread: pick(threads)
    };
  };

  // Cosmic Particle Canvas Orbit
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let particles: Array<{ x: number; y: number; vx: number; vy: number; color: string; radius: number }> = [];

    const colors = ['#f59e0b', '#38bdf8', '#c084fc', '#10b981', '#f472b6'];
    for (let i = 0; i < 45; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.9,
        vy: (Math.random() - 0.5) * 0.9,
        color: colors[Math.floor(Math.random() * colors.length)],
        radius: Math.random() * 2.5 + 1
      });
    }

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.globalAlpha = 0.5;
        ctx.shadowBlur = 10;
        ctx.shadowColor = p.color;
        ctx.fill();
      });

      animId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animId);
  }, []);

  return (
    <div className="space-y-6">
      {/* Immersive Key Artwork Banner Backdrop */}
      <div className="relative rounded-3xl overflow-hidden border border-amber-500/40 shadow-2xl group">
        <img
          src="/soulsmith-hero.png"
          alt="SoulSmith Mythic Hero"
          className="w-full h-72 md:h-80 object-cover object-center transition duration-700 group-hover:scale-105"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#05040a] via-[#05040a]/60 to-transparent p-6 md:p-8 flex flex-col justify-end">
          <div className="flex items-center gap-2 mb-2">
            <span className="mythic-pill">✦ Living Mythology Engine</span>
            <span className="glass-pill text-xs font-semibold text-cyan-300 border-cyan-500/30">
              7-Dice Grammar Core
            </span>
          </div>

          <h2 className="text-3xl md:text-5xl font-black font-cinzel text-gold-gradient tracking-wide mb-2">
            Sanctuary of the Seven Spark Dice
          </h2>
          <p className="text-sm text-slate-200 max-w-2xl font-light leading-relaxed">
            Cast the sacred polyhedral dice. Each die role defines a semantic vector in the mythic sentence grammar before prose is woven by the Soulkeeper.
          </p>
        </div>
      </div>

      {/* 3D Dice Tray & Canvas */}
      <div className="mythic-card p-6 md:p-8 relative overflow-hidden">
        <canvas
          ref={canvasRef}
          width={1000}
          height={220}
          className="absolute inset-0 pointer-events-none opacity-50"
        />

        <div className="relative z-10">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
            <div>
              <span className="text-xs uppercase tracking-widest text-gold-glow flex items-center gap-1.5 font-bold">
                <Sparkles size={16} /> Interactive 3D Dice Matrix
              </span>
              <h3 className="text-2xl font-bold text-slate-100 font-cinzel">Current Mythic Sentence Grammar</h3>
            </div>

            <button
              onClick={handleRollAll}
              disabled={isRolling}
              className={`btn-gold ${isRolling ? 'opacity-50 animate-pulse' : ''}`}
            >
              <RefreshCw className={isRolling ? 'animate-spin' : ''} size={18} />
              {isRolling ? 'Casting Seven Dice...' : 'Roll All Seven Dice'}
            </button>
          </div>

          {/* 7 Polyhedral Gemstone Dice Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3.5 mb-6">
            {(Object.keys(DIE_COLOR_MAP) as Array<keyof DiceRollRead>).map((role) => {
              const info = DIE_COLOR_MAP[role];
              const value = currentRead[role];
              const isSelected = activeDie === role;

              return (
                <div
                  key={role}
                  onClick={() => setActiveDie(role)}
                  className={`cursor-pointer p-4 rounded-2xl transition-all duration-300 transform flex flex-col justify-between ${
                    isSelected ? 'scale-105 shadow-2xl' : 'hover:scale-102 opacity-90'
                  } ${isRolling ? 'animate-bounce' : ''}`}
                  style={{
                    background: info.bg,
                    border: `2px solid ${isSelected ? info.color : info.border}`,
                    boxShadow: isSelected ? `0 0 25px ${info.border}` : '0 4px 20px rgba(0,0,0,0.6)'
                  }}
                >
                  <div className="flex justify-between items-center text-[11px] font-semibold mb-2" style={{ color: info.color }}>
                    <span>{info.poly}</span>
                    <Dices size={14} />
                  </div>
                  <div className="text-[11px] uppercase font-bold text-slate-300 mb-1">{role}</div>
                  <div className="text-xl font-black font-cinzel truncate tracking-wide" style={{ color: info.color, textShadow: `0 0 10px ${info.border}` }}>
                    {value}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Selected Die Detailed Inspector */}
          <div className="p-5 rounded-2xl bg-slate-950/90 border border-amber-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center font-black text-slate-950 font-cinzel text-lg shadow-lg"
                style={{ backgroundColor: DIE_COLOR_MAP[activeDie].color, boxHex: DIE_COLOR_MAP[activeDie].border } as any}
              >
                {activeDie.slice(0, 3).toUpperCase()}
              </div>
              <div>
                <div className="text-base font-bold text-slate-100">
                  {DIE_COLOR_MAP[activeDie].label} → <span className="font-cinzel text-lg" style={{ color: DIE_COLOR_MAP[activeDie].color }}>{currentRead[activeDie]}</span>
                </div>
                <div className="text-xs text-slate-400">
                  Active Vector Feeding Soulkeeper AI Pipeline • Click any die card to inspect face slot.
                </div>
              </div>
            </div>
            <span className="text-xs text-amber-300/80 flex items-center gap-1.5 glass-pill border-amber-500/30">
              <Eye size={14} /> Slot Inspection Active
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
