import React, { useEffect, useMemo, useState } from 'react';
import { Landmark, Loader2, ScrollText, Sparkles, BookOpen } from 'lucide-react';
import type { LegendaryFigure, WorldMemory } from '../types';
import { apiClient } from '../lib/api';

interface WorldMemoryViewProps {
  soulName: string;
}

const MEMORY_FORMS = [
  'legend',
  'historical_account',
  'folk_tale',
  'song_ballad',
  'inscription',
  'monument_statue',
  'festival_tradition',
  'relic_legend',
  'forgotten_fragment',
];

const INTERPRETATIONS = [
  'faithful',
  'mythologized',
  'exaggerated',
  'contradictory',
  'fragmented',
  'symbolic',
];

export const WorldMemoryView: React.FC<WorldMemoryViewProps> = ({ soulName: _soulName }) => {
  const [memories, setMemories] = useState<WorldMemory[]>([]);
  const [figures, setFigures] = useState<LegendaryFigure[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [subjectType, setSubjectType] = useState('event');
  const [subjectId, setSubjectId] = useState('');
  const [culture, setCulture] = useState('');
  const [memoryForm, setMemoryForm] = useState('legend');
  const [interpretation, setInterpretation] = useState('faithful');
  const [compiling, setCompiling] = useState(false);
  const [compileMessage, setCompileMessage] = useState<string | null>(null);

  const reload = () => {
    setLoading(true);
    setError(null);
    Promise.all([apiClient.listWorldMemories(), apiClient.listLegendaryFigures()])
      .then(([mem, fig]) => {
        setMemories(mem.memories);
        setFigures(fig.figures);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    reload();
  }, []);

  const handleCompile = async () => {
    if (!subjectId.trim()) {
      setCompileMessage('Provide a subject entity ID (for example an event_id).');
      return;
    }
    setCompiling(true);
    setCompileMessage(null);
    try {
      const res = await apiClient.compileWorldMemory({
        subject_entity_type: subjectType,
        subject_entity_id: subjectId.trim(),
        culture,
        memory_form: memoryForm,
        interpretation_type: interpretation,
      });
      setCompileMessage(
        `Compiled "${res.memory.title}" (guardian: ${res.memory.guardian_status}).`
      );
      reload();
    } catch (err) {
      setCompileMessage((err as Error).message);
    } finally {
      setCompiling(false);
    }
  };

  const canonCount = useMemo(
    () => memories.filter((m) => m.interpretation_type === 'faithful').length,
    [memories]
  );
  const legendCount = useMemo(
    () => memories.filter((m) => m.interpretation_type !== 'faithful').length,
    [memories]
  );

  return (
    <div className="space-y-6">
      <div className="mythic-card p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="eyebrow flex items-center gap-1.5">
              <Landmark size={14} /> World Memory & Legends
            </span>
            <h2 className="text-2xl font-bold font-cinzel text-[var(--gold)]">What the World Carries Forward</h2>
            <p className="text-xs font-body text-[var(--parchment)] opacity-75 max-w-2xl">
              Cultural memory is derived from the Chronicle, never authoritative over it. Faithful accounts stay beside mythologized legends, each with explicit, traceable drift.
            </p>
          </div>
          <span className="mythic-pill flex items-center gap-1.5 w-fit">
            <BookOpen size={12} /> {canonCount} faithful / {legendCount} legend{legendCount === 1 ? '' : 's'}
          </span>
        </div>
      </div>

      <div className="mythic-card p-6 space-y-4">
        <span className="eyebrow flex items-center gap-1.5">
          <Sparkles size={14} /> Compile a Cultural Memory
        </span>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
          <label className="flex flex-col gap-1">
            <span className="text-[var(--parchment)] opacity-75">Subject type</span>
            <select value={subjectType} onChange={(e) => setSubjectType(e.target.value)} className="bg-[var(--deep)] border border-[var(--line)] rounded-lg p-2 text-[var(--parchment)]">
              <option value="event">Event</option>
              <option value="person">Person</option>
              <option value="place">Place</option>
              <option value="relic">Relic</option>
              <option value="phenomenon">Phenomenon</option>
              <option value="group">Group</option>
            </select>
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[var(--parchment)] opacity-75">Subject ID</span>
            <input value={subjectId} onChange={(e) => setSubjectId(e.target.value)} placeholder="event_id / soul / place…" className="bg-[var(--deep)] border border-[var(--line)] rounded-lg p-2 text-[var(--parchment)]" />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[var(--parchment)] opacity-75">Culture / faction</span>
            <input value={culture} onChange={(e) => setCulture(e.target.value)} placeholder="e.g. Salt Kingdom" className="bg-[var(--deep)] border border-[var(--line)] rounded-lg p-2 text-[var(--parchment)]" />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[var(--parchment)] opacity-75">Memory form</span>
            <select value={memoryForm} onChange={(e) => setMemoryForm(e.target.value)} className="bg-[var(--deep)] border border-[var(--line)] rounded-lg p-2 text-[var(--parchment)]">
              {MEMORY_FORMS.map((f) => <option key={f} value={f}>{f.replace('_', ' ')}</option>)}
            </select>
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[var(--parchment)] opacity-75">Interpretation</span>
            <select value={interpretation} onChange={(e) => setInterpretation(e.target.value)} className="bg-[var(--deep)] border border-[var(--line)] rounded-lg p-2 text-[var(--parchment)]">
              {INTERPRETATIONS.map((i) => <option key={i} value={i}>{i}</option>)}
            </select>
          </label>
        </div>
        <button onClick={handleCompile} disabled={compiling} className="btn-gold text-xs py-2 px-5 disabled:opacity-50">
          {compiling ? 'Compiling…' : 'Compile World Memory'}
        </button>
        {compileMessage && <p className="text-xs text-[var(--spark)]">{compileMessage}</p>}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-20 text-[var(--parchment)] opacity-70 gap-2">
          <Loader2 size={18} className="animate-spin" /> Gathering the world's memory…
        </div>
      )}
      {!loading && error && <div className="mythic-card p-6 text-center text-sm text-rose-300">{error}</div>}

      {!loading && !error && figures.length > 0 && (
        <div>
          <span className="eyebrow flex items-center gap-1.5"><ScrollText size={14} /> Legendary Figures</span>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
            {figures.map((f) => (
              <div key={f.figure_id} className="mythic-card p-5 space-y-2">
                <h3 className="text-lg font-bold font-cinzel text-[var(--gold)]">{f.figure_title}</h3>
                <p className="text-xs text-[var(--parchment)] opacity-75">{f.eligibility_rationale}</p>
                {f.later_cultural_titles.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {f.later_cultural_titles.map((t) => (
                      <span key={t} className="mythic-pill text-[10px] text-purple-300 border-purple-500/30">later title: {t}</span>
                    ))}
                  </div>
                )}
                <p className="text-[10px] font-mono text-[var(--spark)] uppercase tracking-wider">
                  {f.remembrance_scale} · {f.memory_state.replace('_', ' ')}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {!loading && !error && memories.length === 0 && (
        <div className="mythic-card p-10 text-center text-sm text-[var(--parchment)] opacity-75">
          The world has not yet begun to remember. Compile a cultural memory from a canonical source above.
        </div>
      )}

      {!loading && !error && memories.length > 0 && (
        <div className="grid grid-cols-1 gap-4">
          {memories.map((m) => {
            const isFaithful = m.interpretation_type === 'faithful';
            return (
              <div key={m.memory_id} className="mythic-card p-5 space-y-3">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                  <h3 className="text-base font-bold font-cinzel text-[var(--gold)]">{m.title}</h3>
                  <div className="flex flex-wrap gap-2">
                    <span className={`mythic-pill text-[10px] ${isFaithful ? 'text-amber-300 border-amber-400/40' : 'text-rose-300 border-rose-400/40'}`}>
                      {isFaithful ? 'Chronicle record (faithful)' : 'Later account / legend / folklore'}
                    </span>
                    <span className="mythic-pill text-[10px]">{m.memory_form.replace('_', ' ')}</span>
                    <span className="mythic-pill text-[10px] text-[var(--spark)]">{m.memory_state.replace('_', ' ')}</span>
                  </div>
                </div>
                <p className="text-sm font-body text-[var(--parchment)] opacity-85">{m.narrative}</p>
                {m.culture && <p className="text-xs text-[var(--parchment)] opacity-60">Culture: {m.culture}</p>}
                {m.deviations.length > 0 && (
                  <div className="rounded-lg bg-[var(--deep)] border border-[var(--line)] p-3 space-y-2">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-rose-300">Declared drift (never canon)</span>
                    {m.deviations.map((d) => (
                      <div key={d.deviation_id} className="text-xs text-[var(--parchment)] opacity-80">
                        <p><span className="text-[var(--spark)]">Canon:</span> {d.canon_supports}</p>
                        <p><span className="text-rose-300">Legend claims:</span> {d.legend_claims}</p>
                      </div>
                    ))}
                  </div>
                )}
                {m.source_refs.length > 0 && (
                  <p className="text-[10px] font-mono text-[var(--parchment)] opacity-50">
                    Sources: {m.source_refs.map((s) => `${s.source_type}:${s.source_id.slice(0, 8)}`).join(', ')}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
