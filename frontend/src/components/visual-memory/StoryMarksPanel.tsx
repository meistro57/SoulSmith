// frontend/src/components/visual-memory/StoryMarksPanel.tsx
import React, { useState } from 'react';
import type { StoryMark } from '../../types';
import { Flame, GitCommit, Plus } from 'lucide-react';

interface StoryMarksPanelProps {
  storyMarks: StoryMark[];
  onAddStoryMark: (mark: { mark_type: string; location: string; origin_event_id: string; acquired_at: string }) => Promise<void>;
}

export const StoryMarksPanel: React.FC<StoryMarksPanelProps> = ({ storyMarks, onAddStoryMark }) => {
  const [markType, setMarkType] = useState<string>('scar');
  const [markLocation, setMarkLocation] = useState<string>('left_cheek');
  const [originEventId, setOriginEventId] = useState<string>('evt_glass_observatory_01');
  const [acquiredAt, setAcquiredAt] = useState<string>('Year 3, Frostwane');
  const [submitting, setSubmitting] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!originEventId.trim()) return;
    setSubmitting(true);
    try {
      await onAddStoryMark({
        mark_type: markType,
        location: markLocation,
        origin_event_id: originEventId.trim(),
        acquired_at: acquiredAt.trim(),
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p-6 rounded-2xl bg-slate-900/90 border border-purple-500/20 space-y-5 shadow-xl font-mono text-xs">
      <div className="flex justify-between items-center border-b border-purple-500/20 pb-3">
        <h3 className="font-bold text-slate-100 text-sm flex items-center gap-2">
          <Flame size={16} className="text-amber-400" />
          <span>Provenance-Backed Story Marks Ledger</span>
        </h3>
        <span className="text-[10px] text-amber-400">Tied to Chronicle Events</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Story marks list */}
        <div className="space-y-3">
          {storyMarks.length === 0 ? (
            <div className="text-slate-500 text-center py-6 border border-slate-800 rounded-xl">
              No story marks or scars recorded yet.
            </div>
          ) : (
            storyMarks.map((mark) => (
              <div key={mark.id} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-amber-300 uppercase tracking-wider text-[11px]">
                    {mark.mark_type.replace('_', ' ')} ({mark.location.replace('_', ' ')})
                  </span>
                  <span className="text-[10px] text-emerald-400 font-bold">{mark.status}</span>
                </div>
                <div className="text-[10px] text-slate-400 flex items-center gap-1">
                  <GitCommit size={12} className="text-indigo-400" />
                  <span>Origin Event: <strong>#{mark.origin_event_id}</strong> ({mark.acquired_at})</span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Add story mark form */}
        <form onSubmit={handleSubmit} className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
          <span className="text-slate-200 font-bold block text-[11px]">Acquire New Canonical Story Mark</span>
          
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-slate-400 text-[10px] mb-1">Mark Type</label>
              <select
                value={markType}
                onChange={(e) => setMarkType(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200 text-[11px]"
              >
                <option value="scar">Scar</option>
                <option value="burn_mark">Burn Mark</option>
                <option value="blessed_tattoo">Blessed Tattoo</option>
                <option value="broken_horn">Broken Horn</option>
                <option value="gray_hair">Gray Hair</option>
              </select>
            </div>
            <div>
              <label className="block text-slate-400 text-[10px] mb-1">Body Location</label>
              <input
                type="text"
                placeholder="e.g. left_cheek"
                value={markLocation}
                onChange={(e) => setMarkLocation(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200 text-[11px]"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-400 text-[10px] mb-1">Originating Chronicle Event ID</label>
            <input
              type="text"
              required
              placeholder="e.g. evt_glass_observatory_01"
              value={originEventId}
              onChange={(e) => setOriginEventId(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200 text-[11px]"
            />
          </div>

          <div>
            <label className="block text-slate-400 text-[10px] mb-1">Acquired Date / Era</label>
            <input
              type="text"
              placeholder="e.g. Year 3, Frostwane"
              value={acquiredAt}
              onChange={(e) => setAcquiredAt(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200 text-[11px]"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-2.5 px-3 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 border border-amber-400/40 text-amber-200 font-bold transition cursor-pointer flex items-center justify-center gap-1 text-[11px]"
          >
            <Plus size={12} />
            <span>{submitting ? 'Adding Story Mark...' : 'Add Provenance-Backed Mark'}</span>
          </button>
        </form>
      </div>
    </div>
  );
};
