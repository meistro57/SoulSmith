import React, { useState } from 'react';
import type { SoulSheet, Relic } from '../types';
import { Shield, Sparkles, Flame, Bookmark, Package, AlertTriangle, PlusCircle } from 'lucide-react';

interface SoulSheetViewProps {
  sheet: SoulSheet;
  onUpdateSheet: (updated: SoulSheet) => void;
}

export const SoulSheetView: React.FC<SoulSheetViewProps> = ({ sheet, onUpdateSheet }) => {
  const [newRelicName, setNewRelicName] = useState('');

  const adjustResource = (key: 'resonance' | 'strain' | 'thread_count', delta: number) => {
    const caps = { resonance: 6, strain: 6, thread_count: 5 };
    const current = sheet.resources[key];
    const updatedVal = Math.max(0, Math.min(caps[key], current + delta));

    onUpdateSheet({
      ...sheet,
      resources: {
        ...sheet.resources,
        [key]: updatedVal
      }
    });
  };

  const handleAddRelic = () => {
    if (!newRelicName.trim()) return;
    const created: Relic = {
      id: Date.now().toString(),
      name: newRelicName.trim(),
      stage: 'Dormant',
      effect: 'Grants passive story alignment reroll on favored Domains.',
      overdraw_consequence: 'Adds +1 automatic Strain upon overdraw.'
    };
    onUpdateSheet({
      ...sheet,
      relics: [...sheet.relics, created]
    });
    setNewRelicName('');
  };

  return (
    <div className="space-y-6">
      {/* Strain Max Fracture Banner */}
      {sheet.resources.strain >= 6 && (
        <div className="p-4 rounded-xl bg-red-950/80 border border-red-500/50 flex items-center gap-3 text-red-200 animate-pulse">
          <AlertTriangle className="text-red-400 shrink-0" size={24} />
          <div>
            <div className="font-bold font-cinzel text-red-400">CRITICAL SOUL FRACTURE WARNING (6/6 Strain)</div>
            <div className="text-xs text-red-300">
              The Soul is overreached. You must immediately convert a Bond into a Scar, sacrifice a Relic stage, or trigger a Fracture beat!
            </div>
          </div>
        </div>
      )}

      {/* Header & Identity */}
      <div className="glass-panel p-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
          <div>
            <span className="text-xs uppercase tracking-widest text-gold-glow font-semibold flex items-center gap-1">
              <Shield size={14} /> Sacred Chronicle Record
            </span>
            <h2 className="text-3xl font-bold font-cinzel text-slate-100">{sheet.name}</h2>
            <p className="text-sm text-slate-400">
              <span className="text-cyan-400 font-semibold">{sheet.calling}</span> • Origin: {sheet.origin}
            </p>
          </div>

          <div className="flex gap-2">
            <span className="glass-pill text-xs text-amber-300 border-amber-500/30">
              Desire: {sheet.desire}
            </span>
            <span className="glass-pill text-xs text-rose-300 border-rose-500/30">
              Fear: {sheet.fear}
            </span>
          </div>
        </div>

        {/* Core Resource Counters */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Resonance */}
          <div className="p-4 rounded-xl bg-slate-900/90 border border-amber-500/30 flex flex-col justify-between">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs uppercase font-bold text-amber-400 flex items-center gap-1">
                <Sparkles size={14} /> Resonance
              </span>
              <span className="text-sm font-bold text-amber-300 font-cinzel">{sheet.resources.resonance} / 6</span>
            </div>
            <p className="text-xs text-slate-400 mb-3">Mythic alignment. Spend to tune reads, awaken relics, or reroll.</p>
            <div className="flex justify-between items-center">
              <div className="flex gap-1">
                {[...Array(6)].map((_, i) => (
                  <div
                    key={i}
                    className={`w-4 h-4 rounded-full border border-amber-500/50 ${
                      i < sheet.resources.resonance ? 'bg-amber-400 shadow-glow-gold' : 'bg-slate-800'
                    }`}
                  />
                ))}
              </div>
              <div className="flex gap-1">
                <button
                  onClick={() => adjustResource('resonance', -1)}
                  className="w-7 h-7 rounded bg-slate-800 text-amber-400 hover:bg-slate-700 font-bold"
                >
                  -
                </button>
                <button
                  onClick={() => adjustResource('resonance', 1)}
                  className="w-7 h-7 rounded bg-slate-800 text-amber-400 hover:bg-slate-700 font-bold"
                >
                  +
                </button>
              </div>
            </div>
          </div>

          {/* Strain */}
          <div className="p-4 rounded-xl bg-slate-900/90 border border-red-500/30 flex flex-col justify-between">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs uppercase font-bold text-red-400 flex items-center gap-1">
                <Flame size={14} /> Strain
              </span>
              <span className="text-sm font-bold text-red-300 font-cinzel">{sheet.resources.strain} / 6</span>
            </div>
            <p className="text-xs text-slate-400 mb-3">Overreach load. Accepted to force outcomes or resist fear.</p>
            <div className="flex justify-between items-center">
              <div className="flex gap-1">
                {[...Array(6)].map((_, i) => (
                  <div
                    key={i}
                    className={`w-4 h-4 rounded-full border border-red-500/50 ${
                      i < sheet.resources.strain ? 'bg-red-500 shadow-md' : 'bg-slate-800'
                    }`}
                  />
                ))}
              </div>
              <div className="flex gap-1">
                <button
                  onClick={() => adjustResource('strain', -1)}
                  className="w-7 h-7 rounded bg-slate-800 text-red-400 hover:bg-slate-700 font-bold"
                >
                  -
                </button>
                <button
                  onClick={() => adjustResource('strain', 1)}
                  className="w-7 h-7 rounded bg-slate-800 text-red-400 hover:bg-slate-700 font-bold"
                >
                  +
                </button>
              </div>
            </div>
          </div>

          {/* Thread */}
          <div className="p-4 rounded-xl bg-slate-900/90 border border-pink-500/30 flex flex-col justify-between">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs uppercase font-bold text-pink-400 flex items-center gap-1">
                <Bookmark size={14} /> Threads
              </span>
              <span className="text-sm font-bold text-pink-300 font-cinzel">{sheet.resources.thread_count} / 5</span>
            </div>
            <p className="text-xs text-slate-400 mb-3">Persistent continuity tokens used to write facts & summon callbacks.</p>
            <div className="flex justify-between items-center">
              <div className="flex gap-1">
                {[...Array(5)].map((_, i) => (
                  <div
                    key={i}
                    className={`w-4 h-4 rounded-full border border-pink-500/50 ${
                      i < sheet.resources.thread_count ? 'bg-pink-400 shadow-md' : 'bg-slate-800'
                    }`}
                  />
                ))}
              </div>
              <div className="flex gap-1">
                <button
                  onClick={() => adjustResource('thread_count', -1)}
                  className="w-7 h-7 rounded bg-slate-800 text-pink-400 hover:bg-slate-700 font-bold"
                >
                  -
                </button>
                <button
                  onClick={() => adjustResource('thread_count', 1)}
                  className="w-7 h-7 rounded bg-slate-800 text-pink-400 hover:bg-slate-700 font-bold"
                >
                  +
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Relics & Evolving Gear */}
      <div className="glass-panel p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-bold font-cinzel text-slate-200 flex items-center gap-2">
            <Package size={20} className="text-cyan-400" /> Relics That Evolve
          </h3>
          <div className="flex items-center gap-2">
            <input
              type="text"
              placeholder="New Relic name..."
              value={newRelicName}
              onChange={(e) => setNewRelicName(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
            />
            <button onClick={handleAddRelic} className="btn-secondary py-1.5 px-3 text-xs">
              <PlusCircle size={14} /> Add Relic
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sheet.relics.map((relic) => (
            <div key={relic.id} className="p-4 rounded-xl bg-slate-900/80 border border-cyan-500/20">
              <div className="flex justify-between items-center mb-2">
                <span className="font-bold text-slate-200 font-cinzel">{relic.name}</span>
                <span className="glass-pill text-xs text-cyan-300 border-cyan-500/30">
                  {relic.stage}
                </span>
              </div>
              <p className="text-xs text-slate-400 mb-2">{relic.effect}</p>
              <div className="text-xs text-rose-400 italic">Overdraw: {relic.overdraw_consequence}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
