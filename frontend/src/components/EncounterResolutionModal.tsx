import React from 'react';
import type { ResolvedScene } from '../types';
import { ShieldCheck, CheckCircle2, Sparkles, BookOpen, X, Award } from 'lucide-react';

interface EncounterResolutionModalProps {
  scene: ResolvedScene;
  onClose: () => void;
}

export const EncounterResolutionModal: React.FC<EncounterResolutionModalProps> = ({ scene, onClose }) => {
  const { outcome, narration } = scene;

  const outcomeColors = {
    ascendancy: { bg: 'bg-emerald-950/90', border: 'border-emerald-500', text: 'text-emerald-400' },
    marked_success: { bg: 'bg-amber-950/90', border: 'border-amber-500', text: 'text-amber-400' },
    revelatory_failure: { bg: 'bg-purple-950/90', border: 'border-purple-500', text: 'text-purple-400' },
    collapse: { bg: 'bg-rose-950/90', border: 'border-rose-500', text: 'text-rose-400' }
  };

  const style = outcomeColors[outcome.outcome_class] || outcomeColors.marked_success;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md overflow-y-auto">
      <div className="glass-panel max-w-3xl w-full p-6 md:p-8 space-y-6 relative border-purple-500/30 my-8">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-full text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition"
        >
          <X size={20} />
        </button>

        {/* Outcome Header Banner */}
        <div className={`p-4 rounded-xl ${style.bg} border ${style.border} flex justify-between items-center`}>
          <div>
            <span className="text-xs uppercase tracking-widest text-slate-300 font-semibold flex items-center gap-1">
              <Award size={14} /> Deterministic Rules Outcome
            </span>
            <h2 className={`text-2xl font-bold font-cinzel ${style.text}`}>{outcome.outcome_title}</h2>
          </div>
          <div className="glass-pill text-xs font-semibold text-slate-200 uppercase">
            {outcome.outcome_class}
          </div>
        </div>

        {/* Resource Deltas */}
        <div className="grid grid-cols-3 gap-3 text-center">
          <div className="p-3 rounded-lg bg-slate-900/80 border border-amber-500/30">
            <div className="text-xs text-amber-400 font-semibold">Resonance Delta</div>
            <div className="text-lg font-bold font-cinzel text-amber-300">
              {outcome.resonance_delta >= 0 ? `+${outcome.resonance_delta}` : outcome.resonance_delta}
            </div>
          </div>
          <div className="p-3 rounded-lg bg-slate-900/80 border border-red-500/30">
            <div className="text-xs text-red-400 font-semibold">Strain Delta</div>
            <div className="text-lg font-bold font-cinzel text-red-300">
              {outcome.strain_delta >= 0 ? `+${outcome.strain_delta}` : outcome.strain_delta}
            </div>
          </div>
          <div className="p-3 rounded-lg bg-slate-900/80 border border-pink-500/30">
            <div className="text-xs text-pink-400 font-semibold">Thread Delta</div>
            <div className="text-lg font-bold font-cinzel text-pink-300">
              {outcome.thread_delta >= 0 ? `+${outcome.thread_delta}` : outcome.thread_delta}
            </div>
          </div>
        </div>

        {/* Soulkeeper AI Narrative */}
        <div className="space-y-3 p-5 rounded-xl bg-slate-900/90 border border-slate-800">
          <div className="flex justify-between items-center border-b border-slate-800 pb-2">
            <h3 className="text-lg font-bold font-cinzel text-purple-300 flex items-center gap-2">
              <Sparkles size={18} /> {narration.title}
            </h3>
            <span className="text-xs italic text-slate-400">Tone: {narration.tone}</span>
          </div>

          <p className="text-sm text-slate-200 leading-relaxed italic">{narration.prose}</p>

          <div className="pt-2">
            <div className="text-xs font-semibold text-slate-400 mb-1">Scene Beats:</div>
            <div className="flex flex-wrap gap-2">
              {narration.scene_beats.map((beat, idx) => (
                <span key={idx} className="glass-pill text-xs text-cyan-300 border-cyan-500/30">
                  • {beat}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Canon Writes */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-emerald-500/20">
          <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400 mb-2 flex items-center gap-1">
            <BookOpen size={14} /> Written to World Chronicle (Canon)
          </h4>
          <ul className="space-y-1 text-xs text-slate-300">
            {outcome.canon_facts.map((fact, i) => (
              <li key={i} className="flex items-start gap-2">
                <CheckCircle2 size={14} className="text-emerald-400 mt-0.5 shrink-0" />
                <span>{fact}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* 5-Gate Canon Guardian Audit */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-slate-400">
            <ShieldCheck size={16} className="text-indigo-400" /> Canon Guardian 5-Gate Audit Log
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
            {narration.guardian_audit.map((gate, i) => (
              <div key={i} className="p-2 rounded bg-slate-950/80 border border-slate-800 flex items-start gap-2">
                <CheckCircle2 size={14} className="text-emerald-400 mt-0.5 shrink-0" />
                <div>
                  <div className="font-semibold text-slate-200">{gate.gate_name}</div>
                  <div className="text-slate-400 text-[11px]">{gate.details}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="flex justify-end">
          <button onClick={onClose} className="btn-primary">
            Return to Mythic Sanctuary
          </button>
        </div>
      </div>
    </div>
  );
};
