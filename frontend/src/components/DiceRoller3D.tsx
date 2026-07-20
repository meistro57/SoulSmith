import React, { useRef, useState, useEffect } from 'react';
import type { DiceRollRead } from '../types';
import { Dices, Sparkles, RefreshCw, Eye } from 'lucide-react';

interface DiceRoller3DProps {
  currentRead: DiceRollRead;
  onRollComplete: (newRead: DiceRollRead) => void;
  isRolling: boolean;
  setIsRolling: (rolling: boolean) => void;
}

const DIE_COLOR_MAP: Record<keyof DiceRollRead, { label: string; poly: string; color: string; border: string }> = {
  spark: { label: 'Spark (d20)', poly: '20-sided', color: '#d7aa55', border: 'rgba(215, 170, 85, 0.6)' },
  domain: { label: 'Domain (d12)', poly: '12-sided', color: '#46cbff', border: 'rgba(70, 203, 255, 0.6)' },
  pressure: { label: 'Pressure (d10)', poly: '10-sided', color: '#ff5566', border: 'rgba(255, 85, 102, 0.6)' },
  aim: { label: 'Aim (d%)', poly: '100-percentile', color: '#a855f7', border: 'rgba(168, 85, 247, 0.6)' },
  approach: { label: 'Approach (d8)', poly: '8-sided', color: '#38bdf8', border: 'rgba(56, 189, 248, 0.6)' },
  verdict: { label: 'Verdict (d6)', poly: '6-sided', color: '#34d399', border: 'rgba(52, 211, 153, 0.6)' },
  thread: { label: 'Thread (d4)', poly: '4-sided', color: '#f472b6', border: 'rgba(244, 114, 182, 0.6)' }
};

export const DiceRoller3D: React.FC<DiceRoller3DProps> = ({
  currentRead,
  onRollComplete,
  isRolling,
  setIsRolling
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [activeDie, setActiveDie] = useState<keyof DiceRollRead>('spark');

  // Trigger simulated 3D physics roll animation
  const handleRollAll = async () => {
    if (isRolling) return;
    setIsRolling(true);

    try {
      // Call backend API for legal grammar roll
      const res = await fetch('http://localhost:8000/api/v1/dice/roll', { method: 'POST' });
      const data: DiceRollRead = res.ok ? await res.json() : generateFallbackRoll();

      // Play 1.2s roll animation
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

  // Canvas particle animation
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let particles: Array<{ x: number; y: number; vx: number; vy: number; color: string; radius: number }> = [];

    const colors = ['#d7aa55', '#46cbff', '#a855f7', '#34d399', '#f472b6'];
    for (let i = 0; i < 35; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.8,
        vy: (Math.random() - 0.5) * 0.8,
        color: colors[Math.floor(Math.random() * colors.length)],
        radius: Math.random() * 2 + 1
      });
    }

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Render particle background
      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.globalAlpha = 0.4;
        ctx.fill();
      });

      animId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animId);
  }, []);

  return (
    <div className="glass-panel p-6 relative overflow-hidden">
      <canvas
        ref={canvasRef}
        width={800}
        height={180}
        className="absolute inset-0 pointer-events-none opacity-40"
      />

      <div className="relative z-10">
        <div className="flex justify-between items-center mb-6">
          <div>
            <span className="text-xs uppercase tracking-widest text-gold-glow flex items-center gap-1 font-semibold">
              <Sparkles size={14} /> Sacred Seven-Dice Sanctuary
            </span>
            <h2 className="text-2xl font-bold text-slate-100 font-cinzel">Cast the Mythic Spark</h2>
          </div>

          <button
            onClick={handleRollAll}
            disabled={isRolling}
            className={`btn-primary ${isRolling ? 'opacity-50 animate-pulse' : ''}`}
          >
            <RefreshCw className={isRolling ? 'animate-spin' : ''} size={18} />
            {isRolling ? 'Casting Seven Dice...' : 'Roll All Seven Dice'}
          </button>
        </div>

        {/* 7 Polyhedral Dice Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 mb-6">
          {(Object.keys(DIE_COLOR_MAP) as Array<keyof DiceRollRead>).map((role) => {
            const info = DIE_COLOR_MAP[role];
            const value = currentRead[role];
            const isSelected = activeDie === role;

            return (
              <div
                key={role}
                onClick={() => setActiveDie(role)}
                className={`cursor-pointer p-4 rounded-xl transition-all duration-300 transform ${
                  isSelected ? 'scale-105 shadow-lg' : 'hover:scale-102 opacity-90'
                } ${isRolling ? 'animate-bounce' : ''}`}
                style={{
                  background: 'rgba(15, 15, 26, 0.85)',
                  border: `2px solid ${isSelected ? info.color : info.border}`,
                  boxShadow: isSelected ? `0 0 20px ${info.border}` : 'none'
                }}
              >
                <div className="flex justify-between items-center text-xs opacity-75 mb-1" style={{ color: info.color }}>
                  <span>{info.poly}</span>
                  <Dices size={14} />
                </div>
                <div className="text-xs uppercase font-semibold text-slate-400 mb-2">{role}</div>
                <div className="text-lg font-bold font-cinzel truncate" style={{ color: info.color }}>
                  {value}
                </div>
              </div>
            );
          })}
        </div>

        {/* Selected Die Face Detail */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-lg flex items-center justify-center font-bold text-slate-950 font-cinzel"
              style={{ backgroundColor: DIE_COLOR_MAP[activeDie].color }}
            >
              {activeDie.slice(0, 3).toUpperCase()}
            </div>
            <div>
              <div className="text-sm font-semibold text-slate-200">
                {DIE_COLOR_MAP[activeDie].label} → <span style={{ color: DIE_COLOR_MAP[activeDie].color }}>{currentRead[activeDie]}</span>
              </div>
              <div className="text-xs text-slate-400">
                Grammar Function: Active narrative vector feeding the Soulkeeper AI Orchestration pipeline.
              </div>
            </div>
          </div>
          <span className="text-xs text-slate-500 flex items-center gap-1">
            <Eye size={12} /> Click any die to inspect slot
          </span>
        </div>
      </div>
    </div>
  );
};
