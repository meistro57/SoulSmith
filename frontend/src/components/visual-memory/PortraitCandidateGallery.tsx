// frontend/src/components/visual-memory/PortraitCandidateGallery.tsx
import React, { useState } from 'react';
import type { GenerationType, PortraitGenerationCandidate, PortraitVersion } from '../../types';
import { PortraitCandidateCard } from './PortraitCandidateCard';
import { Camera, Plus, Sparkles } from 'lucide-react';

interface PortraitCandidateGalleryProps {
  candidates: PortraitGenerationCandidate[];
  portraitVersions: PortraitVersion[];
  onCreateCandidate: (payload: { generation_type: GenerationType; source_portrait_version_id?: string }) => Promise<void>;
  onGenerateCandidate: (candidateId: string) => Promise<void>;
  onApproveCandidate: (candidateId: string) => Promise<void>;
  onRejectCandidate: (candidateId: string) => Promise<void>;
}

export const PortraitCandidateGallery: React.FC<PortraitCandidateGalleryProps> = ({
  candidates,
  portraitVersions,
  onCreateCandidate,
  onGenerateCandidate,
  onApproveCandidate,
  onRejectCandidate,
}) => {
  const [genType, setGenType] = useState<GenerationType>('initial');
  const [sourceVersionId, setSourceVersionId] = useState<string>('');
  const [creating, setCreating] = useState<boolean>(false);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await onCreateCandidate({
        generation_type: genType,
        source_portrait_version_id: sourceVersionId || undefined,
      });
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-6 font-mono text-xs">
      {/* Create Candidate Form */}
      <form onSubmit={handleCreate} className="p-6 rounded-2xl bg-slate-900/90 border border-cyan-500/30 space-y-4 shadow-xl">
        <div className="flex justify-between items-center border-b border-cyan-500/20 pb-3">
          <h3 className="font-bold text-slate-100 text-sm flex items-center gap-2">
            <Sparkles size={16} className="text-cyan-400" />
            <span>Compile New Portrait Candidate Request</span>
          </h3>
          <span className="text-[10px] text-cyan-400">Phase 10 Continuity Workflow</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-slate-400 text-[10px] mb-1">Generation Type</label>
            <select
              value={genType}
              onChange={(e) => setGenType(e.target.value as GenerationType)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 text-[11px]"
            >
              <option value="initial">Initial Portrait</option>
              <option value="story_mark_update">Story Mark / Scar Update</option>
              <option value="equipment_update">Equipment Change</option>
              <option value="age_update">Age Evolution</option>
              <option value="manual_regeneration">Manual Variation</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-400 text-[10px] mb-1">Baseline Reference Version (Optional)</label>
            <select
              value={sourceVersionId}
              onChange={(e) => setSourceVersionId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 text-[11px]"
            >
              <option value="">None (Initial Baseline)</option>
              {portraitVersions.map((v) => (
                <option key={v.version_id} value={v.version_id}>
                  v{v.version_number} - {v.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={creating}
          className="w-full py-2.5 px-4 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs transition cursor-pointer flex items-center justify-center gap-1.5"
        >
          <Plus size={14} />
          <span>{creating ? 'Compiling Candidate...' : 'Compile & Register Candidate Request'}</span>
        </button>
      </form>

      {/* Candidate List */}
      <div className="space-y-4">
        <h3 className="font-bold text-slate-200 text-sm flex items-center gap-2">
          <Camera size={16} className="text-cyan-400" />
          <span>Portrait Candidate Queue & Review</span>
        </h3>

        {candidates.length === 0 ? (
          <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 text-center text-slate-500">
            No portrait candidates created yet. Click above to compile your first candidate.
          </div>
        ) : (
          candidates.map((candidate) => (
            <PortraitCandidateCard
              key={candidate.candidate_id}
              candidate={candidate}
              onGenerate={onGenerateCandidate}
              onApprove={onApproveCandidate}
              onReject={onRejectCandidate}
            />
          ))
        )}
      </div>
    </div>
  );
};
