// frontend/src/components/CampaignView.tsx
import React, { useCallback, useEffect, useState } from 'react';
import type { CampaignOpportunity, CampaignSession, CampaignTransition } from '../types';
import { apiClient } from '../lib/api';
import { Compass, RefreshCw, Sparkles, ScrollText, ShieldCheck, Play, Eye, CircleDashed, Check, X, Clock3 } from 'lucide-react';

interface CampaignViewProps {
  soulName: string;
}

export const CampaignView: React.FC<CampaignViewProps> = ({ soulName }) => {
  const [session, setSession] = useState<CampaignSession | null>(null);
  const [opportunities, setOpportunities] = useState<CampaignOpportunity[]>([]);
  const [transitions, setTransitions] = useState<CampaignTransition[]>([]);
  const [aftermath, setAftermath] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [inspectId, setInspectId] = useState<string | null>(null);

  const ensureSession = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const started = await apiClient.startCampaignSession({ soul_id: soulName });
      setSession(started.session);
      return started.session.session_id;
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      return null;
    } finally {
      setLoading(false);
    }
  }, [soulName]);

  const refresh = useCallback(async (sessionId?: string) => {
    const id = sessionId ?? session?.session_id;
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const state = await apiClient.getCampaignSession(id);
      setSession(state.session);
      setOpportunities(state.opportunities.filter((o) => o.lifecycle_state === 'eligible' || o.lifecycle_state === 'selected'));
      setTransitions(state.transitions);
      const summary = await apiClient.getCampaignAftermath(id);
      setAftermath(summary);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [session?.session_id]);

  useEffect(() => {
    (async () => {
      const id = await ensureSession();
      if (id) await refresh(id);
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [soulName]);

  const handleEvaluate = async () => {
    if (!session) return;
    setBusy(true);
    setError(null);
    try {
      await apiClient.evaluateCampaignOpportunities(session.session_id, true);
      await refresh(session.session_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const handleResolve = async (opportunity: CampaignOpportunity, payload: Record<string, any> = {}) => {
    setBusy(true);
    setError(null);
    try {
      await apiClient.resolveCampaignOpportunity(opportunity.opportunity_id, payload);
      await refresh(session!.session_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const handleInspect = async (opportunityId: string) => {
    setInspectId(inspectId === opportunityId ? null : opportunityId);
  };

  if (loading && !session) {
    return (
      <div className="flex items-center justify-center min-h-[400px] text-indigo-300">
        <Compass className="w-8 h-8 animate-spin mr-3 text-amber-400" />
        <span className="text-lg font-mono">Gathering the campaign...</span>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6 p-4 md:p-6 text-slate-100">
      {/* Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950/80 to-slate-900 border border-indigo-500/30 p-6 md:p-8 shadow-2xl">
        <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
          <Compass className="w-64 h-64 text-indigo-300" />
        </div>
        <div className="relative z-10 space-y-4">
          <div className="flex items-center space-x-3 text-indigo-400 font-mono text-sm tracking-wider uppercase">
            <Compass className="w-4 h-4" />
            <span>Phase 17 • Campaign Orchestrator</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-200 via-amber-200 to-sky-300">
            The North-Star Loop
          </h1>
          <p className="text-slate-300 text-sm md:text-base max-w-3xl leading-relaxed">
            The orchestrator decides what gets an opportunity to act next. It never decides what your story means.
          </p>
          <div className="flex flex-wrap items-center gap-2 pt-4 border-t border-indigo-500/20">
            <button
              onClick={handleEvaluate}
              disabled={busy}
              className="inline-flex items-center px-4 py-2.5 rounded-xl bg-indigo-500/20 hover:bg-indigo-500/30 border border-indigo-400/40 text-indigo-200 font-medium transition-all shadow-lg cursor-pointer disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${busy ? 'animate-spin' : ''}`} />
              Evaluate Opportunities
            </button>
            {session && (
              <span className="text-xs font-mono text-slate-400 ml-2">
                Session {session.session_id.slice(0, 8)}
              </span>
            )}
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-xl bg-rose-950/60 border border-rose-500/40 p-4 text-rose-200 text-sm">{error}</div>
      )}

      {/* Aftermath */}
      {aftermath && (
        <div className="rounded-xl bg-slate-900/80 border border-slate-800 p-5 grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-amber-300">{aftermath.transition_count ?? 0}</div>
            <div className="text-xs font-mono uppercase text-slate-400">Transitions</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-indigo-300">{aftermath.open_opportunity_count ?? 0}</div>
            <div className="text-xs font-mono uppercase text-slate-400">Open Opportunities</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-emerald-300">{aftermath.recognized_thread_count ?? 0}</div>
            <div className="text-xs font-mono uppercase text-slate-400">Recognized Threads</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-purple-300">{aftermath.remembered_relic_count ?? 0}</div>
            <div className="text-xs font-mono uppercase text-slate-400">Remembered Relics</div>
          </div>
        </div>
      )}

      {/* Opportunities */}
      <section>
        <div className="flex items-center space-x-2 mb-3">
          <Sparkles className="w-4 h-4 text-amber-400" />
          <h2 className="text-lg font-bold text-slate-100">Eligible Opportunities</h2>
        </div>
        {opportunities.length === 0 ? (
          <p className="text-sm text-slate-400 italic">Nothing needs to echo right now. Let the current scene breathe.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {opportunities.map((opportunity) => (
              <div key={opportunity.opportunity_id} className="bg-slate-900/80 border border-indigo-500/30 rounded-xl p-4 space-y-3 shadow-xl">
                <div className="flex items-center justify-between gap-2">
                  <span className="inline-flex items-center space-x-1.5 text-xs font-mono uppercase bg-indigo-950/80 border border-indigo-500/30 px-2.5 py-1 rounded-full text-indigo-300">
                    <CircleDashed className="w-3.5 h-3.5" />
                    <span>{opportunity.opportunity_type.replace(/_/g, ' ')}</span>
                  </span>
                  <span className="text-xs font-mono uppercase text-slate-400">{opportunity.urgency_class}</span>
                </div>

                {opportunity.narration && (
                  <p className="text-sm text-slate-200 italic leading-relaxed">"{opportunity.narration}"</p>
                )}

                <div className="text-xs text-slate-400">
                  <span className="font-mono uppercase text-slate-500">Why:</span> {opportunity.eligibility_rule}
                </div>

                {opportunity.source_evidence.length > 0 && (
                  <div className="text-xs text-slate-400">
                    <span className="font-mono uppercase text-slate-500">Evidence:</span>{' '}
                    {opportunity.source_evidence.map((e) => `${e.source_type}:${e.source_id.slice(0, 8)}`).join(', ')}
                  </div>
                )}

                <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800">
                  {opportunity.opportunity_type === 'recognition' && (
                    <>
                      <button onClick={() => handleResolve(opportunity, { recognition: { decision: 'recognize' } })} disabled={busy} className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-mono bg-emerald-500/20 border border-emerald-400/40 text-emerald-200 cursor-pointer disabled:opacity-50">
                        <Check className="w-3.5 h-3.5 mr-1" /> Recognize
                      </button>
                      <button onClick={() => handleResolve(opportunity, { recognition: { decision: 'reject' } })} disabled={busy} className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-mono bg-rose-500/20 border border-rose-400/40 text-rose-200 cursor-pointer disabled:opacity-50">
                        <X className="w-3.5 h-3.5 mr-1" /> Reject
                      </button>
                      <button onClick={() => handleResolve(opportunity, { recognition: { decision: 'postpone' } })} disabled={busy} className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-mono bg-slate-700/40 border border-slate-600 text-slate-300 cursor-pointer disabled:opacity-50">
                        <Clock3 className="w-3.5 h-3.5 mr-1" /> Postpone
                      </button>
                    </>
                  )}
                  {opportunity.opportunity_type === 'integration_candidate' && (
                    <button onClick={() => handleResolve(opportunity, { decision: 'integrate', player_intent: 'I chose differently after recognizing the pattern.' })} disabled={busy} className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-mono bg-amber-500/20 border border-amber-400/40 text-amber-200 cursor-pointer disabled:opacity-50">
                      <Play className="w-3.5 h-3.5 mr-1" /> Integrate
                    </button>
                  )}
                  {opportunity.opportunity_type !== 'recognition' && opportunity.opportunity_type !== 'integration_candidate' && (
                    <button onClick={() => handleResolve(opportunity, {})} disabled={busy} className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-mono bg-indigo-500/20 border border-indigo-400/40 text-indigo-200 cursor-pointer disabled:opacity-50">
                      <Play className="w-3.5 h-3.5 mr-1" /> Resolve
                    </button>
                  )}
                  <button onClick={() => handleInspect(opportunity.opportunity_id)} className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-mono bg-slate-800/60 border border-slate-700 text-slate-300 cursor-pointer">
                    <Eye className="w-3.5 h-3.5 mr-1" /> Why
                  </button>
                </div>

                {inspectId === opportunity.opportunity_id && (
                  <pre className="text-xs font-mono bg-slate-950/80 rounded-lg p-3 overflow-x-auto text-slate-300">
                    {JSON.stringify(opportunity, null, 2)}
                  </pre>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Transitions */}
      <section>
        <div className="flex items-center space-x-2 mb-3">
          <ScrollText className="w-4 h-4 text-amber-400" />
          <h2 className="text-lg font-bold text-slate-100">Recent Transitions</h2>
        </div>
        {transitions.length === 0 ? (
          <p className="text-sm text-slate-400 italic">No transitions yet.</p>
        ) : (
          <div className="space-y-3">
            {[...transitions].reverse().slice(0, 8).map((transition) => (
              <div key={transition.transition_id} className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="text-xs font-mono uppercase text-indigo-300">{transition.transition_type}</span>
                  <span className="text-xs font-mono text-slate-500">{transition.transition_id.slice(0, 8)}</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {transition.systems_invoked.map((system) => (
                    <span key={system} className="inline-flex items-center text-[11px] font-mono bg-slate-800 border border-slate-700 px-2 py-0.5 rounded-full text-slate-300">
                      <ShieldCheck className="w-3 h-3 mr-1 text-emerald-400" />
                      {system}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
