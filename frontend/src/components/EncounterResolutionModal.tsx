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
    ascendancy: { bg: 'bg-emerald-950/90', border: 'border-emerald-500', text: 'text-emerald-300' },
    marked_success: { bg: 'bg-amber-950/90', border: 'border-amber-500', text: 'text-amber-300' },
    revelatory_failure: { bg: 'bg-purple-950/90', border: 'border-purple-500', text: 'text-purple-300' },
    collapse: { bg: 'bg-rose-950/90', border: 'border-rose-500', text: 'text-rose-300' }
  };

  const style = outcomeColors[outcome.outcome_class] || outcomeColors.marked_success;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#05040a]/90 backdrop-blur-xl overflow-y-auto">
      <div className="mythic-card max-w-3xl w-full p-6 md:p-8 space-y-6 relative border-amber-500/40 my-8 shadow-2xl">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-full text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition"
        >
          <X size={20} />
        </button>

        {/* Outcome Header Banner */}
        <div className={`p-5 rounded-2xl ${style.bg} border ${style.border} flex justify-between items-center shadow-lg`}>
          <div>
            <span className="text-xs uppercase tracking-widest text-slate-300 font-bold flex items-center gap-1.5">
              <Award size={16} /> Deterministic Rules Outcome
            </span>
            <h2 className={`text-3xl font-black font-cinzel ${style.text} mt-1`}>{outcome.outcome_title}</h2>
          </div>
          <span className="mythic-pill border-amber-500/40 text-amber-300">
            {outcome.outcome_class}
          </span>
        </div>

        {/* Resource Deltas */}
        <div className="grid grid-cols-3 gap-4 text-center">
          <div className="p-4 rounded-xl bg-slate-950/90 border border-amber-500/30">
            <div className="text-xs text-amber-400 font-bold uppercase tracking-wider">Resonance</div>
            <div className="text-xl font-black font-cinzel text-amber-300 mt-1">
              {outcome.resonance_delta >= 0 ? `+${outcome.resonance_delta}` : outcome.resonance_delta}
            </div>
          </div>
          <div className="p-4 rounded-xl bg-slate-950/90 border border-red-500/30">
            <div className="text-xs text-red-400 font-bold uppercase tracking-wider">Strain</div>
            <div className="text-xl font-black font-cinzel text-red-300 mt-1">
              {outcome.strain_delta >= 0 ? `+${outcome.strain_delta}` : outcome.strain_delta}
            </div>
          </div>
          <div className="p-4 rounded-xl bg-slate-950/90 border border-pink-500/30">
            <div className="text-xs text-pink-400 font-bold uppercase tracking-wider">Threads</div>
            <div className="text-xl font-black font-cinzel text-pink-300 mt-1">
              {outcome.thread_delta >= 0 ? `+${outcome.thread_delta}` : outcome.thread_delta}
            </div>
          </div>
        </div>

        {/* Soulkeeper AI Narrative */}
        <div className="space-y-4 p-6 rounded-2xl bg-slate-950/90 border border-slate-800">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <h3 className="text-xl font-bold font-cinzel text-purple-300 flex items-center gap-2">
              <Sparkles size={20} /> {narration.title}
            </h3>
            <span className="text-xs italic text-slate-400">Tone: {narration.tone}</span>
          </div>

          <p className="text-sm text-slate-200 leading-relaxed italic font-light">{narration.prose}</p>

          <div className="pt-2">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Scene Beats:</div>
            <div className="flex flex-wrap gap-2">
              {narration.scene_beats.map((beat, idx) => (
                <span key={idx} className="mythic-pill text-cyan-300 border-cyan-500/30">
                  • {beat}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Canon Writes */}
        <div className="p-5 rounded-2xl bg-slate-950/90 border border-emerald-500/30 space-y-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
            <BookOpen size={16} /> Written to World Chronicle (Canon)
          </h4>
          <ul className="space-y-1.5 text-xs text-slate-300">
            {outcome.canon_facts.map((fact, i) => (
              <li key={i} className="flex items-start gap-2">
                <CheckCircle2 size={16} className="text-emerald-400 mt-0.5 shrink-0" />
                <span>{fact}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* 5-Gate Canon Guardian Audit */}
        <div className="p-5 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-slate-300">
            <ShieldCheck size={18} className="text-indigo-400" /> Canon Guardian 5-Gate Audit Log
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 text-xs">
            {narration.guardian_audit.map((gate, i) => (
              <div key={i} className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex items-start gap-2.5">
                <CheckCircle2 size={16} className="text-emerald-400 mt-0.5 shrink-0" />
                <div>
                  <div className="font-bold text-slate-200">{gate.gate_name}</div>
                  <div className="text-slate-400 text-[11px] leading-normal">{gate.details}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="flex justify-end">
          <button onClick={onClose} className="btn-gold">
            Return to Mythic Sanctuary
          </button>
        </div>
      </div>
    </div>
  );
};
