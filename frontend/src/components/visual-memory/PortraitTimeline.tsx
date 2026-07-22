// frontend/src/components/visual-memory/PortraitTimeline.tsx
import React, { useState } from 'react';
import type { PortraitVersion } from '../../types';
import { PortraitVersionCard } from './PortraitVersionCard';
import { History, Camera } from 'lucide-react';

interface PortraitTimelineProps {
  portraits: PortraitVersion[];
}

export const PortraitTimeline: React.FC<PortraitTimelineProps> = ({ portraits }) => {
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(
    portraits.length > 0 ? portraits[portraits.length - 1].version_id : null
  );

  const selectedVersion = portraits.find((p) => p.version_id === selectedVersionId) || portraits[portraits.length - 1];

  return (
    <div className="space-y-6 font-mono text-xs">
      <div className="flex justify-between items-center border-b border-purple-500/20 pb-3">
        <h3 className="font-bold text-slate-100 text-sm flex items-center gap-2">
          <History size={16} className="text-purple-400" />
          <span>Chronological Portrait Timeline</span>
        </h3>
        <span className="text-[10px] text-purple-300">Historical Versions Locked</span>
      </div>

      {/* Grid of approved versions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {portraits.map((version, idx) => (
          <PortraitVersionCard
            key={version.version_id}
            version={version}
            isLatest={idx === portraits.length - 1}
            isSelected={selectedVersion?.version_id === version.version_id}
            onSelect={() => setSelectedVersionId(version.version_id)}
          />
        ))}
      </div>

      {/* Selected Version Detail Card */}
      {selectedVersion && (
        <div className="p-6 rounded-2xl bg-slate-900/90 border border-purple-500/30 space-y-4 shadow-xl">
          <div className="flex justify-between items-center border-b border-purple-500/20 pb-3">
            <div>
              <h4 className="font-bold text-slate-100 text-sm flex items-center gap-2">
                <Camera size={16} className="text-purple-400" />
                <span>Version #{selectedVersion.version_number}: {selectedVersion.label}</span>
              </h4>
              <span className="text-[10px] text-slate-400 font-mono">Snapshot Created: {selectedVersion.created_at || 'Canonical Baseline'}</span>
            </div>
            <span className="px-2.5 py-1 rounded-full bg-purple-950 border border-purple-500/40 text-purple-300 text-[10px] font-bold">
              ID: {selectedVersion.version_id}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="relative rounded-2xl overflow-hidden border border-purple-500/40 bg-slate-950 aspect-square">
              <img
                src={selectedVersion.image_url}
                alt={selectedVersion.label}
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80';
                }}
              />
            </div>

            <div className="md:col-span-2 space-y-4">
              <div>
                <span className="text-[10px] text-slate-500 block mb-1">HISTORICAL STORY MARKS AT SNAPSHOT TIME</span>
                {selectedVersion.story_marks_snapshot.length === 0 ? (
                  <div className="text-slate-500 text-[11px] italic">No story marks existed at this portrait snapshot.</div>
                ) : (
                  <div className="space-y-1.5">
                    {selectedVersion.story_marks_snapshot.map((mark) => (
                      <div key={mark.id} className="p-2.5 rounded-lg bg-slate-950 border border-amber-500/30 flex justify-between items-center text-[11px]">
                        <span className="text-amber-300 font-bold">
                          {mark.mark_type.replace('_', ' ')} ({mark.location.replace('_', ' ')})
                        </span>
                        <span className="text-slate-400 text-[10px]">Acquired: {mark.acquired_at}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <span className="text-[10px] text-slate-500 block mb-1">HISTORICAL EQUIPMENT AT SNAPSHOT TIME</span>
                {selectedVersion.equipment_snapshot ? (
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1 text-[11px] text-slate-300">
                    <div><strong>Armor:</strong> {selectedVersion.equipment_snapshot.armor}</div>
                    <div><strong>Clothing:</strong> {selectedVersion.equipment_snapshot.clothing}</div>
                    <div><strong>Weapons:</strong> {selectedVersion.equipment_snapshot.weapons.join(', ')}</div>
                    <div><strong>Relics:</strong> {selectedVersion.equipment_snapshot.relics.join(', ')}</div>
                  </div>
                ) : (
                  <div className="text-slate-500 text-[11px] italic">Standard Equipment</div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
