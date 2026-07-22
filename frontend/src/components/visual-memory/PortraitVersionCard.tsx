// frontend/src/components/visual-memory/PortraitVersionCard.tsx
import React from 'react';
import type { PortraitVersion } from '../../types';
import { Camera } from 'lucide-react';

interface PortraitVersionCardProps {
  version: PortraitVersion;
  isLatest: boolean;
  isSelected: boolean;
  onSelect: () => void;
}

export const PortraitVersionCard: React.FC<PortraitVersionCardProps> = ({
  version,
  isLatest,
  isSelected,
  onSelect,
}) => {
  return (
    <div
      onClick={onSelect}
      className={`p-4 rounded-2xl border ${isSelected ? 'bg-purple-950/40 border-purple-400 ring-2 ring-purple-500/50' : 'bg-slate-900/90 border-purple-500/20 hover:border-purple-500/40'} space-y-3 cursor-pointer transition font-mono text-xs`}
    >
      <div className="flex justify-between items-start">
        <div className="flex items-center gap-2">
          <span className="font-bold text-slate-100 text-sm">v{version.version_number}</span>
          <span className="text-purple-300 font-serif text-[11px] truncate max-w-[140px]">{version.label}</span>
        </div>
        {isLatest && (
          <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-bold text-[9px]">
            ACTIVE CANON
          </span>
        )}
      </div>

      <div className="relative rounded-xl overflow-hidden border border-purple-500/30 bg-slate-950 aspect-square">
        <img
          src={version.image_url}
          alt={version.label}
          className="w-full h-full object-cover"
          onError={(e) => {
            (e.target as HTMLImageElement).src = 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80';
          }}
        />
        <div className="absolute top-2 right-2 p-1 rounded bg-slate-950/80 backdrop-blur text-[9px] text-slate-300 flex items-center gap-1">
          <Camera size={10} className="text-purple-400" />
          <span>v{version.version_number}</span>
        </div>
      </div>

      <div className="space-y-1 text-[10px]">
        <div className="flex justify-between text-slate-400">
          <span>Marks Snapshot:</span>
          <span className="text-amber-300 font-bold">{version.story_marks_snapshot.length}</span>
        </div>
        <div className="flex justify-between text-slate-400">
          <span>Relics:</span>
          <span className="text-cyan-300">{version.equipment_snapshot?.relics.length ?? 0}</span>
        </div>
      </div>
    </div>
  );
};
