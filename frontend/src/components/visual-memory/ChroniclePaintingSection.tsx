// frontend/src/components/visual-memory/ChroniclePaintingSection.tsx
import React, { useCallback, useEffect, useState } from 'react';
import type { ChroniclePainting, MemoryObject } from '../../types';
import { apiClient, resolveAssetUrl } from '../../lib/api';
import {
  CheckCircle2,
  Paintbrush,
  RefreshCw,
  ShieldAlert,
  XCircle,
} from 'lucide-react';

interface ChroniclePaintingSectionProps {
  memoryObject: MemoryObject;
}

const statusBadge = (painting: ChroniclePainting) => {
  switch (painting.status) {
    case 'approved':
      return <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-bold text-[10px]">Approved</span>;
    case 'superseded':
      return <span className="px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-400 text-[10px]">Superseded</span>;
    case 'rejected':
      return <span className="px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-400 text-[10px]">Rejected</span>;
    case 'failed':
      return <span className="px-2 py-0.5 rounded-full bg-rose-500/20 border border-rose-500/40 text-rose-300 text-[10px]">Failed</span>;
    default:
      return <span className="px-2 py-0.5 rounded-full bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 font-bold text-[10px]">Candidate</span>;
  }
};

export const ChroniclePaintingSection: React.FC<ChroniclePaintingSectionProps> = ({ memoryObject }) => {
  const [paintings, setPaintings] = useState<ChroniclePainting[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [busy, setBusy] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await apiClient.listChroniclePaintings(memoryObject.id);
      setPaintings(data.paintings);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load paintings');
    } finally {
      setLoading(false);
    }
  }, [memoryObject.id]);

  useEffect(() => {
    load();
  }, [load]);

  const paintThisMemory = async () => {
    setBusy(true);
    setError(null);
    try {
      const created = await apiClient.createChroniclePainting({
        memory_object_id: memoryObject.id,
        generation_type: 'initial',
      });
      await apiClient.generateChroniclePainting(created.painting.painting_id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Painting generation failed');
    } finally {
      setBusy(false);
    }
  };

  const act = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    setError(null);
    try {
      await fn();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Action failed');
    } finally {
      setBusy(false);
    }
  };

  const regenerate = async (painting: ChroniclePainting) => {
    setBusy(true);
    setError(null);
    try {
      const created = await apiClient.createChroniclePainting({
        memory_object_id: memoryObject.id,
        generation_type: 'manual_regeneration',
        source_painting_id: painting.painting_id,
      });
      await apiClient.generateChroniclePainting(created.painting.painting_id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Regeneration failed');
    } finally {
      setBusy(false);
    }
  };

  const approved = paintings.find((p) => p.status === 'approved');

  return (
    <div className="rounded-2xl bg-slate-900/70 border border-indigo-500/20 p-4 space-y-3 font-mono text-xs">
      <div className="flex items-center justify-between border-b border-indigo-500/20 pb-2">
        <h5 className="font-bold text-slate-200 text-xs flex items-center gap-2">
          <Paintbrush size={14} className="text-indigo-400" />
          <span>Chronicle Painting</span>
        </h5>
        <span className="text-[10px] text-slate-500">CANON → SCENE → IMAGE → GUARDIAN → CANDIDATE</span>
      </div>

      {error && (
        <div className="p-2 rounded-lg bg-rose-950/50 border border-rose-500/40 text-rose-300 text-[10px]">{error}</div>
      )}

      {approved && approved.image_url && (
        <div className="rounded-xl overflow-hidden border border-emerald-500/40 bg-slate-950 max-w-[360px]">
          <img
            src={resolveAssetUrl(approved.image_url)}
            alt={`${memoryObject.event_title} painting`}
            className="w-full h-auto object-cover"
          />
          <div className="p-1.5 text-[9px] text-emerald-300 text-center">Approved interpretation</div>
        </div>
      )}

      <button
        onClick={paintThisMemory}
        disabled={busy}
        className="py-2 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center gap-1.5 transition cursor-pointer disabled:opacity-50"
      >
        <Paintbrush size={14} className={busy ? 'animate-spin' : ''} />
        <span>{busy ? 'Working...' : 'Paint This Memory'}</span>
      </button>

      {loading ? (
        <div className="text-slate-500 text-[10px] flex items-center gap-2">
          <RefreshCw size={12} className="animate-spin" /> Loading painting history...
        </div>
      ) : paintings.length === 0 ? (
        <div className="text-slate-500 text-[10px]">No painting attempts yet.</div>
      ) : (
        <div className="space-y-2">
          {paintings.map((p) => (
            <div
              key={p.painting_id}
              className={`p-3 rounded-xl border ${
                p.status === 'approved'
                  ? 'bg-emerald-950/20 border-emerald-500/30'
                  : p.status === 'failed' || p.status === 'rejected'
                    ? 'bg-slate-950/80 border-slate-800 opacity-80'
                    : 'bg-slate-950/60 border-slate-800'
              }`}
            >
              <div className="flex justify-between items-start gap-2">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-100 text-[11px]">{p.painting_id}</span>
                    {statusBadge(p)}
                  </div>
                  <p className="text-[10px] text-slate-500">
                    {p.generation_type.replace('_', ' ').toUpperCase()} · {p.composition} · {p.provider}/{p.provider_model}
                  </p>
                  {p.created_at && (
                    <p className="text-[10px] text-slate-600">Generated {new Date(p.created_at).toLocaleString()}</p>
                  )}
                  <p className="text-[10px] text-slate-500">
                    Guardian: <strong className="text-purple-300">{p.guardian_status}</strong>
                    {p.guardian_report ? ` (${p.guardian_report.status})` : ''}
                  </p>
                  {p.source_painting_id && (
                    <p className="text-[10px] text-amber-300">Source: {p.source_painting_id}</p>
                  )}
                  {p.failure_reason && (
                    <p className="text-[10px] text-rose-300 flex items-start gap-1">
                      <ShieldAlert size={12} className="shrink-0 mt-0.5" /> {p.failure_reason}
                    </p>
                  )}
                </div>
                {p.image_url && (
                  <img
                    src={resolveAssetUrl(p.image_url)}
                    alt="Painting"
                    className="w-16 h-16 object-cover rounded-lg border border-slate-700"
                  />
                )}
              </div>

              <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-800">
                {p.status === 'candidate' && (
                  <>
                    <button
                      onClick={() => act(() => apiClient.approveChroniclePainting(p.painting_id))}
                      disabled={busy}
                      className="py-1.5 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-[10px] flex items-center gap-1 cursor-pointer disabled:opacity-50"
                    >
                      <CheckCircle2 size={12} /> Approve
                    </button>
                    <button
                      onClick={() => act(() => apiClient.rejectChroniclePainting(p.painting_id))}
                      disabled={busy}
                      className="py-1.5 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-[10px] flex items-center gap-1 cursor-pointer disabled:opacity-50"
                    >
                      <XCircle size={12} /> Reject
                    </button>
                  </>
                )}
                <button
                  onClick={() => regenerate(p)}
                  disabled={busy}
                  className="py-1.5 px-3 rounded-lg bg-indigo-700 hover:bg-indigo-600 text-white font-bold text-[10px] flex items-center gap-1 cursor-pointer disabled:opacity-50"
                >
                  <RefreshCw size={12} /> Reinterpret
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
