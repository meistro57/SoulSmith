import React, { useCallback, useEffect, useState } from 'react';
import { BookOpen, HeartHandshake, Loader2, ScrollText, ShieldCheck } from 'lucide-react';
import type { PromiseRecord, Relationship } from '../types';
import { apiClient } from '../lib/api';

interface RelationshipsViewProps {
  soulName: string;
}

export const RelationshipsView: React.FC<RelationshipsViewProps> = ({ soulName }) => {
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [promises, setPromises] = useState<PromiseRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      apiClient.listRelationships({ viewer_soul_id: soulName }),
      apiClient.listPromises({ viewer_soul_id: soulName }),
    ])
      .then(([rel, prom]) => {
        setRelationships(rel.relationships);
        setPromises(prom.promises);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [soulName]);

  useEffect(() => {
    reload();
  }, [reload]);

  const activePromises = promises.filter((p) =>
    ['proposed', 'made', 'acknowledged', 'active', 'disputed', 'inherited', 'rediscovered', 'unresolved'].includes(p.lifecycle_state)
  );
  const settledPromises = promises.filter((p) =>
    ['fulfilled', 'broken', 'released', 'impossible', 'forgotten'].includes(p.lifecycle_state)
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[300px] text-amber-300">
        <Loader2 className="w-8 h-8 animate-spin mr-3" />
        <span className="text-lg font-mono">Gathering bonds and oaths...</span>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6 p-4 md:p-6 text-slate-100">
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-amber-950/70 to-slate-900 border border-amber-500/30 p-6 md:p-8 shadow-2xl">
        <div className="relative z-10 space-y-3">
          <div className="flex items-center space-x-3 text-amber-400 font-mono text-sm tracking-wider uppercase">
            <HeartHandshake className="w-4 h-4" />
            <span>Phase 19 • Relationship &amp; Promise Engine</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-amber-200 via-rose-200 to-sky-300">
            Bonds &amp; Oaths
          </h1>
          <p className="text-slate-300 text-sm md:text-base max-w-3xl leading-relaxed">
            A relationship is history between people. A promise is a claim on the future. Neither may be invented by the narrator.
          </p>
        </div>
      </div>

      {error && (
        <div className="rounded-xl bg-rose-950/60 border border-rose-500/40 p-4 text-rose-200 text-sm">{error}</div>
      )}

      {/* Relationships */}
      <section>
        <div className="flex items-center space-x-2 mb-3">
          <BookOpen className="w-4 h-4 text-amber-400" />
          <h2 className="text-lg font-bold text-slate-100">Relationships</h2>
        </div>
        {relationships.length === 0 ? (
          <p className="text-sm text-slate-400 italic">No canonical relationships recorded yet.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {relationships.map((rel) => (
              <div key={rel.relationship_id} className="bg-slate-900/80 border border-amber-500/20 rounded-xl p-4 space-y-3 shadow-xl">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-mono uppercase bg-amber-950/80 border border-amber-500/30 px-2.5 py-1 rounded-full text-amber-300">
                    {rel.kinds.join(', ') || 'relationship'}
                  </span>
                  <span className="text-xs font-mono uppercase text-slate-400">{rel.status}</span>
                </div>
                <div className="text-sm text-slate-300">
                  <span className="font-mono uppercase text-slate-500 text-xs">Between:</span>{' '}
                  {rel.participants.map((p) => p.entity_id).join(' ↔ ')}
                </div>
                {rel.creation_context && (
                  <p className="text-sm text-slate-400 italic">"{rel.creation_context}"</p>
                )}
                {rel.events.length > 0 && (
                  <div className="text-xs text-slate-400 space-y-1">
                    <span className="font-mono uppercase text-slate-500">History:</span>
                    {rel.events.map((e) => (
                      <div key={e.event_id}>· {e.event_type} ({e.source_type}:{e.source_id.slice(0, 8)})</div>
                    ))}
                  </div>
                )}
                {rel.perspectives.length > 0 && (
                  <div className="text-xs text-slate-400 space-y-1">
                    <span className="font-mono uppercase text-slate-500">Perspectives:</span>
                    {rel.perspectives.map((p) => (
                      <div key={p.perspective_id} className="italic">
                        · {p.entity_id} sees this as {p.kind}{p.is_canonical_interaction ? '' : ' (interpretation)'}
                      </div>
                    ))}
                  </div>
                )}
                {rel.source_refs.length > 0 && (
                  <div className="text-[11px] font-mono text-slate-500 border-t border-slate-800 pt-2">
                    Why: {rel.source_refs.map((r) => `${r.source_type}:${r.source_id.slice(0, 8)}`).join(', ')}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Active / unresolved promises */}
      <section>
        <div className="flex items-center space-x-2 mb-3">
          <ScrollText className="w-4 h-4 text-amber-400" />
          <h2 className="text-lg font-bold text-slate-100">Active &amp; Unresolved Promises</h2>
        </div>
        {activePromises.length === 0 ? (
          <p className="text-sm text-slate-400 italic">No unresolved oaths.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {activePromises.map((promise) => (
              <div key={promise.promise_id} className="bg-slate-900/80 border border-rose-500/20 rounded-xl p-4 space-y-2 shadow-xl">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-mono uppercase bg-rose-950/80 border border-rose-500/30 px-2.5 py-1 rounded-full text-rose-300">
                    {promise.lifecycle_state}
                  </span>
                  <span className="text-xs font-mono text-slate-500">{promise.visibility}</span>
                </div>
                <p className="text-sm text-slate-200 italic">"{promise.promise_text}"</p>
                <div className="text-xs text-slate-400">
                  <span className="font-mono uppercase text-slate-500">Promisor:</span> {promise.promisor_entity_id}
                </div>
                <div className="text-[11px] font-mono text-slate-500 border-t border-slate-800 pt-2">
                  Why: {promise.source_type}:{promise.source_id.slice(0, 8)} · {promise.source_authorization}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Settled / historical promises */}
      <section>
        <div className="flex items-center space-x-2 mb-3">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <h2 className="text-lg font-bold text-slate-100">Fulfilled, Released &amp; Historical</h2>
        </div>
        {settledPromises.length === 0 ? (
          <p className="text-sm text-slate-400 italic">No settled oaths yet.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {settledPromises.map((promise) => (
              <div key={promise.promise_id} className="bg-slate-900/80 border border-slate-700 rounded-xl p-4 space-y-2 shadow-xl">
                <span className="text-xs font-mono uppercase bg-slate-800 border border-slate-700 px-2.5 py-1 rounded-full text-slate-300">
                  {promise.lifecycle_state}
                </span>
                <p className="text-sm text-slate-300 italic">"{promise.promise_text}"</p>
                <div className="text-[11px] font-mono text-slate-500 border-t border-slate-800 pt-2">
                  Original wording preserved · {promise.state_history.length} transition(s)
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
