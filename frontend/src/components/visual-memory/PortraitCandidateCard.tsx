// frontend/src/components/visual-memory/PortraitCandidateCard.tsx
import React, { useState } from 'react';
import type { PortraitGenerationCandidate } from '../../types';
import { Camera, CheckCircle2, XCircle, AlertCircle, RefreshCw, Eye } from 'lucide-react';

interface PortraitCandidateCardProps {
  candidate: PortraitGenerationCandidate;
  onGenerate: (candidateId: string) => Promise<void>;
  onApprove: (candidateId: string) => Promise<void>;
  onReject: (candidateId: string) => Promise<void>;
}

export const PortraitCandidateCard: React.FC<PortraitCandidateCardProps> = ({
  candidate,
  onGenerate,
  onApprove,
  onReject,
}) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [showPromptDetails, setShowPromptDetails] = useState<boolean>(false);

  const handleAction = async (action: () => Promise<void>) => {
    setLoading(true);
    try {
      await action();
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = () => {
    switch (candidate.status) {
      case 'pending':
        return <span className="px-2.5 py-0.5 rounded-full bg-amber-500/20 border border-amber-500/40 text-amber-300 font-bold text-[10px]">Pending Synthesis</span>;
      case 'generated':
        return <span className="px-2.5 py-0.5 rounded-full bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 font-bold text-[10px]">Generated Candidate</span>;
      case 'approved':
        return <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-bold text-[10px]">Approved (Version Created)</span>;
      case 'rejected':
        return <span className="px-2.5 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-400 text-[10px]">Rejected Candidate</span>;
      case 'failed':
        return <span className="px-2.5 py-0.5 rounded-full bg-rose-500/20 border border-rose-500/40 text-rose-300 text-[10px]">Generation Failed</span>;
    }
  };

  return (
    <div className={`p-5 rounded-2xl border ${candidate.status === 'approved' ? 'bg-emerald-950/20 border-emerald-500/30' : candidate.status === 'rejected' ? 'bg-slate-950/80 border-slate-800 opacity-70' : candidate.status === 'failed' ? 'bg-rose-950/20 border-rose-500/30' : 'bg-slate-900/90 border-cyan-500/30'} space-y-4 shadow-xl font-mono text-xs transition`}>
      <div className="flex justify-between items-start">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-100 text-sm">{candidate.candidate_id}</span>
            {getStatusBadge()}
          </div>
          <p className="text-[11px] text-purple-300">
            Type: <strong>{candidate.generation_type.replace('_', ' ').toUpperCase()}</strong>
          </p>
        </div>
        <span className="text-[10px] text-slate-500">Provider: {candidate.provider} ({candidate.provider_model})</span>
      </div>

      {/* Preview imagery */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
        <div>
          <span className="text-[10px] text-slate-500 block mb-1">CANDIDATE PORTRAIT IMAGE</span>
          {candidate.generated_image_url ? (
            <div className="relative rounded-xl overflow-hidden border border-cyan-500/40 bg-slate-950 aspect-square max-w-[220px]">
              <img
                src={candidate.generated_image_url}
                alt="Candidate Portrait"
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80';
                }}
              />
              <div className="absolute bottom-2 left-2 right-2 p-1.5 rounded bg-slate-950/80 backdrop-blur text-[9px] text-slate-300 text-center">
                Seed: {candidate.generation_seed ?? 'N/A'}
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-slate-800 bg-slate-950/50 aspect-square max-w-[220px] flex flex-col items-center justify-center p-4 text-center space-y-2">
              <Camera size={24} className="text-slate-600" />
              <span className="text-slate-500 text-[10px]">No image generated yet</span>
            </div>
          )}
        </div>

        <div className="space-y-2 text-[11px]">
          <div>
            <span className="text-slate-500 block text-[10px]">SOURCE BASELINE REFERENCE</span>
            <span className="text-slate-300 font-mono text-[10px]">{candidate.source_portrait_version_id || 'Initial Avatar (None)'}</span>
          </div>

          <div>
            <span className="text-slate-500 block text-[10px]">CANONICAL MARKS INCLUDED</span>
            {candidate.story_marks_snapshot.length === 0 ? (
              <span className="text-slate-500 text-[10px]">None</span>
            ) : (
              <div className="flex flex-wrap gap-1 mt-1">
                {candidate.story_marks_snapshot.map((m) => (
                  <span key={m.id} className="px-2 py-0.5 rounded bg-amber-950 border border-amber-500/40 text-amber-300 text-[10px]">
                    {m.mark_type} ({m.location})
                  </span>
                ))}
              </div>
            )}
          </div>

          {candidate.failure_reason && (
            <div className="p-2 rounded-lg bg-rose-950/50 border border-rose-500/40 text-rose-300 text-[10px] flex items-start gap-1">
              <AlertCircle size={14} className="shrink-0 mt-0.5" />
              <span>{candidate.failure_reason}</span>
            </div>
          )}

          <button
            onClick={() => setShowPromptDetails(!showPromptDetails)}
            className="text-[10px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1 underline cursor-pointer"
          >
            <Eye size={12} />
            <span>{showPromptDetails ? 'Hide Compiled Prompt' : 'View Compiled Prompt'}</span>
          </button>
        </div>
      </div>

      {showPromptDetails && (
        <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[10px] text-slate-300 space-y-1">
          <span className="text-purple-400 font-bold block">COMPILED PROMPT:</span>
          <p className="font-serif italic leading-relaxed text-slate-300">{candidate.compiled_prompt}</p>
          {candidate.negative_prompt && (
            <p className="text-rose-400 text-[9px]"><strong className="text-slate-500">Negative:</strong> {candidate.negative_prompt}</p>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-800">
        {candidate.status === 'pending' && (
          <button
            disabled={loading}
            onClick={() => handleAction(() => onGenerate(candidate.candidate_id))}
            className="py-2 px-4 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs flex items-center gap-1.5 transition cursor-pointer"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Synthesize Imagery</span>
          </button>
        )}

        {candidate.status === 'generated' && (
          <>
            <button
              disabled={loading}
              onClick={() => handleAction(() => onApprove(candidate.candidate_id))}
              className="py-2 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center gap-1.5 transition cursor-pointer"
            >
              <CheckCircle2 size={14} />
              <span>Approve Candidate into Canon</span>
            </button>
            <button
              disabled={loading}
              onClick={() => handleAction(() => onReject(candidate.candidate_id))}
              className="py-2 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs flex items-center gap-1.5 transition cursor-pointer"
            >
              <XCircle size={14} />
              <span>Reject Candidate</span>
            </button>
          </>
        )}

        {candidate.status === 'approved' && (
          <span className="text-emerald-400 text-[11px] font-bold flex items-center gap-1">
            <CheckCircle2 size={14} /> Approved as Portrait Version #{candidate.resulting_portrait_version_id}
          </span>
        )}

        {candidate.status === 'rejected' && (
          <span className="text-slate-500 text-[11px]">Rejected candidate preserved in audit log. Canonical character state was untouched.</span>
        )}
      </div>
    </div>
  );
};
