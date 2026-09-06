// frontend/src/components/visual-memory/GroupMemoryPanel.tsx
import React, { useCallback, useEffect, useState } from 'react';
import type { GroupMemory, MemoryObject, PerspectiveComparison } from '../../types';
import { apiClient } from '../../lib/api';
import { Eye, Link2, RefreshCw, Tags, Users } from 'lucide-react';

interface GroupMemoryPanelProps {
  memoryObject: MemoryObject;
  viewerSoulId?: string;
}

/**
 * Narrative, consent-filtered view of the shared event behind a Memory Object.
 * Disagreement is treated as perspective, never database corruption.
 */
export const GroupMemoryPanel: React.FC<GroupMemoryPanelProps> = ({
  memoryObject,
  viewerSoulId,
}) => {
  const [group, setGroup] = useState<GroupMemory | null>(null);
  const [comparison, setComparison] = useState<PerspectiveComparison | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const byEvent = await apiClient.getGroupMemoryByEvent(memoryObject.event_id, viewerSoulId);
      const groupMemory = byEvent.group_memory;
      setGroup(groupMemory);
      const comp = await apiClient.getGroupPerspectives(groupMemory.group_id, viewerSoulId);
      setComparison(comp);
    } catch {
      // No group memory yet; nothing to show.
      setGroup(null);
      setComparison(null);
    } finally {
      setLoading(false);
    }
  }, [memoryObject.event_id, viewerSoulId]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <div className="rounded-2xl bg-slate-900/70 border border-slate-800 p-3 text-slate-500 text-[10px] flex items-center gap-2 font-mono">
        <RefreshCw size={12} className="animate-spin" />
        <span>Looking for others who remember this event...</span>
      </div>
    );
  }

  if (!group || !comparison) {
    return null;
  }

  const others = comparison.perspectives.filter((p) => p.memory_object_id !== memoryObject.id);

  return (
    <div className="rounded-2xl bg-slate-900/70 border border-purple-500/25 p-4 space-y-3 font-mono text-xs">
      <div className="flex items-center justify-between border-b border-purple-500/20 pb-2">
        <h5 className="font-bold text-slate-200 text-xs flex items-center gap-2">
          <Users size={14} className="text-purple-400" />
          <span>Group Memory</span>
        </h5>
        <span className="text-[10px] text-purple-300 italic">Everyone remembers the same moment differently.</span>
      </div>

      <p className="text-slate-300 font-serif italic text-[11px]">{group.summary}</p>

      {others.length > 0 && (
        <div className="space-y-2">
          <span className="text-slate-500 block text-[10px] uppercase tracking-wider">Others remember this event</span>
          {others.map((p) => (
            <div key={p.memory_object_id} className="p-2 rounded-lg bg-slate-950 border border-slate-800">
              <div className="flex items-center gap-1.5">
                <Eye size={12} className="text-purple-400" />
                <span className="text-slate-200 font-bold">{p.character_name}</span>
                {p.role_in_event && <span className="text-slate-500 text-[10px]">({p.role_in_event})</span>}
              </div>
              {p.emotional_tone && (
                <div className="text-[10px] text-slate-400 mt-1">Feels: {p.emotional_tone}</div>
              )}
              {p.lasting_consequence && (
                <div className="text-[10px] text-amber-300 mt-0.5">Remembers: {p.lasting_consequence}</div>
              )}
            </div>
          ))}
        </div>
      )}

      {comparison.shared_facts.length > 0 && (
        <div>
          <span className="text-slate-500 block text-[10px] uppercase tracking-wider">Shared facts</span>
          <ul className="space-y-0.5 mt-1">
            {comparison.shared_facts.map((fact) => (
              <li key={fact} className="text-slate-300 text-[10px] flex items-center gap-1.5">
                <Link2 size={10} className="text-cyan-400" /> {fact}
              </li>
            ))}
          </ul>
        </div>
      )}

      {comparison.disagreements.length > 0 && (
        <div>
          <span className="text-slate-500 block text-[10px] uppercase tracking-wider">Different recollections</span>
          <div className="space-y-1 mt-1">
            {comparison.disagreements.map((d) => (
              <div key={d.field} className="text-[10px] text-slate-400">
                <span className="text-rose-300 font-bold">{d.field.replace('_', ' ')}:</span>{' '}
                {d.perspectives.map((per: { soul_id: string; [k: string]: string }) => `${per.soul_id} — ${per[d.field]}`).join(' · ')}
              </div>
            ))}
          </div>
        </div>
      )}

      {group.tags.length > 0 && (
        <div>
          <span className="text-slate-500 block text-[10px] uppercase tracking-wider flex items-center gap-1">
            <Tags size={10} /> Tags
          </span>
          <div className="flex flex-wrap gap-1.5 mt-1">
            {group.tags.map((tag) => (
              <span
                key={tag.tag_id}
                className="px-2 py-0.5 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-300 text-[10px]"
              >
                {tag.tag_type}:{tag.value}
                {tag.anchor_id ? ` @${tag.anchor_id}` : ''}
              </span>
            ))}
          </div>
        </div>
      )}

      {group.anchors.length > 0 && (
        <div>
          <span className="text-slate-500 block text-[10px] uppercase tracking-wider">Shared anchors</span>
          <div className="flex flex-wrap gap-1.5 mt-1">
            {group.anchors.map((anchor) => (
              <span
                key={`${anchor.anchor_type}:${anchor.anchor_ref}`}
                className="px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-[10px]"
              >
                {anchor.anchor_type}:{anchor.label}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
