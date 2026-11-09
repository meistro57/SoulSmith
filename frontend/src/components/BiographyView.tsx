// frontend/src/components/BiographyView.tsx
import React, { useCallback, useEffect, useState } from 'react';
import type { Biography, BiographySection } from '../types';
import { apiClient, resolveAssetUrl } from '../lib/api';
import { BookOpen, ChevronDown, History, RefreshCw, ScrollText, ShieldCheck } from 'lucide-react';

interface BiographyViewProps {
  soulName: string;
}

const CLAIM_LABELS: Record<string, string> = {
  canonical_fact: 'Canonical fact',
  participant_perspective: 'Participant perspective',
  shared_perspective: 'Shared perspective',
  inferred_theme: 'Inferred theme',
  narrative_connective: 'Narrative connective',
  unresolved: 'Unresolved',
};

/**
 * Living Biography: a story assembled from canonical Chronicle records, with
 * provenance available on demand. The biography grows with the Chronicle; it
 * never writes back into it.
 */
export const BiographyView: React.FC<BiographyViewProps> = ({ soulName }) => {
  const [biography, setBiography] = useState<Biography | null>(null);
  const [history, setHistory] = useState<Biography[]>([]);
  const [loading, setLoading] = useState(true);
  const [compiling, setCompiling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const current = await apiClient.getCurrentBiography(soulName, soulName);
      setBiography(current.biography);
    } catch {
      setBiography(null);
    }
    try {
      const hist = await apiClient.listBiographyHistory(soulName);
      setHistory(hist.biographies);
    } catch {
      setHistory([]);
    } finally {
      setLoading(false);
    }
  }, [soulName]);

  useEffect(() => {
    load();
  }, [load]);

  const handleCompile = async () => {
    setCompiling(true);
    setNotice(null);
    setError(null);
    try {
      const result = await apiClient.compileBiography({
        soul_id: soulName,
        viewer_soul_id: soulName,
        visibility: 'public_canon',
      });
      setBiography(result.biography);
      setNotice(
        result.guardian_report.status === 'pass'
          ? 'Biography compiled and ready for review.'
          : 'Biography compilation failed Guardian review. Canon was untouched.',
      );
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to compile biography.');
    } finally {
      setCompiling(false);
    }
  };

  const handleApprove = async () => {
    if (!biography) return;
    try {
      await apiClient.approveBiography(biography.biography_id, soulName);
      setNotice('Biography approved as the current story.');
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to approve biography.');
    }
  };

  const handleReject = async () => {
    if (!biography) return;
    try {
      await apiClient.rejectBiography(biography.biography_id, soulName);
      setNotice('Biography rejected. Canonical Chronicle was untouched.');
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to reject biography.');
    }
  };

  const toggle = (sectionId: string) =>
    setExpanded((prev) => ({ ...prev, [sectionId]: !prev[sectionId] }));

  return (
    <div className="space-y-5">
      <div className="mythic-card p-6 md:p-8">
        <span className="eyebrow flex items-center gap-1.5">
          <BookOpen size={14} /> Living Biography
        </span>
        <h2 className="text-2xl font-bold font-cinzel text-[var(--gold)] mt-1">
          The Story the Memories Support
        </h2>
        <p className="text-sm text-[var(--parchment)] opacity-75 mt-2 max-w-2xl">
          Assembled from canonical Chronicle records, shared events, relationships,
          StoryMarks, places, relics, consequences, and approved artwork. Every
          claim stays traceable to its source; the Chronicle remains the truth.
        </p>

        <div className="flex flex-wrap items-center gap-3 mt-5">
          <button
            onClick={handleCompile}
            disabled={compiling}
            className={`btn-gold text-xs py-2 px-5 ${compiling ? 'opacity-50 animate-pulse' : ''}`}
          >
            <RefreshCw size={14} className="inline mr-1.5" />
            {compiling ? 'Compiling...' : 'Compile / Regenerate'}
          </button>
          {biography && biography.status === 'draft' && (
            <>
              <button onClick={handleApprove} className="mythic-pill border-emerald-500/40 text-emerald-300 text-xs py-2 px-4">
                <ShieldCheck size={14} className="inline mr-1.5" /> Make Current
              </button>
              <button onClick={handleReject} className="mythic-pill border-rose-500/40 text-rose-300 text-xs py-2 px-4">
                Reject Draft
              </button>
            </>
          )}
        </div>

        {notice && <p className="text-xs text-emerald-300 mt-3 font-mono">{notice}</p>}
        {error && <p className="text-xs text-rose-300 mt-3 font-mono">{error}</p>}
      </div>

      {loading && (
        <div className="rounded-2xl bg-slate-900/70 border border-slate-800 p-4 text-slate-500 text-xs font-mono">
          Reading the Chronicle...
        </div>
      )}

      {!loading && !biography && (
        <div className="rounded-2xl bg-slate-900/70 border border-slate-800 p-6 text-slate-400 text-sm font-mono">
          No biography yet. Compile one from the Chronicle to begin reading the
          life it can support.
        </div>
      )}

      {!loading && biography && (
        <div className="space-y-4">
          <div className="mythic-card p-6 md:p-8 border border-[var(--line)]">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-mono text-[var(--spark)] uppercase tracking-wider">
                  Version {biography.version_number} · {biography.status}
                </p>
                <h3 className="text-3xl font-bold font-cinzel text-[var(--gold-bright)] mt-1">
                  {biography.title}
                </h3>
                {biography.current_chapter && (
                  <p className="text-sm text-[var(--parchment)] opacity-80 italic mt-1">
                    Current chapter: {biography.current_chapter}
                  </p>
                )}
              </div>
              <div className="text-right text-xs font-mono text-slate-400">
                <p>compiler {biography.compiler_version}</p>
                <p>provider {biography.provider_model ?? biography.provider}</p>
                <p>guardian {biography.guardian_status}</p>
              </div>
            </div>
          </div>

          {biography.sections.map((section) => (
            <BiographySectionCard
              key={section.section_id}
              section={section}
              expanded={!!expanded[section.section_id]}
              onToggle={() => toggle(section.section_id)}
              biographyId={biography.biography_id}
              soulName={soulName}
            />
          ))}

          {history.length > 1 && (
            <div className="rounded-2xl bg-slate-900/70 border border-slate-800 p-4 font-mono text-xs text-slate-400">
              <span className="flex items-center gap-1.5 text-slate-300 font-bold">
                <History size={14} /> Previous versions
              </span>
              <ul className="mt-2 space-y-1">
                {history
                  .filter((b) => b.biography_id !== biography.biography_id)
                  .map((b) => (
                    <li key={b.biography_id}>
                      v{b.version_number} · {b.status} · {b.title}
                    </li>
                  ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

interface BiographySectionCardProps {
  section: BiographySection;
  expanded: boolean;
  onToggle: () => void;
  biographyId: string;
  soulName: string;
}

const BiographySectionCard: React.FC<BiographySectionCardProps> = ({
  section,
  expanded,
  onToggle,
  biographyId,
  soulName,
}) => {
  const [provenance, setProvenance] = useState<BiographySection['provenance'] | null>(null);

  useEffect(() => {
    if (!expanded || provenance !== null) return;
    apiClient
      .getBiographySectionProvenance(biographyId, section.section_id, soulName)
      .then((res) => setProvenance(res.provenance))
      .catch(() => setProvenance([]));
  }, [expanded, provenance, biographyId, section.section_id, soulName]);

  return (
    <div className="rounded-2xl bg-slate-900/70 border border-[var(--line)] overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between gap-3 p-4 text-left hover:bg-slate-900/40 transition"
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <ScrollText size={16} className="text-[var(--gold)] shrink-0" />
          <div className="min-w-0">
            <h4 className="font-cinzel font-bold text-[var(--gold)] text-sm truncate">{section.title}</h4>
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
              {CLAIM_LABELS[section.claim_kind] ?? section.claim_kind}
              {section.perspective_of ? ` · ${section.perspective_of}` : ''}
            </span>
          </div>
        </div>
        <ChevronDown size={16} className={`text-slate-500 transition-transform ${expanded ? 'rotate-180' : ''}`} />
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-3">
          {section.visual_reference && (
            <img
              src={resolveAssetUrl(section.visual_reference)}
              alt={section.title}
              className="rounded-xl max-h-64 w-full object-cover border border-slate-800"
            />
          )}
          <p className="text-sm text-[var(--parchment)] opacity-90 font-serif leading-relaxed">
            {section.narrative}
          </p>
          <div className="border-t border-slate-800 pt-2">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
              From the Chronicle
            </span>
            <ul className="mt-1.5 space-y-1">
              {(provenance ?? section.provenance).map((ref, idx) => (
                <li key={`${ref.source_type}:${ref.source_id}:${idx}`} className="text-[10px] font-mono text-slate-400">
                  <span className="text-cyan-400">{ref.source_type}</span> · {ref.source_id}
                  {ref.note ? ` · ${ref.note}` : ''}
                </li>
              ))}
              {!provenance && section.provenance.length === 0 && (
                <li className="text-[10px] font-mono text-slate-500">No canonical source for this passage.</li>
              )}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};
