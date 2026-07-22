// frontend/src/components/VisualMemoryView.tsx
import React, { useCallback, useEffect, useState } from 'react';
import type { MemoryObject, VisualAvatarProfile } from '../types';
import { apiClient } from '../lib/api';
import { Image, Sparkles, Flame, Shield, History, Camera, User, Tag, Plus, CheckCircle2, GitCommit, Layers } from 'lucide-react';

interface VisualMemoryViewProps {
  soulName: string;
}

export const VisualMemoryView: React.FC<VisualMemoryViewProps> = ({ soulName }) => {
  const [activeSubTab, setActiveSubTab] = useState<'avatar' | 'timeline' | 'memory_compiler' | 'tags'>('avatar');
  const [profile, setProfile] = useState<VisualAvatarProfile | null>(null);
  const [memoryObjects, setMemoryObjects] = useState<MemoryObject[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // Forms State
  const [markType, setMarkType] = useState<string>('scar');
  const [markLocation, setMarkLocation] = useState<string>('left_cheek');
  const [originEventId, setOriginEventId] = useState<string>('evt_salt_spire_01');
  const [acquiredAt, setAcquiredAt] = useState<string>('Year 3, Frostwane');
  
  // Portrait Snapshot Form
  const [snapshotLabel, setSnapshotLabel] = useState<string>('');
  const [snapshotUrl, setSnapshotUrl] = useState<string>('');

  // Memory Compiler Form
  const [eventId, setEventId] = useState<string>('evt_salt_spire_01');
  const [eventTitle, setEventTitle] = useState<string>('Awakening of the Salt Spire');
  const [locationEnv, setLocationEnv] = useState<string>('Salt-encrusted subterranean sanctuary');
  const [emotionalTone, setEmotionalTone] = useState<string>('Tense awakening, solemn reverence');
  const [actionComposition, setActionComposition] = useState<string>('Kaelen channels starlight while Vael anchors the physical altar.');
  const [lastingConsequence, setLastingConsequence] = useState<string>('Kaelen received a prominent scar on left cheek; Salt Bell awakened.');

  const fetchProfileAndMemories = useCallback(async () => {
    setLoading(true);
    try {
      const profData = await apiClient.getVisualAvatarProfile(soulName);
      setProfile(profData);

      const memData = await apiClient.listMemoryObjects();
      setMemoryObjects(memData.memory_objects);
    } catch (err) {
      console.error('Failed to load visual avatar profile:', err);
    } finally {
      setLoading(false);
    }
  }, [soulName]);

  useEffect(() => {
    fetchProfileAndMemories();
  }, [fetchProfileAndMemories]);

  const handleAddStoryMark = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await apiClient.addStoryMark({
        soul_id: soulName,
        mark_type: markType,
        location: markLocation,
        origin_event_id: originEventId,
        acquired_at: acquiredAt,
        visibility: 'prominent',
        status: 'permanent',
      });
      setStatusMessage(`Added story mark '${res.story_mark.mark_type}' linked to event #${res.story_mark.origin_event_id}!`);
      fetchProfileAndMemories();
      setTimeout(() => setStatusMessage(null), 4000);
    } catch (err) {
      console.error('Failed to add story mark:', err);
    }
  };

  const handleSnapshotPortrait = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!snapshotLabel) return;
    try {
      const res = await apiClient.createPortraitSnapshot({
        soul_id: soulName,
        label: snapshotLabel,
        image_url: snapshotUrl || `/assets/portraits/${soulName.toLowerCase()}_v_new.png`,
      });
      setSnapshotLabel('');
      setSnapshotUrl('');
      setStatusMessage(`Created Portrait Snapshot '${res.portrait.label}' (v${res.portrait.version_number})!`);
      fetchProfileAndMemories();
      setTimeout(() => setStatusMessage(null), 4000);
    } catch (err) {
      console.error('Failed to create portrait snapshot:', err);
    }
  };

  const handleCompileMemoryObject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile) return;
    try {
      const activePortrait = profile.portraits[profile.portraits.length - 1];
      const res = await apiClient.compileMemoryObject({
        event_id: eventId,
        event_title: eventTitle,
        participants: [
          {
            soul_id: soulName,
            character_name: soulName,
            portrait_version_id: activePortrait ? activePortrait.version_id : 'pv_kael_1',
            role_in_event: 'Focus',
            real_person_tag_opt_in: false,
          },
          {
            soul_id: 'Archivist Vael',
            character_name: 'Archivist Vael',
            portrait_version_id: 'pv_vael_1',
            role_in_event: 'Witness',
            real_person_tag_opt_in: true,
          },
        ],
        location_environment: locationEnv,
        relics_involved: ['Dormant Salt Bell'],
        emotional_tone: emotionalTone,
        action_composition: actionComposition,
        lasting_consequence: lastingConsequence,
        privacy_consent_scope: 'public_canon',
      });
      setStatusMessage(`Compiled Chronicle Event '${res.memory_object.event_title}' into a structured Memory Object!`);
      fetchProfileAndMemories();
      setTimeout(() => setStatusMessage(null), 4000);
    } catch (err) {
      console.error('Failed to compile memory object:', err);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-purple-950 to-slate-900 border border-purple-500/30 p-6 md:p-8 shadow-2xl">
        <div className="relative z-10 space-y-3">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-purple-400/10 border border-purple-400/30 text-purple-300 text-xs font-mono">
            <Image className="w-3.5 h-3.5" />
            <span>Phase 9: Visual Identity Foundation & Memory Objects</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-200 via-amber-100 to-indigo-200">
            Living Avatar & Visual Memory Sanctuary
          </h1>
          <p className="text-slate-300 text-xs md:text-sm max-w-3xl leading-relaxed font-serif">
            "The portrait is disposable. The history beneath it is canonical." Every scar, age progression, relic awakening, and story mark holds explicit provenance linked to event IDs in the Chronicle.
          </p>
        </div>
      </div>

      {statusMessage && (
        <div className="p-3.5 rounded-xl bg-purple-950/80 border border-purple-500/40 text-purple-200 text-xs font-mono flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{statusMessage}</span>
          </div>
          <button onClick={() => setStatusMessage(null)} className="text-slate-400 hover:text-slate-200">
            ✕
          </button>
        </div>
      )}

      {/* Sub-Tab Navigation */}
      <div className="flex border-b border-purple-500/20 font-mono text-xs">
        <button
          onClick={() => setActiveSubTab('avatar')}
          className={`py-3 px-5 font-bold transition flex items-center gap-2 border-b-2 cursor-pointer ${
            activeSubTab === 'avatar'
              ? 'border-purple-400 text-purple-300 bg-purple-950/20'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <User size={14} />
          <span>Living Avatar & Story Marks</span>
        </button>

        <button
          onClick={() => setActiveSubTab('timeline')}
          className={`py-3 px-5 font-bold transition flex items-center gap-2 border-b-2 cursor-pointer ${
            activeSubTab === 'timeline'
              ? 'border-purple-400 text-purple-300 bg-purple-950/20'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <History size={14} />
          <span>Portrait Timeline ({profile?.portraits.length || 0})</span>
        </button>

        <button
          onClick={() => setActiveSubTab('memory_compiler')}
          className={`py-3 px-5 font-bold transition flex items-center gap-2 border-b-2 cursor-pointer ${
            activeSubTab === 'memory_compiler'
              ? 'border-purple-400 text-purple-300 bg-purple-950/20'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Layers size={14} />
          <span>Memory Object Compiler ({memoryObjects.length})</span>
        </button>

        <button
          onClick={() => setActiveSubTab('tags')}
          className={`py-3 px-5 font-bold transition flex items-center gap-2 border-b-2 cursor-pointer ${
            activeSubTab === 'tags'
              ? 'border-purple-400 text-purple-300 bg-purple-950/20'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Tag size={14} />
          <span>Group Tags & Consent</span>
        </button>
      </div>

      {loading || !profile ? (
        <div className="text-center py-10 font-mono text-slate-400 animate-pulse text-xs">
          Loading visual memory engine...
        </div>
      ) : (
        <>
          {/* TAB 1: LIVING AVATAR & STORY MARKS */}
          {activeSubTab === 'avatar' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Permanent Identity Card */}
                <div className="p-6 rounded-2xl bg-slate-900/90 border border-purple-500/20 space-y-4 shadow-xl">
                  <div className="flex justify-between items-center border-b border-purple-500/20 pb-3">
                    <h3 className="font-bold text-slate-100 text-sm flex items-center gap-2">
                      <Sparkles size={16} className="text-purple-400" />
                      <span>Permanent Identity Layer</span>
                    </h3>
                    <span className="text-[10px] font-mono text-slate-400">Rarely Changes</span>
                  </div>

                  <div className="space-y-3 font-mono text-xs">
                    <div>
                      <span className="text-slate-500 block text-[10px]">CHARACTER NAME</span>
                      <span className="text-slate-100 font-bold text-sm">{profile.identity.soul_id}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">SPECIES & ASPECT</span>
                      <span className="text-purple-300">{profile.identity.species}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">FACIAL STRUCTURE</span>
                      <span className="text-slate-300 font-serif">{profile.identity.face}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">EYES & VISION</span>
                      <span className="text-amber-300">{profile.identity.eyes}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">HAIR & CROWN</span>
                      <span className="text-slate-300 font-serif">{profile.identity.hair}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">BODY BUILD</span>
                      <span className="text-slate-300 font-serif">{profile.identity.body}</span>
                    </div>
                  </div>
                </div>

                {/* Equipment Appearance Layer */}
                <div className="p-6 rounded-2xl bg-slate-900/90 border border-purple-500/20 space-y-4 shadow-xl">
                  <div className="flex justify-between items-center border-b border-purple-500/20 pb-3">
                    <h3 className="font-bold text-slate-100 text-sm flex items-center gap-2">
                      <Shield size={16} className="text-indigo-400" />
                      <span>Equipment Layer</span>
                    </h3>
                    <span className="text-[10px] font-mono text-indigo-400">Dynamic</span>
                  </div>

                  <div className="space-y-3 font-mono text-xs">
                    <div>
                      <span className="text-slate-500 block text-[10px]">ARMOR</span>
                      <span className="text-slate-200 font-serif">{profile.equipment.armor}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">CLOTHING & EMBROIDERY</span>
                      <span className="text-slate-200 font-serif">{profile.equipment.clothing}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">WEAPONS</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {profile.equipment.weapons.map((w) => (
                          <span key={w} className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-[10px] text-cyan-300">
                            {w}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">RELICS</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {profile.equipment.relics.map((r) => (
                          <span key={r} className="px-2 py-0.5 rounded bg-amber-950 border border-amber-500/30 text-[10px] text-amber-300">
                            {r}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Story Marks Ledger */}
                <div className="p-6 rounded-2xl bg-slate-900/90 border border-purple-500/20 space-y-4 shadow-xl">
                  <div className="flex justify-between items-center border-b border-purple-500/20 pb-3">
                    <h3 className="font-bold text-slate-100 text-sm flex items-center gap-2">
                      <Flame size={16} className="text-amber-400" />
                      <span>Story Marks Ledger</span>
                    </h3>
                    <span className="text-[10px] font-mono text-amber-400">Provenance-Backed</span>
                  </div>

                  <div className="space-y-3">
                    {profile.story_marks.length === 0 ? (
                      <div className="text-slate-500 text-center py-4 font-mono text-xs">
                        No story marks or scars recorded yet.
                      </div>
                    ) : (
                      profile.story_marks.map((mark) => (
                        <div key={mark.id} className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1 font-mono text-xs">
                          <div className="flex justify-between items-center">
                            <span className="font-bold text-amber-300 uppercase tracking-wider text-[11px]">
                              {mark.mark_type} ({mark.location})
                            </span>
                            <span className="text-[10px] text-emerald-400">{mark.status}</span>
                          </div>
                          <div className="text-[10px] text-slate-400 flex items-center gap-1">
                            <GitCommit size={12} className="text-indigo-400" />
                            <span>Origin Event: <strong>#{mark.origin_event_id}</strong> ({mark.acquired_at})</span>
                          </div>
                        </div>
                      ))
                    )}

                    {/* Add Story Mark Form */}
                    <form onSubmit={handleAddStoryMark} className="pt-2 space-y-3 border-t border-slate-800 font-mono text-xs">
                      <span className="text-slate-300 font-bold block text-[11px]">Acquire New Story Mark</span>
                      <div className="grid grid-cols-2 gap-2">
                        <select
                          value={markType}
                          onChange={(e) => setMarkType(e.target.value)}
                          className="bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 text-[11px]"
                        >
                          <option value="scar">Scar</option>
                          <option value="burn_mark">Burn Mark</option>
                          <option value="blessed_tattoo">Blessed Tattoo</option>
                          <option value="broken_horn">Broken Horn</option>
                          <option value="gray_hair">Gray Hair</option>
                        </select>
                        <input
                          type="text"
                          placeholder="Location (e.g. left_cheek)"
                          value={markLocation}
                          onChange={(e) => setMarkLocation(e.target.value)}
                          className="bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 text-[11px]"
                        />
                      </div>
                      <input
                        type="text"
                        placeholder="Origin Event ID (e.g. evt_salt_spire_01)"
                        value={originEventId}
                        onChange={(e) => setOriginEventId(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 text-[11px]"
                      />
                      <input
                        type="text"
                        placeholder="Acquired At (e.g. Year 3, Frostwane)"
                        value={acquiredAt}
                        onChange={(e) => setAcquiredAt(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 text-[11px]"
                      />
                      <button
                        type="submit"
                        className="w-full py-2 px-3 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 border border-amber-400/40 text-amber-200 font-bold transition cursor-pointer flex items-center justify-center gap-1 text-[11px]"
                      >
                        <Plus size={12} /> Add Provenance-Backed Mark
                      </button>
                    </form>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: PORTRAIT TIMELINE */}
          {activeSubTab === 'timeline' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                    <History className="w-4 h-4 text-purple-400" />
                    <span>Chronological Portrait Timeline</span>
                  </h3>
                  <p className="text-xs text-slate-400">
                    Older portrait versions remain immutable. Regenerating an avatar cannot erase canonical history.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {profile.portraits.map((p) => (
                  <div key={p.version_id} className="p-6 rounded-2xl bg-slate-900/90 border border-purple-500/30 space-y-4 shadow-xl flex flex-col justify-between">
                    <div className="space-y-3 font-mono text-xs">
                      <div className="flex justify-between items-center">
                        <span className="font-bold text-purple-300 text-sm">{p.label}</span>
                        <span className="px-2.5 py-0.5 rounded-full bg-purple-950 border border-purple-500/40 text-purple-200 font-bold text-[10px]">
                          Version v{p.version_number}
                        </span>
                      </div>

                      {/* Mock Portrait Canvas */}
                      <div className="w-full h-44 rounded-xl bg-slate-950 border border-slate-800 flex flex-col items-center justify-center p-4 text-center space-y-2 relative overflow-hidden">
                        <Camera className="w-8 h-8 text-purple-400/60" />
                        <span className="text-slate-300 font-cinzel text-xs font-bold">{p.label}</span>
                        <span className="text-[10px] text-slate-500">{p.image_url}</span>
                      </div>

                      {/* Snapshot Story Marks */}
                      <div className="space-y-1">
                        <span className="text-[10px] text-slate-500 block font-bold uppercase">Marks at Time of Version:</span>
                        {p.story_marks_snapshot.length === 0 ? (
                          <span className="text-slate-400 italic text-[11px]">Original Pre-Scar Identity</span>
                        ) : (
                          p.story_marks_snapshot.map((m) => (
                            <span key={m.id} className="inline-block px-2 py-0.5 rounded bg-amber-950 border border-amber-500/30 text-amber-300 text-[10px] mr-1">
                              {m.mark_type} ({m.location})
                            </span>
                          ))
                        )}
                      </div>
                    </div>

                    <div className="text-[10px] font-mono text-slate-500 pt-3 border-t border-slate-800">
                      Created: {p.created_at || 'Canonical Version'}
                    </div>
                  </div>
                ))}
              </div>

              {/* Snapshot New Portrait Form */}
              <div className="p-6 rounded-2xl bg-slate-900/90 border border-indigo-500/20 space-y-4">
                <h4 className="font-bold text-slate-100 text-sm font-mono flex items-center gap-2">
                  <Camera size={14} className="text-indigo-400" />
                  <span>Snapshot New Portrait Version</span>
                </h4>
                <form onSubmit={handleSnapshotPortrait} className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono text-xs">
                  <div>
                    <label className="block text-slate-400 mb-1">Version Label</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Post-Salt-Spire Awakening"
                      value={snapshotLabel}
                      onChange={(e) => setSnapshotLabel(e.target.value)}
                      className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl p-2.5 text-slate-100 focus:outline-none focus:border-purple-400"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1">Image Asset Path / URL</label>
                    <input
                      type="text"
                      placeholder="/assets/portraits/kaelen_v2.png"
                      value={snapshotUrl}
                      onChange={(e) => setSnapshotUrl(e.target.value)}
                      className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl p-2.5 text-slate-100 focus:outline-none focus:border-purple-400"
                    />
                  </div>
                  <div className="flex items-end">
                    <button
                      type="submit"
                      className="w-full py-2.5 px-4 rounded-xl bg-purple-500 hover:bg-purple-400 text-slate-950 font-bold transition cursor-pointer shadow-lg"
                    >
                      Snapshot Version
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* TAB 3: MEMORY OBJECT COMPILER */}
          {activeSubTab === 'memory_compiler' && (
            <div className="space-y-6">
              <div className="p-6 rounded-2xl bg-slate-900/90 border border-purple-500/30 space-y-4 shadow-xl">
                <h3 className="text-base font-bold text-slate-100 flex items-center gap-2 font-cinzel">
                  <Layers className="w-4 h-4 text-purple-400" />
                  <span>Chronicle Event Memory Object Compiler</span>
                </h3>
                <p className="text-xs text-slate-300 font-serif leading-relaxed">
                  Compiles a Chronicle event into a first-class Memory Object schema linking participants to the exact historical `PortraitVersion` they held when the event occurred.
                </p>

                <form onSubmit={handleCompileMemoryObject} className="space-y-4 font-mono text-xs">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-slate-400 mb-1">Canonical Event ID</label>
                      <input
                        type="text"
                        required
                        value={eventId}
                        onChange={(e) => setEventId(e.target.value)}
                        className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl p-2.5 text-slate-100"
                      />
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1">Event Title</label>
                      <input
                        type="text"
                        required
                        value={eventTitle}
                        onChange={(e) => setEventTitle(e.target.value)}
                        className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl p-2.5 text-slate-100"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-slate-400 mb-1">Location & Environment Description</label>
                    <input
                      type="text"
                      required
                      value={locationEnv}
                      onChange={(e) => setLocationEnv(e.target.value)}
                      className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl p-2.5 text-slate-100"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-slate-400 mb-1">Emotional Tone</label>
                      <input
                        type="text"
                        required
                        value={emotionalTone}
                        onChange={(e) => setEmotionalTone(e.target.value)}
                        className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl p-2.5 text-slate-100"
                      />
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1">Action & Composition</label>
                      <input
                        type="text"
                        required
                        value={actionComposition}
                        onChange={(e) => setActionComposition(e.target.value)}
                        className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl p-2.5 text-slate-100"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-slate-400 mb-1">Lasting Consequence</label>
                    <input
                      type="text"
                      required
                      value={lastingConsequence}
                      onChange={(e) => setLastingConsequence(e.target.value)}
                      className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl p-2.5 text-slate-100"
                    />
                  </div>

                  <button
                    type="submit"
                    className="py-2.5 px-6 rounded-xl bg-purple-500 hover:bg-purple-400 text-slate-950 font-bold transition cursor-pointer shadow-lg"
                  >
                    Compile Memory Object
                  </button>
                </form>
              </div>

              {/* Memory Objects Gallery */}
              <div className="space-y-4">
                <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
                  Compiled Chronicle Memory Objects ({memoryObjects.length})
                </h4>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {memoryObjects.map((mem) => (
                    <div key={mem.id} className="p-5 rounded-2xl bg-slate-900/90 border border-indigo-500/20 space-y-3 font-mono text-xs shadow-xl">
                      <div className="flex justify-between items-start">
                        <div>
                          <span className="text-[10px] text-purple-400 font-bold">EVENT #{mem.event_id}</span>
                          <h4 className="font-bold text-slate-100 text-sm font-cinzel">{mem.event_title}</h4>
                        </div>
                        <span className="px-2.5 py-0.5 rounded-full bg-emerald-950 border border-emerald-500/40 text-emerald-300 text-[10px] font-bold">
                          {mem.visual_generation_status.toUpperCase()}
                        </span>
                      </div>

                      <p className="text-slate-300 font-serif leading-relaxed text-xs">
                        {mem.action_composition}
                      </p>

                      <div className="space-y-1 text-[11px] pt-2 border-t border-slate-800">
                        <div><strong className="text-slate-400">Environment:</strong> <span className="text-slate-200">{mem.location_environment}</span></div>
                        <div><strong className="text-slate-400">Tone:</strong> <span className="text-amber-300">{mem.emotional_tone}</span></div>
                        <div><strong className="text-slate-400">Consequence:</strong> <span className="text-emerald-300">{mem.lasting_consequence}</span></div>
                      </div>

                      <div className="pt-2 border-t border-slate-800 flex justify-between items-center text-[10px]">
                        <span className="text-cyan-300">{mem.participants.length} Participants Locked</span>
                        <span className="text-slate-500">{mem.privacy_consent_scope}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: GROUP TAGS & CONSENT */}
          {activeSubTab === 'tags' && (
            <div className="space-y-6">
              <div className="p-6 rounded-2xl bg-slate-900/90 border border-indigo-500/20 space-y-4 shadow-xl font-mono text-xs">
                <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                  <Tag className="w-4 h-4 text-cyan-400" />
                  <span>Group Memory Tags & Consent Settings</span>
                </h3>
                <p className="text-xs text-slate-300 font-serif leading-relaxed">
                  In-world character tags operate independently from real-person profile tags. A real photo is never used as source material for fantasy art unless explicitly permitted.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                    <span className="font-bold text-slate-200 text-sm block">In-World Character Tagging</span>
                    <p className="text-[11px] font-serif text-slate-400">
                      Allows your Aspect identity to be tagged in multi-player Chronicle paintings.
                    </p>
                    <span className="inline-block px-2.5 py-1 rounded bg-emerald-950 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold">
                      {profile.consent.allow_character_tagging ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                    <span className="font-bold text-slate-200 text-sm block">Real-Person Group Tagging</span>
                    <p className="text-[11px] font-serif text-slate-400">
                      Allows friends to see your real profile photo on group memory pages.
                    </p>
                    <span className="inline-block px-2.5 py-1 rounded bg-indigo-950 text-indigo-300 border border-indigo-500/30 text-[10px] font-bold">
                      {profile.consent.allow_real_person_tagging ? 'Opted In' : 'Excluded (Default)'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
