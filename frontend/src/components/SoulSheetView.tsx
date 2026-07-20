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
        <div className="p-5 rounded-2xl bg-red-950/90 border-2 border-red-500/80 flex items-center gap-4 text-red-200 shadow-2xl animate-pulse">
          <AlertTriangle className="text-red-400 shrink-0" size={28} />
          <div>
            <div className="font-extrabold font-cinzel text-red-400 text-lg">CRITICAL SOUL FRACTURE WARNING (6/6 Strain)</div>
            <div className="text-xs text-red-300">
              The Soul is overreached. Convert a Bond into a Scar, sacrifice a Relic stage, or trigger a Fracture beat immediately!
            </div>
          </div>
        </div>
      )}

      {/* Header & Identity */}
      <div className="mythic-card p-6 md:p-8 space-y-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-amber-500/20 pb-6">
          <div>
            <span className="text-xs uppercase tracking-widest text-gold-glow font-bold flex items-center gap-1.5">
              <Shield size={16} /> Sacred Chronicle Character Record
            </span>
            <h2 className="text-3xl md:text-4xl font-black font-cinzel text-gold-gradient mt-1">{sheet.name}</h2>
            <p className="text-sm text-slate-300 mt-1">
              <span className="text-cyan-400 font-bold">{sheet.calling}</span> • Origin: {sheet.origin}
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <span className="mythic-pill text-amber-300 border-amber-500/40">
              Desire: {sheet.desire}
            </span>
            <span className="mythic-pill text-rose-300 border-rose-500/40">
              Fear: {sheet.fear}
            </span>
          </div>
        </div>

        {/* Core Resource Counters */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Resonance */}
          <div className="p-5 rounded-2xl bg-slate-950/90 border border-amber-500/40 flex flex-col justify-between shadow-xl">
            <div className="flex justify-between items-center mb-3">
              <span className="text-xs uppercase font-bold text-amber-400 flex items-center gap-1.5">
                <Sparkles size={16} /> Resonance
              </span>
              <span className="text-base font-black text-amber-300 font-cinzel">{sheet.resources.resonance} / 6</span>
            </div>
            <p className="text-xs text-slate-400 mb-4">Mythic alignment. Spend to tune reads, awaken relics, or reroll.</p>
            <div className="flex justify-between items-center">
              <div className="flex gap-1.5">
                {[...Array(6)].map((_, i) => (
                  <div
                    key={i}
                    className={`w-4 h-4 rounded-full border border-amber-500/60 ${
                      i < sheet.resources.resonance ? 'bg-amber-400 shadow-glow-gold' : 'bg-slate-900'
                    }`}
                  />
                ))}
              </div>
              <div className="flex gap-1">
                <button
                  onClick={() => adjustResource('resonance', -1)}
                  className="w-8 h-8 rounded-lg bg-slate-900 border border-amber-500/30 text-amber-400 hover:bg-amber-950 font-bold"
                >
                  -
                </button>
                <button
                  onClick={() => adjustResource('resonance', 1)}
                  className="w-8 h-8 rounded-lg bg-slate-900 border border-amber-500/30 text-amber-400 hover:bg-amber-950 font-bold"
                >
                  +
                </button>
              </div>
            </div>
          </div>

          {/* Strain */}
          <div className="p-5 rounded-2xl bg-slate-950/90 border border-rose-500/40 flex flex-col justify-between shadow-xl">
            <div className="flex justify-between items-center mb-3">
              <span className="text-xs uppercase font-bold text-rose-400 flex items-center gap-1.5">
                <Flame size={16} /> Strain
              </span>
              <span className="text-base font-black text-rose-300 font-cinzel">{sheet.resources.strain} / 6</span>
            </div>
            <p className="text-xs text-slate-400 mb-4">Overreach load. Accepted to force outcomes or resist fear.</p>
            <div className="flex justify-between items-center">
              <div className="flex gap-1.5">
                {[...Array(6)].map((_, i) => (
                  <div
                    key={i}
                    className={`w-4 h-4 rounded-full border border-rose-500/60 ${
                      i < sheet.resources.strain ? 'bg-rose-500 shadow-md' : 'bg-slate-900'
                    }`}
                  />
                ))}
              </div>
              <div className="flex gap-1">
                <button
                  onClick={() => adjustResource('strain', -1)}
                  className="w-8 h-8 rounded-lg bg-slate-900 border border-rose-500/30 text-rose-400 hover:bg-rose-950 font-bold"
                >
                  -
                </button>
                <button
                  onClick={() => adjustResource('strain', 1)}
                  className="w-8 h-8 rounded-lg bg-slate-900 border border-rose-500/30 text-rose-400 hover:bg-rose-950 font-bold"
                >
                  +
                </button>
              </div>
            </div>
          </div>

          {/* Thread */}
          <div className="p-5 rounded-2xl bg-slate-950/90 border border-pink-500/40 flex flex-col justify-between shadow-xl">
            <div className="flex justify-between items-center mb-3">
              <span className="text-xs uppercase font-bold text-pink-400 flex items-center gap-1.5">
                <Bookmark size={16} /> Threads
              </span>
              <span className="text-base font-black text-pink-300 font-cinzel">{sheet.resources.thread_count} / 5</span>
            </div>
            <p className="text-xs text-slate-400 mb-4">Persistent continuity tokens used to write facts & summon callbacks.</p>
            <div className="flex justify-between items-center">
              <div className="flex gap-1.5">
                {[...Array(5)].map((_, i) => (
                  <div
                    key={i}
                    className={`w-4 h-4 rounded-full border border-pink-500/60 ${
                      i < sheet.resources.thread_count ? 'bg-pink-400 shadow-md' : 'bg-slate-900'
                    }`}
                  />
                ))}
              </div>
              <div className="flex gap-1">
                <button
                  onClick={() => adjustResource('thread_count', -1)}
                  className="w-8 h-8 rounded-lg bg-slate-900 border border-pink-500/30 text-pink-400 hover:bg-pink-950 font-bold"
                >
                  -
                </button>
                <button
                  onClick={() => adjustResource('thread_count', 1)}
                  className="w-8 h-8 rounded-lg bg-slate-900 border border-pink-500/30 text-pink-400 hover:bg-pink-950 font-bold"
                >
                  +
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Relics & Evolving Gear with Product Image Header */}
      <div className="mythic-card p-6 md:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h3 className="text-2xl font-bold font-cinzel text-slate-100 flex items-center gap-2">
            <Package size={22} className="text-cyan-400" /> Relics That Evolve
          </h3>
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <input
              type="text"
              placeholder="New Relic name..."
              value={newRelicName}
              onChange={(e) => setNewRelicName(e.target.value)}
              className="bg-slate-950 border border-slate-700 rounded-xl px-4 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 flex-1 sm:w-48"
            />
            <button onClick={handleAddRelic} className="btn-purple py-2 px-4 text-xs shrink-0">
              <PlusCircle size={14} /> Add Relic
            </button>
          </div>
        </div>

        {/* Relic Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {sheet.relics.map((relic) => (
            <div key={relic.id} className="p-5 rounded-2xl bg-slate-950/90 border border-cyan-500/30 space-y-2">
              <div className="flex justify-between items-center">
                <span className="font-bold text-slate-100 font-cinzel text-lg">{relic.name}</span>
                <span className="mythic-pill text-cyan-300 border-cyan-500/40">
                  {relic.stage}
                </span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">{relic.effect}</p>
              <div className="text-xs text-rose-400 italic pt-1 border-t border-slate-900">
                Overdraw Consequence: {relic.overdraw_consequence}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
