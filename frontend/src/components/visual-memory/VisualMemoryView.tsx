// frontend/src/components/visual-memory/VisualMemoryView.tsx
import React, { useCallback, useEffect, useState } from 'react';
import type { GenerationType, MemoryObject, PortraitGenerationCandidate, VisualAvatarProfile } from '../../types';
import { apiClient } from '../../lib/api';
import { AvatarIdentityPanel } from './AvatarIdentityPanel';
import { StoryMarksPanel } from './StoryMarksPanel';
import { PortraitCandidateGallery } from './PortraitCandidateGallery';
import { PortraitTimeline } from './PortraitTimeline';
import { MemoryObjectCard } from './MemoryObjectCard';
import { ConsentControls } from './ConsentControls';
import { Camera, Sparkles, Shield, History, Tag, Layers, RefreshCw } from 'lucide-react';

interface VisualMemoryViewProps {
  soulName: string;
}

export const VisualMemoryView: React.FC<VisualMemoryViewProps> = ({ soulName }) => {
  const [profile, setProfile] = useState<VisualAvatarProfile | null>(null);
  const [memoryObjects, setMemoryObjects] = useState<MemoryObject[]>([]);
  const [candidates, setCandidates] = useState<PortraitGenerationCandidate[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeSubTab, setActiveSubTab] = useState<'avatar' | 'candidates' | 'timeline' | 'chronicle' | 'consent'>('candidates');

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const prof = await apiClient.getVisualAvatarProfile(soulName);
      setProfile(prof);

      const memData = await apiClient.listMemoryObjects();
      setMemoryObjects(memData.memory_objects);

      const candData = await apiClient.listPortraitCandidates(soulName);
      setCandidates(candData.candidates);
    } catch (err) {
      console.error('Failed to load visual memory data:', err);
    } finally {
      setLoading(false);
    }
  }, [soulName]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleAddStoryMark = async (mark: { mark_type: string; location: string; origin_event_id: string; acquired_at: string }) => {
    try {
      await apiClient.addStoryMark({
        soul_id: soulName,
        mark_type: mark.mark_type,
        location: mark.location,
        origin_event_id: mark.origin_event_id,
        acquired_at: mark.acquired_at,
      });
      await loadData();
    } catch (err) {
      console.error('Failed to add story mark:', err);
    }
  };

  const handleCreateCandidate = async (payload: { generation_type: GenerationType; source_portrait_version_id?: string }) => {
    try {
      await apiClient.createPortraitCandidate({
        soul_id: soulName,
        generation_type: payload.generation_type,
        source_portrait_version_id: payload.source_portrait_version_id,
      });
      await loadData();
    } catch (err) {
      console.error('Failed to create candidate:', err);
    }
  };

  const handleGenerateCandidate = async (candidateId: string) => {
    try {
      await apiClient.generateCandidate(candidateId);
      await loadData();
    } catch (err) {
      console.error('Failed to generate candidate:', err);
    }
  };

  const handleApproveCandidate = async (candidateId: string) => {
    try {
      await apiClient.approveCandidate(candidateId, { soul_id: soulName });
      await loadData();
    } catch (err) {
      console.error('Failed to approve candidate:', err);
    }
  };

  const handleRejectCandidate = async (candidateId: string) => {
    try {
      await apiClient.rejectCandidate(candidateId, { soul_id: soulName });
      await loadData();
    } catch (err) {
      console.error('Failed to reject candidate:', err);
    }
  };

  if (loading && !profile) {
    return (
      <div className="flex items-center justify-center p-12 text-purple-400 font-mono text-xs gap-2">
        <RefreshCw size={16} className="animate-spin" />
        <span>Loading Visual Memory System & Portrait Candidates...</span>
      </div>
    );
  }

  if (!profile) return null;

  return (
    <div className="max-w-5xl mx-auto space-y-6 p-4">
      {/* Header Banner */}
      <div className="p-6 rounded-3xl bg-slate-900/90 border border-purple-500/30 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 p-8 text-purple-500/10 pointer-events-none">
          <Layers size={140} />
        </div>

        <div className="relative z-10 space-y-2">
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-purple-500/20 border border-purple-500/40 text-purple-300 font-mono text-[10px] font-bold tracking-widest uppercase">
              Phase 10: Portrait Generation & Continuity
            </span>
            <span className="text-slate-500 text-xs font-mono">• Games save progress. SoulSmith preserves memories.</span>
          </div>

          <h2 className="text-2xl font-bold text-slate-100 font-serif tracking-wide flex items-center gap-3">
            <Camera size={26} className="text-purple-400" />
            <span>SoulSmith Visual Memory & Candidate Workflow</span>
          </h2>

          <p className="text-slate-400 text-xs max-w-2xl leading-relaxed">
            The portrait image is not canonical history. Canonical identity, equipment, story marks, and portrait-version provenance are canonical. Generated imagery is candidate representation.
          </p>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-3 font-mono text-xs">
        <button
          onClick={() => setActiveSubTab('candidates')}
          className={`px-4 py-2 rounded-xl transition flex items-center gap-2 font-bold cursor-pointer ${
            activeSubTab === 'candidates'
              ? 'bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 shadow-lg'
              : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200'
          }`}
        >
          <Camera size={14} />
          <span>Candidate Queue ({candidates.length})</span>
        </button>

        <button
          onClick={() => setActiveSubTab('timeline')}
          className={`px-4 py-2 rounded-xl transition flex items-center gap-2 font-bold cursor-pointer ${
            activeSubTab === 'timeline'
              ? 'bg-purple-500/20 border border-purple-500/40 text-purple-300 shadow-lg'
              : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200'
          }`}
        >
          <History size={14} />
          <span>Portrait Timeline ({profile.portraits.length})</span>
        </button>

        <button
          onClick={() => setActiveSubTab('avatar')}
          className={`px-4 py-2 rounded-xl transition flex items-center gap-2 font-bold cursor-pointer ${
            activeSubTab === 'avatar'
              ? 'bg-amber-500/20 border border-amber-500/40 text-amber-300 shadow-lg'
              : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200'
          }`}
        >
          <Sparkles size={14} />
          <span>Identity & Story Marks ({profile.story_marks.length})</span>
        </button>

        <button
          onClick={() => setActiveSubTab('chronicle')}
          className={`px-4 py-2 rounded-xl transition flex items-center gap-2 font-bold cursor-pointer ${
            activeSubTab === 'chronicle'
              ? 'bg-indigo-500/20 border border-indigo-500/40 text-indigo-300 shadow-lg'
              : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200'
          }`}
        >
          <Shield size={14} />
          <span>Memory Objects ({memoryObjects.length})</span>
        </button>

        <button
          onClick={() => setActiveSubTab('consent')}
          className={`px-4 py-2 rounded-xl transition flex items-center gap-2 font-bold cursor-pointer ${
            activeSubTab === 'consent'
              ? 'bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 shadow-lg'
              : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200'
          }`}
        >
          <Tag size={14} />
          <span>Consent & Recognition</span>
        </button>
      </div>

      {/* Sub-Tab Content */}
      {activeSubTab === 'candidates' && (
        <PortraitCandidateGallery
          candidates={candidates}
          portraitVersions={profile.portraits}
          onCreateCandidate={handleCreateCandidate}
          onGenerateCandidate={handleGenerateCandidate}
          onApproveCandidate={handleApproveCandidate}
          onRejectCandidate={handleRejectCandidate}
        />
      )}

      {activeSubTab === 'timeline' && (
        <PortraitTimeline portraits={profile.portraits} />
      )}

      {activeSubTab === 'avatar' && (
        <div className="space-y-6">
          <AvatarIdentityPanel identity={profile.identity} equipment={profile.equipment} />
          <StoryMarksPanel storyMarks={profile.story_marks} onAddStoryMark={handleAddStoryMark} />
        </div>
      )}

      {activeSubTab === 'chronicle' && (
        <div className="space-y-4 font-mono text-xs">
          <h3 className="font-bold text-slate-200 text-sm flex items-center gap-2">
            <Shield size={16} className="text-indigo-400" />
            <span>Chronicle Memory Objects Ledger</span>
          </h3>
          {memoryObjects.length === 0 ? (
            <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 text-center text-slate-500">
              No memory objects compiled yet.
            </div>
          ) : (
            memoryObjects.map((memObj) => (
              <MemoryObjectCard key={memObj.id} memoryObject={memObj} />
            ))
          )}
        </div>
      )}

      {activeSubTab === 'consent' && (
        <ConsentControls consent={profile.consent} />
      )}
    </div>
  );
};
