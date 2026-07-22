// frontend/src/components/visual-memory/MemoryObjectCard.tsx
import React from 'react';
import type { MemoryObject } from '../../types';
import { BookMarked, Camera, User } from 'lucide-react';

interface MemoryObjectCardProps {
  memoryObject: MemoryObject;
}

export const MemoryObjectCard: React.FC<MemoryObjectCardProps> = ({ memoryObject }) => {
  return (
    <div className="p-5 rounded-2xl bg-slate-900/90 border border-indigo-500/20 space-y-3 font-mono text-xs shadow-xl">
      <div className="flex justify-between items-center border-b border-indigo-500/20 pb-2">
        <h4 className="font-bold text-slate-100 text-sm flex items-center gap-2">
          <BookMarked size={16} className="text-indigo-400" />
          <span>{memoryObject.event_title}</span>
        </h4>
        <span className="text-[10px] text-cyan-300 font-bold">#{memoryObject.event_id}</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px]">
        <div>
          <span className="text-slate-500 block text-[10px]">PARTICIPANTS & HISTORICAL PORTRAIT LOCK</span>
          <div className="space-y-1 mt-1">
            {memoryObject.participants.map((p) => (
              <div key={p.soul_id} className="p-2 rounded bg-slate-950 border border-slate-800 flex justify-between items-center">
                <span className="text-slate-200 font-bold flex items-center gap-1">
                  <User size={12} className="text-purple-400" />
                  {p.character_name} ({p.role_in_event})
                </span>
                <span className="text-[10px] font-mono text-purple-300 flex items-center gap-1">
                  <Camera size={10} /> {p.portrait_version_id}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <div>
            <span className="text-slate-500 block text-[10px]">ENVIRONMENT & TONE</span>
            <span className="text-slate-300 font-serif">{memoryObject.location_environment} ({memoryObject.emotional_tone})</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">ACTION & COMPOSITION</span>
            <span className="text-slate-300 font-serif">{memoryObject.action_composition}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">LASTING CONSEQUENCE</span>
            <span className="text-amber-300 font-serif">{memoryObject.lasting_consequence}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
