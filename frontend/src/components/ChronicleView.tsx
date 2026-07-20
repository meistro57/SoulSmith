import React, { useState } from 'react';
import type { ResolvedScene } from '../types';
import { BookMarked, Search, Globe, Database } from 'lucide-react';

interface ChronicleViewProps {
  history: ResolvedScene[];
  worldFacts: string[];
}

export const ChronicleView: React.FC<ChronicleViewProps> = ({ history, worldFacts }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterClass, setFilterClass] = useState<string>('all');

  const filteredHistory = history.filter((item) => {
    const matchesQuery =
      item.narration.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.narration.prose.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterClass === 'all' || item.outcome.outcome_class === filterClass;
    return matchesQuery && matchesFilter;
  });

  return (
    <div className="space-y-6">
      {/* World Facts / Canonical Source of Truth Header */}
      <div className="glass-panel p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <span className="text-xs uppercase tracking-widest text-cyan-400 font-semibold flex items-center gap-1">
              <Globe size={14} /> Living Mythology Source of Truth
            </span>
            <h2 className="text-2xl font-bold font-cinzel text-slate-100">World Chronicle & Immutable Facts</h2>
          </div>
          <span className="glass-pill text-xs text-purple-300 border-purple-500/30 flex items-center gap-1">
            <Database size={12} /> SQLite Chronicle Memory
          </span>
        </div>

        <div className="space-y-2 bg-slate-900/80 p-4 rounded-xl border border-slate-800">
          <div className="text-xs uppercase font-semibold text-slate-400 mb-1">Locked Canonical Facts:</div>
          {worldFacts.map((fact, idx) => (
            <div key={idx} className="text-xs text-slate-300 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
              <span>{fact}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Search & Filter bar */}
      <div className="glass-panel p-4 flex flex-col md:flex-row gap-3 justify-between items-center">
        <div className="relative w-full md:w-96">
          <Search size={16} className="absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Search semantic memory archive..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-xl pl-9 pr-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="flex gap-2 w-full md:w-auto overflow-x-auto">
          {['all', 'ascendancy', 'marked_success', 'revelatory_failure', 'collapse'].map((cls) => (
            <button
              key={cls}
              onClick={() => setFilterClass(cls)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase transition ${
                filterClass === cls
                  ? 'bg-purple-600 text-white shadow-glow-purple'
                  : 'bg-slate-900 text-slate-400 hover:bg-slate-800'
              }`}
            >
              {cls.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Chronicle Event Cards */}
      <div className="space-y-4">
        {filteredHistory.length === 0 ? (
          <div className="glass-panel p-8 text-center text-slate-400">
            <BookMarked size={32} className="mx-auto mb-2 opacity-50 text-cyan-400" />
            <p>No matching chronicle beats found in memory.</p>
          </div>
        ) : (
          filteredHistory.map((entry, idx) => (
            <div key={entry.event_id || idx} className="glass-panel p-6 space-y-3">
              <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-purple-400" />
                  <h3 className="text-lg font-bold font-cinzel text-slate-100">{entry.narration.title}</h3>
                </div>
                <span className="glass-pill text-xs uppercase text-slate-300 font-semibold">
                  {entry.outcome.outcome_title}
                </span>
              </div>

              <p className="text-sm text-slate-300 leading-relaxed italic">{entry.narration.prose}</p>

              {entry.dice_read && (
                <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-950 text-xs">
                  <span className="text-gold-glow">Spark: {entry.dice_read.interpretation.spark}</span>
                  <span className="text-slate-600">•</span>
                  <span className="text-cyan-glow">Domain: {entry.dice_read.interpretation.domain}</span>
                  <span className="text-slate-600">•</span>
                  <span className="text-purple-glow">Verdict: {entry.dice_read.interpretation.verdict}</span>
                  <span className="text-slate-600">•</span>
                  <span className="text-pink-400">Thread: {entry.dice_read.interpretation.thread}</span>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
