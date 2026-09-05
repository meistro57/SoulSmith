// frontend/src/components/WorldAtlasView.tsx
import React, { useCallback, useEffect, useState } from 'react';
import type { VisualEntityVersion, WorldCandidateStatus, WorldEntityType, WorldVisualCandidate } from '../types';
import { apiClient, resolveAssetUrl } from '../lib/api';
import { Globe, MapPin, Gem, Sparkles, RefreshCw, CheckCircle2, XCircle, History } from 'lucide-react';

const ENTITY_LABELS: Record<WorldEntityType, string> = {
  location: 'Locations',
  relic: 'Relics',
  phenomenon: 'Phenomena',
};

const ENTITY_ICONS: Record<WorldEntityType, React.ReactNode> = {
  location: <MapPin size={16} className="text-cyan-400" />,
  relic: <Gem size={16} className="text-amber-400" />,
  phenomenon: <Sparkles size={16} className="text-purple-400" />,
};

function statusBadge(status: WorldCandidateStatus) {
  switch (status) {
    case 'pending': return <span className="px-2 py-0.5 rounded-full bg-amber-500/20 border border-amber-500/40 text-amber-300 text-[10px] font-bold">Pending</span>;
    case 'generated': return <span className="px-2 py-0.5 rounded-full bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 text-[10px] font-bold">Generated</span>;
    case 'approved': return <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-[10px] font-bold">Approved</span>;
    case 'rejected': return <span className="px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-400 text-[10px] font-bold">Rejected</span>;
    case 'failed': return <span className="px-2 py-0.5 rounded-full bg-rose-500/20 border border-rose-500/40 text-rose-300 text-[10px] font-bold">Failed</span>;
  }
}

export const WorldAtlasView: React.FC = () => {
  const [entityType, setEntityType] = useState<WorldEntityType>('location');
  const [entityId, setEntityId] = useState('hall_of_echoes');
  const [name, setName] = useState('The Hall of Echoes');
  const [generationType, setGenerationType] = useState('initial');
  const [sourceVersionId, setSourceVersionId] = useState('');
  const [stateJson, setStateJson] = useState('{\n  "architecture": "vast subterranean limestone hall",\n  "landmarks": ["seven black arches", "central dais"]\n}');
  const [versions, setVersions] = useState<VisualEntityVersion[]>([]);
  const [candidates, setCandidates] = useState<WorldVisualCandidate[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (type: WorldEntityType, id: string) => {
    if (!id) return;
    try {
      const [v, c] = await Promise.all([
        apiClient.listWorldVisualVersions(type, id),
        apiClient.listWorldVisualCandidates(type, id),
      ]);
      setVersions(v.versions);
      setCandidates(c.candidates);
    } catch (err) {
      console.error('Failed to load world visuals:', err);
    }
  }, []);

  useEffect(() => {
    load(entityType, entityId);
  }, [entityType, entityId, load]);

  const handleCreate = async () => {
    setBusy(true);
    setError(null);
    try {
      let canonicalState: Record<string, any>;
      try {
        canonicalState = JSON.parse(stateJson);
      } catch {
        setError('Canonical state must be valid JSON.');
        setBusy(false);
        return;
      }
      await apiClient.createWorldVisualCandidate({
        entity_type: entityType,
        entity_id: entityId,
        name,
        canonical_state: canonicalState,
        generation_type: generationType,
        source_visual_version_id: sourceVersionId || undefined,
      });
      await load(entityType, entityId);
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  };

  const handleGenerate = async (candidateId: string) => {
    setBusy(true);
    setError(null);
    try {
      await apiClient.generateWorldVisualCandidate(candidateId);
      await load(entityType, entityId);
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  };

  const handleApprove = async (candidateId: string) => {
    setBusy(true);
    setError(null);
    try {
      await apiClient.approveWorldVisualCandidate(candidateId);
      await load(entityType, entityId);
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  };

  const handleReject = async (candidateId: string) => {
    setBusy(true);
    setError(null);
    try {
      await apiClient.rejectWorldVisualCandidate(candidateId);
      await load(entityType, entityId);
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 p-4 font-mono text-xs">
      <div className="p-6 rounded-3xl bg-slate-900/90 border border-cyan-500/30 shadow-2xl">
        <h2 className="text-2xl font-bold text-slate-100 font-serif flex items-center gap-3">
          <Globe size={26} className="text-cyan-400" />
          <span>Visual World Atlas</span>
        </h2>
        <p className="text-slate-400 text-xs mt-2 max-w-2xl leading-relaxed">
          The image represents the world. It never defines it. Approved visuals are immutable historical versions.
        </p>
      </div>

      {/* Entity type tabs */}
      <div className="flex flex-wrap gap-2">
        {(Object.keys(ENTITY_LABELS) as WorldEntityType[]).map((t) => (
          <button
            key={t}
            onClick={() => { setEntityType(t); }}
            className={`px-4 py-2 rounded-xl flex items-center gap-2 font-bold cursor-pointer transition ${
              entityType === t ? 'bg-cyan-500/20 border border-cyan-500/40 text-cyan-300' : 'bg-slate-900 border border-slate-800 text-slate-400'
            }`}
          >
            {ENTITY_ICONS[t]}
            <span>{ENTITY_LABELS[t]}</span>
          </button>
        ))}
      </div>

      {/* Create form */}
      <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-3">
        <h3 className="text-sm font-bold text-slate-100">Create {ENTITY_LABELS[entityType].slice(0, -1)} Visual</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <label className="space-y-1">
            <span className="text-slate-500 text-[10px] block">ENTITY ID</span>
            <input value={entityId} onChange={(e) => setEntityId(e.target.value)} className="w-full p-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-200" />
          </label>
          <label className="space-y-1">
            <span className="text-slate-500 text-[10px] block">NAME</span>
            <input value={name} onChange={(e) => setName(e.target.value)} className="w-full p-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-200" />
          </label>
          <label className="space-y-1">
            <span className="text-slate-500 text-[10px] block">GENERATION TYPE</span>
            <select value={generationType} onChange={(e) => setGenerationType(e.target.value)} className="w-full p-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-200">
              <option value="initial">initial</option>
              <option value="state_update">state_update</option>
              <option value="damage_update">damage_update</option>
              <option value="restoration">restoration</option>
              <option value="magical_transformation">magical_transformation</option>
              <option value="manual_regeneration">manual_regeneration</option>
            </select>
          </label>
        </div>
        <label className="space-y-1 block">
          <span className="text-slate-500 text-[10px] block">SOURCE VISUAL VERSION ID (optional)</span>
          <input value={sourceVersionId} onChange={(e) => setSourceVersionId(e.target.value)} className="w-full p-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-200" placeholder="wvv_1_xxxxxxxx" />
        </label>
        <label className="space-y-1 block">
          <span className="text-slate-500 text-[10px] block">CANONICAL STATE (JSON)</span>
          <textarea value={stateJson} onChange={(e) => setStateJson(e.target.value)} rows={5} className="w-full p-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-200 font-mono" />
        </label>
        {error && <div className="p-2 rounded-lg bg-rose-950/50 border border-rose-500/40 text-rose-300 text-[10px]">{error}</div>}
        <button onClick={handleCreate} disabled={busy} className="py-2 px-4 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold flex items-center gap-2 cursor-pointer">
          <RefreshCw size={14} className={busy ? 'animate-spin' : ''} />
          <span>Create Candidate</span>
        </button>
      </div>

      {/* Versions */}
      <div className="space-y-2">
        <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2"><History size={16} className="text-purple-400" /> Visual Timeline ({versions.length})</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
          {versions.map((v) => (
            <div key={v.version_id} className="p-3 rounded-xl bg-slate-900/90 border border-purple-500/30 space-y-2">
              <img src={resolveAssetUrl(v.image_url)} alt={v.label} className="w-full aspect-square object-cover rounded-lg border border-slate-800" />
              <div className="text-[10px] text-slate-300">
                <div className="font-bold text-purple-300">v{v.version_number}</div>
                <div className="truncate">{v.label}</div>
              </div>
            </div>
          ))}
          {versions.length === 0 && <div className="text-slate-500 text-[11px] col-span-full">No approved visuals yet.</div>}
        </div>
      </div>

      {/* Candidates */}
      <div className="space-y-2">
        <h3 className="text-sm font-bold text-slate-100">Candidates ({candidates.length})</h3>
        {candidates.map((c) => (
          <div key={c.candidate_id} className="p-4 rounded-xl bg-slate-900/90 border border-cyan-500/30 space-y-3">
            <div className="flex justify-between items-start">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-slate-100">{c.candidate_id}</span>
                  {statusBadge(c.status)}
                </div>
                <div className="text-[10px] text-slate-500">
                  {c.generation_type.replace('_', ' ').toUpperCase()} · {c.workflow_role} · provider {c.provider} · seed {c.generation_seed ?? 'N/A'}
                </div>
                {c.source_visual_version_id && (
                  <div className="text-[10px] text-amber-300">Based on {c.source_visual_version_id}</div>
                )}
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 items-start">
              {c.reference_image_url && (
                <div>
                  <span className="text-slate-500 text-[10px] block mb-1">SOURCE</span>
                  <img src={resolveAssetUrl(c.reference_image_url)} alt="source" className="w-32 h-32 object-cover rounded-lg border border-amber-500/40" />
                </div>
              )}
              {c.generated_image_url ? (
                <div>
                  <span className="text-slate-500 text-[10px] block mb-1">CANDIDATE</span>
                  <img src={resolveAssetUrl(c.generated_image_url)} alt="candidate" className="w-32 h-32 object-cover rounded-lg border border-cyan-500/40" />
                </div>
              ) : (
                <div className="text-slate-500 text-[11px]">No image generated yet.</div>
              )}
            </div>
            {c.failure_reason && <div className="p-2 rounded-lg bg-rose-950/50 border border-rose-500/40 text-rose-300 text-[10px]">{c.failure_reason}</div>}
            <div className="flex flex-wrap gap-2">
              {c.status === 'pending' && (
                <button onClick={() => handleGenerate(c.candidate_id)} disabled={busy} className="py-1.5 px-3 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-[11px] cursor-pointer">Generate</button>
              )}
              {c.status === 'generated' && (
                <>
                  <button onClick={() => handleApprove(c.candidate_id)} disabled={busy} className="py-1.5 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-[11px] flex items-center gap-1 cursor-pointer"><CheckCircle2 size={12} /> Approve</button>
                  <button onClick={() => handleReject(c.candidate_id)} disabled={busy} className="py-1.5 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-[11px] flex items-center gap-1 cursor-pointer"><XCircle size={12} /> Reject</button>
                </>
              )}
            </div>
          </div>
        ))}
        {candidates.length === 0 && <div className="text-slate-500 text-[11px]">No candidates yet.</div>}
      </div>
    </div>
  );
};
