// frontend/src/components/CuriosityView.tsx
import React, { useCallback, useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import type { LocalThread, OpenQuestion, Seed } from '../types';

interface CuriosityViewProps {
  soulName?: string;
  onRefreshChronicle?: () => void;
}

export const CuriosityView: React.FC<CuriosityViewProps> = ({ soulName = 'Unbound Soul', onRefreshChronicle }) => {
  const [seeds, setSeeds] = useState<Seed[]>([]);
  const [questions, setQuestions] = useState<OpenQuestion[]>([]);
  const [threads, setThreads] = useState<LocalThread[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // New Seed Form
  const [showPlantModal, setShowPlantModal] = useState<boolean>(false);
  const [newSymbol, setNewSymbol] = useState<string>('');
  const [newThreadType, setNewThreadType] = useState<string>('Memory');
  const [newContext, setNewContext] = useState<string>('');
  const [newQuestion, setNewQuestion] = useState<string>('');

  // Question resolution
  const [resolvingQId, setResolvingQId] = useState<string | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState<string>('');

  // Thread integration
  const [integratingThreadId, setIntegratingThreadId] = useState<string | null>(null);
  const [choiceMade, setChoiceMade] = useState<string>('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [seedRes, qRes, threadRes] = await Promise.all([
        apiClient.listSeeds(),
        apiClient.listQuestions(),
        apiClient.listThreads(soulName),
      ]);
      setSeeds(seedRes.seeds || []);
      setQuestions(qRes.questions || []);
      setThreads(threadRes.threads || []);
    } catch (err) {
      console.error('Failed to fetch curiosity data', err);
    } finally {
      setLoading(false);
    }
  }, [soulName]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handlePlantSeed = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSymbol || !newContext) return;
    try {
      await apiClient.plantSeed({
        symbol: newSymbol,
        thread_type: newThreadType,
        narrative_context: newContext,
        soul_id: soulName,
        initial_question: newQuestion || undefined,
      });
      setShowPlantModal(false);
      setNewSymbol('');
      setNewContext('');
      setNewQuestion('');
      fetchData();
    } catch (err) {
      console.error('Plant seed failed', err);
    }
  };

  const handleResolveQuestion = async (qId: string) => {
    if (!resolutionNotes) return;
    try {
      await apiClient.resolveQuestion({
        question_id: qId,
        resolution_notes: resolutionNotes,
      });
      setResolvingQId(null);
      setResolutionNotes('');
      fetchData();
      if (onRefreshChronicle) onRefreshChronicle();
    } catch (err) {
      console.error('Resolve question failed', err);
    }
  };

  const handleIntegrateThread = async (threadId: string) => {
    if (!choiceMade) return;
    try {
      await apiClient.integrateThread({
        thread_id: threadId,
        soul_name: soulName,
        choice_made: choiceMade,
      });
      setIntegratingThreadId(null);
      setChoiceMade('');
      fetchData();
      if (onRefreshChronicle) onRefreshChronicle();
    } catch (err) {
      console.error('Integrate thread failed', err);
    }
  };

  const getStageBadge = (stage: Seed['stage']) => {
    switch (stage) {
      case 'planted': return 'bg-cyan-900/60 text-cyan-300 border-cyan-500/40';
      case 'echoed': return 'bg-amber-900/60 text-amber-300 border-amber-500/40';
      case 'recognized': return 'bg-purple-900/60 text-purple-300 border-purple-500/40';
      case 'integrated': return 'bg-emerald-900/60 text-emerald-300 border-emerald-500/40';
      default: return 'bg-gray-800 text-gray-400 border-gray-600';
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto p-4 sm:p-6 text-slate-100">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-indigo-500/20 pb-4">
        <div>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-amber-200 via-indigo-300 to-cyan-300">
            ✦ Curiosity & Threads Engine
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Plant seeds of curiosity, track recurring symbols, investigate open questions, and integrate narrative threads.
          </p>
        </div>
        <button
          onClick={() => setShowPlantModal(true)}
          className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-lg shadow-lg font-medium transition text-sm flex items-center gap-2 border border-indigo-400/30"
        >
          <span>🌱</span> Plant New Seed
        </button>
      </div>

      {loading ? (
        <div className="py-12 text-center text-slate-400 animate-pulse">Consulting the Curiosity Engine...</div>
      ) : (
        <div className="space-y-8">
          {/* Section 1: Recurring Seeds & Symbols */}
          <section className="bg-slate-900/70 border border-indigo-950 rounded-xl p-5 shadow-xl backdrop-blur-md">
            <h3 className="text-lg font-bold text-amber-300 mb-4 flex items-center gap-2">
              <span>🔮</span> Active Seeds & Recurring Symbols ({seeds.length})
            </h3>
            {seeds.length === 0 ? (
              <p className="text-slate-500 italic text-sm py-4">No seeds planted yet. Roll dice or plant a seed to start tracking symbols.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {seeds.map((seed) => (
                  <div key={seed.id} className="bg-slate-800/80 border border-slate-700/60 rounded-lg p-4 flex flex-col justify-between hover:border-indigo-500/40 transition">
                    <div>
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-semibold text-indigo-200 text-base">{seed.symbol}</h4>
                        <span className={`text-xs px-2.5 py-0.5 rounded-full border ${getStageBadge(seed.stage)} uppercase font-mono tracking-wider`}>
                          {seed.stage}
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 mb-3 line-clamp-3">{seed.narrative_context}</p>
                    </div>
                    <div className="flex justify-between items-center text-xs text-slate-400 border-t border-slate-700/40 pt-2 mt-2">
                      <span className="text-cyan-400 font-mono">Thread: {seed.thread_type}</span>
                      <span className="bg-slate-700/60 text-slate-300 px-2 py-0.5 rounded text-2xs">Echoes: {seed.echo_count}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Section 2: Open Questions & Unresolved Mysteries */}
          <section className="bg-slate-900/70 border border-indigo-950 rounded-xl p-5 shadow-xl backdrop-blur-md">
            <h3 className="text-lg font-bold text-cyan-300 mb-4 flex items-center gap-2">
              <span>❓</span> Open Questions & Unresolved Mysteries ({questions.length})
            </h3>
            {questions.length === 0 ? (
              <p className="text-slate-500 italic text-sm py-4">No open questions right now. The mythology is tranquil.</p>
            ) : (
              <div className="space-y-3">
                {questions.map((q) => (
                  <div key={q.id} className="bg-slate-800/80 border border-slate-700/60 rounded-lg p-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div className="space-y-1 flex-1">
                      <div className="flex items-center gap-2">
                        <span className={`text-xs px-2 py-0.5 rounded font-mono uppercase ${q.status === 'open' ? 'bg-amber-900/50 text-amber-300 border border-amber-500/30' : 'bg-emerald-900/50 text-emerald-300 border border-emerald-500/30'}`}>
                          {q.status}
                        </span>
                        <h4 className="font-medium text-slate-200 text-sm">{q.question_text}</h4>
                      </div>
                      {q.stakes && <p className="text-xs text-slate-400 italic">{q.stakes}</p>}
                    </div>

                    {q.status === 'open' && (
                      <div>
                        {resolvingQId === q.id ? (
                          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                            <input
                              type="text"
                              placeholder="Describe how this choice answered the question..."
                              value={resolutionNotes}
                              onChange={(e) => setResolutionNotes(e.target.value)}
                              className="px-3 py-1.5 bg-slate-950 border border-cyan-500/50 rounded text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-cyan-400"
                            />
                            <button
                              onClick={() => handleResolveQuestion(q.id)}
                              className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-medium"
                            >
                              Confirm
                            </button>
                            <button
                              onClick={() => setResolvingQId(null)}
                              className="px-2 py-1.5 text-slate-400 hover:text-slate-200 text-xs"
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => { setResolvingQId(q.id); setResolutionNotes(''); }}
                            className="px-3 py-1.5 bg-cyan-900/40 hover:bg-cyan-800/60 border border-cyan-500/40 text-cyan-200 rounded text-xs font-medium transition"
                          >
                            Resolve Question
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Section 3: Local Threads & Integration Engine */}
          <section className="bg-slate-900/70 border border-indigo-950 rounded-xl p-5 shadow-xl backdrop-blur-md">
            <h3 className="text-lg font-bold text-purple-300 mb-4 flex items-center gap-2">
              <span>🪡</span> Local Threads & Integration Engine ({threads.length})
            </h3>
            {threads.length === 0 ? (
              <p className="text-slate-500 italic text-sm py-4">No local threads registered yet. Encounter events will form threads over time.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {threads.map((th) => (
                  <div key={th.id} className="bg-slate-800/80 border border-purple-900/40 rounded-lg p-4 flex flex-col justify-between">
                    <div className="space-y-2">
                      <div className="flex justify-between items-start">
                        <h4 className="font-bold text-purple-200">{th.name}</h4>
                        <span className={`text-xs px-2.5 py-0.5 rounded-full border font-mono ${th.status === 'integrated' ? 'bg-emerald-950 text-emerald-300 border-emerald-600/40' : th.status === 'pattern_recognized' ? 'bg-purple-950 text-purple-300 border-purple-500/40' : 'bg-slate-800 text-slate-300 border-slate-600'}`}>
                          {th.status}
                        </span>
                      </div>
                      <p className="text-xs text-slate-300">{th.evidence_summary}</p>
                      <div className="text-2xs text-slate-400 font-mono">
                        Type: <span className="text-purple-300">{th.thread_type}</span> | Evidence Count: <span className="text-amber-300">{th.evidence_count}</span>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-700/50">
                      {th.status !== 'integrated' ? (
                        integratingThreadId === th.id ? (
                          <div className="space-y-2">
                            <textarea
                              placeholder="State the player's integrating choice..."
                              value={choiceMade}
                              onChange={(e) => setChoiceMade(e.target.value)}
                              className="w-full p-2 bg-slate-950 border border-purple-500/40 rounded text-xs text-slate-100 focus:outline-none"
                              rows={2}
                            />
                            <div className="flex gap-2 justify-end">
                              <button
                                onClick={() => handleIntegrateThread(th.id)}
                                className="px-3 py-1 bg-purple-600 hover:bg-purple-500 text-white rounded text-xs font-semibold"
                              >
                                Transform & Integrate
                              </button>
                              <button
                                onClick={() => setIntegratingThreadId(null)}
                                className="px-2 py-1 text-slate-400 hover:text-slate-200 text-xs"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        ) : (
                          <button
                            onClick={() => { setIntegratingThreadId(th.id); setChoiceMade(''); }}
                            className="w-full py-1.5 bg-gradient-to-r from-purple-900/60 to-indigo-900/60 hover:from-purple-800/80 hover:to-indigo-800/80 border border-purple-500/40 text-purple-200 rounded text-xs font-semibold transition"
                          >
                            Integrate Thread Choice ✨
                          </button>
                        )
                      ) : (
                        <div className="text-xs text-emerald-400 flex items-center gap-1 font-mono">
                          <span>✓</span> Integrated into Canon
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      )}

      {/* Plant Seed Modal */}
      {showPlantModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-indigo-500/30 rounded-xl p-6 max-w-lg w-full shadow-2xl space-y-4">
            <h3 className="text-xl font-bold text-amber-300">🌱 Plant a Curiosity Seed</h3>
            <form onSubmit={handlePlantSeed} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Symbol Name</label>
                <input
                  type="text"
                  placeholder="e.g. Drowned Lantern, Salt Bell, Unreflected King"
                  value={newSymbol}
                  onChange={(e) => setNewSymbol(e.target.value)}
                  className="w-full p-2 bg-slate-950 border border-slate-700 rounded text-sm text-slate-100"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Thread Dimension</label>
                <select
                  value={newThreadType}
                  onChange={(e) => setNewThreadType(e.target.value)}
                  className="w-full p-2 bg-slate-950 border border-slate-700 rounded text-sm text-slate-100"
                >
                  <option value="Memory">Memory</option>
                  <option value="Bond">Bond</option>
                  <option value="Mark">Mark</option>
                  <option value="Prophecy">Prophecy</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Narrative Context</label>
                <textarea
                  placeholder="Where or how did this symbol first manifest?"
                  value={newContext}
                  onChange={(e) => setNewContext(e.target.value)}
                  className="w-full p-2 bg-slate-950 border border-slate-700 rounded text-sm text-slate-100"
                  rows={3}
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Initial Open Question (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. What oath was erased beneath the harbor?"
                  value={newQuestion}
                  onChange={(e) => setNewQuestion(e.target.value)}
                  className="w-full p-2 bg-slate-950 border border-slate-700 rounded text-sm text-slate-100"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowPlantModal(false)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 rounded text-sm hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded text-sm"
                >
                  Plant Seed
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
