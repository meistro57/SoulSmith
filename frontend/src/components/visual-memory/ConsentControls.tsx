// frontend/src/components/visual-memory/ConsentControls.tsx
import React from 'react';
import type { ConsentSettings } from '../../types';
import { Tag, Lock, CheckCircle2 } from 'lucide-react';

interface ConsentControlsProps {
  consent: ConsentSettings;
}

export const ConsentControls: React.FC<ConsentControlsProps> = ({ consent }) => {
  return (
    <div className="p-6 rounded-2xl bg-slate-900/90 border border-emerald-500/20 space-y-4 shadow-xl font-mono text-xs">
      <div className="flex justify-between items-center border-b border-emerald-500/20 pb-3">
        <h3 className="font-bold text-slate-100 text-sm flex items-center gap-2">
          <Tag size={16} className="text-emerald-400" />
          <span>Group Tagging & Recognition Consent</span>
        </h3>
        <span className="text-[10px] text-emerald-400">Strict Privacy Boundaries</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-slate-200 font-bold">In-World Character Tagging</span>
            <span className="text-emerald-400 font-bold flex items-center gap-1">
              <CheckCircle2 size={12} /> {consent.allow_character_tagging ? 'Allowed' : 'Disabled'}
            </span>
          </div>
          <p className="text-[10px] text-slate-400 leading-relaxed">
            Allows other players' Chronicle paintings to include your character portrait version when you participate in joint gatherings.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-slate-200 font-bold">Real-Person Photo Tagging</span>
            <span className="text-amber-400 font-bold flex items-center gap-1">
              <Lock size={12} /> {consent.allow_real_person_tagging ? 'Opted In' : 'Opted Out (Default)'}
            </span>
          </div>
          <p className="text-[10px] text-slate-400 leading-relaxed">
            Real photos will never automatically become source material for fantasy art unless explicitly opted in.
          </p>
        </div>
      </div>
    </div>
  );
};
