import React, { useEffect, useMemo, useState } from 'react';
import { Image, Landmark, Loader2, Users, ScrollText, HeartHandshake, BookOpen, X } from 'lucide-react';
import type { GalleryArtifact } from '../types';
import { apiClient, resolveAssetUrl } from '../lib/api';

type GalleryMode = 'all' | 'world' | 'people' | 'chronicle' | 'shared' | 'life';

const MODES: Array<{ id: GalleryMode; label: string; icon: typeof Image }> = [
  { id: 'all', label: 'The Gallery', icon: Image },
  { id: 'world', label: 'The World', icon: Landmark },
  { id: 'people', label: 'The People', icon: Users },
  { id: 'chronicle', label: 'The Chronicle', icon: ScrollText },
  { id: 'shared', label: 'Shared Moments', icon: HeartHandshake },
  { id: 'life', label: 'A Life', icon: BookOpen },
];

interface WorldGalleryViewProps {
  soulName: string;
}

export const WorldGalleryView: React.FC<WorldGalleryViewProps> = ({ soulName }) => {
  const [mode, setMode] = useState<GalleryMode>('all');
  const [artifacts, setArtifacts] = useState<GalleryArtifact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<GalleryArtifact | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    const params: Record<string, string> = { mode };
    if (mode === 'life') {
      params.entity_id = soulName;
    }
    apiClient
      .listGalleryArtifacts(params)
      .then((res) => {
        if (!cancelled) setArtifacts(res.artifacts);
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [mode, soulName]);

  useEffect(() => {
    if (!selected) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setSelected(null);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [selected]);

  const activeMode = useMemo(() => MODES.find((m) => m.id === mode) ?? MODES[0], [mode]);

  return (
    <div className="space-y-6">
      <div className="mythic-card p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="eyebrow flex items-center gap-1.5">
              <Landmark size={14} /> World Gallery
            </span>
            <h2 className="text-2xl font-bold font-cinzel text-[var(--gold)]">The Visual Memory of a World</h2>
            <p className="text-xs font-body text-[var(--parchment)] opacity-75 max-w-2xl">
              Approved portraits, world visuals, Chronicle paintings, shared moments, and biography illustrations, curated with consent and never used to rewrite history.
            </p>
          </div>
          <span className="mythic-pill flex items-center gap-1.5 w-fit">
            <Image size={12} /> {artifacts.length} artifact{artifacts.length === 1 ? '' : 's'}
          </span>
        </div>
      </div>

      <nav aria-label="Gallery modes" className="flex flex-wrap gap-2">
        {MODES.map((m) => {
          const Icon = m.icon;
          const active = m.id === mode;
          return (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              aria-pressed={active}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono tracking-wider transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--gold)] ${
                active
                  ? 'bg-[var(--gold)] text-[var(--void)] font-bold'
                  : 'bg-[var(--deep)] text-[var(--parchment)] opacity-80 hover:opacity-100 border border-[var(--line)]'
              }`}
            >
              <Icon size={14} />
              <span>{m.label}</span>
            </button>
          );
        })}
      </nav>

      {loading && (
        <div className="flex items-center justify-center py-20 text-[var(--parchment)] opacity-70 gap-2">
          <Loader2 size={18} className="animate-spin" /> Loading the gallery…
        </div>
      )}

      {!loading && error && (
        <div className="mythic-card p-6 text-center text-sm text-rose-300">{error}</div>
      )}

      {!loading && !error && artifacts.length === 0 && (
        <div className="mythic-card p-10 text-center text-sm text-[var(--parchment)] opacity-75">
          No approved artifacts for {activeMode.label} yet. This room of the museum is still waiting for its first memory.
        </div>
      )}

      {!loading && !error && artifacts.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {artifacts.map((art) => (
            <button
              key={`${art.artifact_type}-${art.artifact_id}`}
              onClick={() => setSelected(art)}
              className="mythic-card overflow-hidden text-left group focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--gold)] transition-all duration-300 hover:border-[var(--spark)] flex flex-col"
            >
              <div className="relative h-52 overflow-hidden bg-[var(--void)]">
                <img
                  src={resolveAssetUrl(art.image_url)}
                  alt={art.alt_text}
                  loading="lazy"
                  className="w-full h-full object-cover transition duration-500 group-hover:scale-105 motion-reduce:transform-none"
                />
                <span className="absolute top-3 left-3 mythic-pill text-[10px]">{art.artifact_type.replace('_', ' ')}</span>
              </div>
              <div className="p-4 space-y-1.5 flex-1">
                <h3 className="text-base font-bold font-cinzel text-[var(--gold)] leading-snug">{art.title}</h3>
                <p className="text-xs font-body text-[var(--parchment)] opacity-75 leading-relaxed">{art.caption}</p>
                {art.guardian_status && (
                  <p className="text-[10px] font-mono text-[var(--spark)] uppercase tracking-wider">
                    Guardian: {art.guardian_status}
                  </p>
                )}
              </div>
            </button>
          ))}
        </div>
      )}

      {selected && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#070A12]/95 backdrop-blur-md"
          onClick={() => setSelected(null)}
          role="dialog"
          aria-modal="true"
          aria-label={selected.title}
        >
          <div className="mythic-card max-w-5xl w-full p-4 space-y-4 relative max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-start gap-3">
              <div>
                <span className="text-xs font-mono text-[var(--spark)]">{selected.artifact_type.replace('_', ' ')}</span>
                <h3 className="text-xl font-bold font-cinzel text-[var(--gold)]">{selected.title}</h3>
              </div>
              <button
                onClick={() => setSelected(null)}
                className="btn-glass text-xs flex items-center gap-1.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--gold)]"
                aria-label="Close"
              >
                <X size={14} /> Close
              </button>
            </div>

            <div className="rounded-xl overflow-hidden bg-[var(--void)] border border-[var(--line)] flex items-center justify-center p-2">
              <img src={resolveAssetUrl(selected.image_url)} alt={selected.alt_text} className="max-h-[65vh] w-auto object-contain" />
            </div>

            <p className="text-xs font-body text-[var(--parchment)] italic opacity-85">{selected.caption}</p>

            {selected.provenance.length > 0 && (
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-[var(--spark)]">Provenance</span>
                <ul className="text-xs font-body text-[var(--parchment)] opacity-75 list-disc pl-5 mt-1 space-y-0.5">
                  {selected.provenance.map((p) => (
                    <li key={`${p.source_type}-${p.source_id}`}>{p.label}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
