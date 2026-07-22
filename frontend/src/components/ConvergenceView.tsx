// frontend/src/components/ConvergenceView.tsx
import React, { useCallback, useEffect, useState } from 'react';
import type { CanonicalDiceRead, CommunitySymbol, GatheringSession } from '../types';
import { apiClient } from '../lib/api';
import { Users, Radio, Sparkles, Send, Zap, GitFork, Globe, CheckCircle2, Share2, Plus, X } from 'lucide-react';

interface ConvergenceViewProps {
  currentRead: CanonicalDiceRead;
  soulName: string;
}

interface ConvergenceMessage {
  id: string;
  sender: string;
  role: 'Focus' | 'Anchor' | 'Witness' | 'Tempest';
  text: string;
  timestamp: string;
}

export const ConvergenceView: React.FC<ConvergenceViewProps> = ({ currentRead, soulName }) => {
  const [roomId] = useState('Convergence-Room-Alpha');
  const [activeRole, setActiveRole] = useState<'Focus' | 'Anchor' | 'Witness' | 'Tempest'>('Focus');
  const [messages, setMessages] = useState<ConvergenceMessage[]>([
    {
      id: '1',
      sender: 'Kaelen the Seeker',
      role: 'Focus',
      text: 'Cast roll: Oracle + Water + Transformation. Attempting to decode the submerged archive.',
      timestamp: '13:42',
    },
    {
      id: '2',
      sender: 'Archivist Vael',
      role: 'Witness',
      text: 'Witnessing beat. Standard memory facts confirmed. No canon contradiction found.',
      timestamp: '13:43',
    },
  ]);
  const [inputText, setInputText] = useState('');

  // Phase 7 State
  const [gathering, setGathering] = useState<GatheringSession | null>(null);
  const [communitySymbols, setCommunitySymbols] = useState<CommunitySymbol[]>([]);
  const [resonanceContribution, setResonanceContribution] = useState<number>(2);
  const [contributionNotes, setContributionNotes] = useState<string>('');
  const [showMergeModal, setShowMergeModal] = useState<boolean>(false);
  const [showCreateSymbolModal, setShowCreateSymbolModal] = useState<boolean>(false);
  const [newSymbolName, setNewSymbolName] = useState<string>('');
  const [newSymbolDesc, setNewSymbolDesc] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const fetchGatheringAndSymbols = useCallback(async () => {
    setLoading(true);
    try {
      const gRes = await apiClient.getGatheringSession(roomId, 'Awakening of the Salt Spire');
      setGathering(gRes.gathering);

      const sRes = await apiClient.listCommunitySymbols();
      setCommunitySymbols(sRes.symbols);
    } catch (err) {
      console.error('Failed to load convergence gathering:', err);
    } finally {
      setLoading(false);
    }
  }, [roomId]);

  useEffect(() => {
    fetchGatheringAndSymbols();
  }, [fetchGatheringAndSymbols]);

  const handleSendMessage = () => {
    if (!inputText.trim()) return;
    const newMsg: ConvergenceMessage = {
      id: Date.now().toString(),
      sender: soulName,
      role: activeRole,
      text: inputText.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages((prev) => [...prev, newMsg]);
    setInputText('');
  };

  const handleSynthesizeConvergence = () => {
    const synMsg: ConvergenceMessage = {
      id: Date.now().toString(),
      sender: 'SOULKEEPER WEAVER',
      role: 'Witness',
      text: `SYNTHESIS BEAT: [Focus] ${soulName}'s Spark (${currentRead.interpretation.spark}) merges with the [Tempest] pressure (${currentRead.interpretation.pressure}). A shared revelation emerges at the ${currentRead.interpretation.domain}!`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages((prev) => [...prev, synMsg]);
  };

  const handleContributeResonance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!gathering) return;
    try {
      const res = await apiClient.contributeToGathering({
        gathering_id: gathering.id,
        contributor_soul: soulName,
        role: activeRole,
        resonance_amount: resonanceContribution,
        notes: contributionNotes || `Channeled [${currentRead.interpretation.spark}] spark into gathering resonance.`,
      });
      setGathering(res.gathering);
      setContributionNotes('');
      setStatusMessage(`Contributed +${resonanceContribution} Resonance as ${activeRole}!`);
      setTimeout(() => setStatusMessage(null), 4000);
    } catch (err: any) {
      console.error('Failed to contribute resonance:', err);
    }
  };

  const handleMergeCanon = async () => {
    if (!gathering) return;
    try {
      const res = await apiClient.mergeSharedCanon({
        gathering_id: gathering.id,
        symbol_name: gathering.phenomenon_name,
        description: `Community gathering outcome achieved by ${soulName} and participating Souls.`,
        consenting_souls: [soulName, 'Archivist Vael', 'Mira the Seeker'],
      });
      setShowMergeModal(false);
      setStatusMessage(res.canon_merge_summary);
      fetchGatheringAndSymbols();
      setTimeout(() => setStatusMessage(null), 5000);
    } catch (err: any) {
      console.error('Failed to merge canon:', err);
    }
  };

  const handleForkCanon = async () => {
    if (!gathering) return;
    try {
      const res = await apiClient.forkPrivateCanon({
        gathering_id: gathering.id,
        forking_soul: soulName,
        reason: 'Player opted to preserve private campaign divergence from community canon.',
      });
      setStatusMessage(res.fork_summary);
      setTimeout(() => setStatusMessage(null), 5000);
    } catch (err: any) {
      console.error('Failed to fork canon:', err);
    }
  };

  const handleCreateSymbolSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSymbolName || !newSymbolDesc) return;
    try {
      await apiClient.createCommunitySymbol({
        symbol_name: newSymbolName,
        description: newSymbolDesc,
        contributing_souls: [soulName],
        canon_status: 'opt_in_shared',
      });
      setShowCreateSymbolModal(false);
      setNewSymbolName('');
      setNewSymbolDesc('');
      fetchGatheringAndSymbols();
    } catch (err: any) {
      console.error('Failed to create community symbol:', err);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header Banner */}
      <div className="glass-panel p-6 md:p-8 relative overflow-hidden">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative z-10">
          <div>
            <span className="text-xs uppercase tracking-widest text-pink-400 font-mono font-bold flex items-center gap-1.5 mb-1">
              <Radio size={14} className="animate-pulse text-pink-400" /> Real-Time Multiplayer Resonance
            </span>
            <h2 className="text-2xl md:text-3xl font-bold font-cinzel text-slate-100">
              Convergence Room Sanctuary
            </h2>
            <p className="text-xs md:text-sm text-slate-300 max-w-2xl mt-1">
              Phase 7: Gatherings where multiple rolls contribute to evolving phenomena, consent-aware shared canon, world-level community symbols, and explicit merge/fork controls.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="glass-pill text-xs text-emerald-400 border-emerald-500/30 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" /> Room: {roomId}
            </span>
            <button onClick={handleSynthesizeConvergence} className="btn-primary py-2 px-4 text-xs font-mono">
              <Zap size={14} /> Synthesize Shared Beat
            </button>
          </div>
        </div>
      </div>

      {statusMessage && (
        <div className="p-4 rounded-xl bg-indigo-950/80 border border-indigo-400/40 text-indigo-200 text-xs font-mono flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{statusMessage}</span>
          </div>
          <button onClick={() => setStatusMessage(null)} className="text-slate-400 hover:text-slate-200">
            ✕
          </button>
        </div>
      )}

      {/* Gathering Phenomenon Resonance Awakening Section */}
      {gathering && (
        <div className="bg-slate-900/90 backdrop-blur-md rounded-2xl border border-purple-500/30 p-6 space-y-5 shadow-2xl">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
            <div>
              <span className="text-[11px] font-mono text-amber-400 font-bold uppercase tracking-wider">
                Gathering Phenomenon Goal
              </span>
              <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-purple-400" />
                <span>{gathering.phenomenon_name}</span>
              </h3>
            </div>

            <div className="flex items-center gap-2 font-mono text-xs">
              <span className={`px-3 py-1 rounded-full border font-bold ${
                gathering.status === 'reconciled'
                  ? 'bg-emerald-950 text-emerald-300 border-emerald-500/50'
                  : 'bg-purple-950 text-purple-300 border-purple-500/50'
              }`}>
                Status: {gathering.status.toUpperCase()}
              </span>
              <button
                onClick={() => setShowMergeModal(true)}
                className="py-1.5 px-3 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 border border-amber-400/40 text-amber-200 font-bold transition flex items-center gap-1 cursor-pointer"
              >
                <Share2 size={13} />
                <span>Merge / Fork Canon</span>
              </button>
            </div>
          </div>

          {/* Resonance Progress Bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs font-mono text-slate-300">
              <span>Collective Resonance Pool</span>
              <span className="font-bold text-amber-300">
                {gathering.current_resonance} / {gathering.target_resonance} Resonance Points
              </span>
            </div>
            <div className="w-full h-3 bg-slate-950 rounded-full border border-indigo-500/30 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-amber-400 transition-all duration-500 shadow-glow-purple"
                style={{
                  width: `${Math.min(100, (gathering.current_resonance / gathering.target_resonance) * 100)}%`,
                }}
              />
            </div>
          </div>

          {/* Contribute Roll Form */}
          <form onSubmit={handleContributeResonance} className="pt-2 grid grid-cols-1 md:grid-cols-4 gap-3 text-xs font-mono">
            <div>
              <label className="block text-slate-400 mb-1">Resonance Points</label>
              <input
                type="number"
                min={1}
                max={5}
                value={resonanceContribution}
                onChange={(e) => setResonanceContribution(parseInt(e.target.value) || 1)}
                className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl p-2.5 text-slate-100 focus:outline-none focus:border-amber-400"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-slate-400 mb-1">Resonance Intention / Roll Notes</label>
              <input
                type="text"
                placeholder={`Channeled [${currentRead.interpretation.spark}] spark as ${activeRole}...`}
                value={contributionNotes}
                onChange={(e) => setContributionNotes(e.target.value)}
                className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl p-2.5 text-slate-100 focus:outline-none focus:border-amber-400"
              />
            </div>

            <div className="flex items-end">
              <button
                type="submit"
                className="w-full py-2.5 px-4 rounded-xl bg-purple-500 hover:bg-purple-400 font-bold text-slate-950 flex items-center justify-center gap-1.5 transition cursor-pointer shadow-lg shadow-purple-500/20"
              >
                <Zap size={14} />
                <span>Contribute Roll</span>
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Role Selection Grid */}
      <div className="space-y-3">
        <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300">
          Gathering Role Rotation
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { role: 'Focus', desc: 'Active Soul whose intention is on the line' },
            { role: 'Anchor', desc: 'Chooses which existing Bond/Thread is at stake' },
            { role: 'Witness', desc: 'Confirms canon write-back and validates lore' },
            { role: 'Tempest', desc: 'Speaks for the environment and phenomenon pressure' },
          ].map((r) => (
            <div
              key={r.role}
              onClick={() => setActiveRole(r.role as any)}
              className={`cursor-pointer p-4 rounded-xl transition-all ${
                activeRole === r.role
                  ? 'bg-slate-900 border-2 border-purple-500 shadow-glow-purple'
                  : 'bg-slate-900/60 border border-slate-800 hover:bg-slate-900/90'
              }`}
            >
              <div className="flex justify-between items-center mb-1">
                <span className="font-bold text-sm font-cinzel text-slate-100">{r.role}</span>
                {activeRole === r.role && <Sparkles size={14} className="text-purple-400" />}
              </div>
              <p className="text-[11px] text-slate-400">{r.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Community World Symbols Board */}
      <div className="bg-slate-900/90 backdrop-blur-md rounded-2xl border border-indigo-500/20 p-6 space-y-4 shadow-xl">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Globe className="w-4 h-4 text-cyan-400" />
              <span>World-Level Community Symbols</span>
            </h3>
            <p className="text-xs text-slate-400">
              Shared symbols forged through multi-player convergence sessions.
            </p>
          </div>
          <button
            onClick={() => setShowCreateSymbolModal(true)}
            className="py-2 px-3 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-400/40 text-cyan-200 text-xs font-mono font-bold flex items-center gap-1.5 transition cursor-pointer"
          >
            <Plus size={14} />
            <span>Propose Symbol</span>
          </button>
        </div>

        {loading ? (
          <div className="text-center py-6 font-mono text-slate-400 animate-pulse text-xs">
            Loading community world symbols...
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {communitySymbols.map((sym) => (
              <div key={sym.id} className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2 flex flex-col justify-between">
                <div className="space-y-1.5">
                  <div className="flex items-start justify-between gap-1">
                    <h4 className="font-bold text-slate-100 text-sm">{sym.symbol_name}</h4>
                    <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                      sym.canon_status === 'public_canon'
                        ? 'bg-emerald-950 text-emerald-300 border-emerald-500/40'
                        : 'bg-amber-950 text-amber-300 border-amber-500/40'
                    }`}>
                      {sym.canon_status === 'public_canon' ? 'Public Canon' : 'Opt-In Shared'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 font-serif leading-relaxed">
                    {sym.description}
                  </p>
                </div>

                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-slate-400">
                  <span>Significance: <strong>{sym.significance_score} Souls</strong></span>
                  <span className="text-cyan-300">{sym.contributing_souls.length} Contributors</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Live Room Feed & Chat */}
      <div className="glass-panel p-6 space-y-4">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
          <Users size={16} className="text-cyan-400" /> Live Room Chronicle Stream
        </h3>

        <div className="space-y-3 max-h-80 overflow-y-auto p-4 rounded-xl bg-slate-950/80 border border-slate-800 font-mono text-xs">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`p-3 rounded-lg border space-y-1 ${
                m.sender.includes('SOULKEEPER')
                  ? 'bg-purple-950/60 border-purple-500/40 text-purple-200'
                  : 'bg-slate-900 border-slate-800 text-slate-200'
              }`}
            >
              <div className="flex justify-between items-center">
                <span className="font-bold font-cinzel text-slate-100 flex items-center gap-2">
                  {m.sender} <span className="glass-pill py-0 px-2 text-[10px] text-cyan-300">{m.role}</span>
                </span>
                <span className="text-[10px] text-slate-500">{m.timestamp}</span>
              </div>
              <p className="leading-relaxed">{m.text}</p>
            </div>
          ))}
        </div>

        {/* Input box */}
        <div className="flex gap-2 font-mono text-xs">
          <input
            type="text"
            placeholder={`Speak as [${activeRole}] in ${roomId}...`}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-200 focus:outline-none focus:border-purple-500"
          />
          <button onClick={handleSendMessage} className="btn-primary py-2.5 px-5">
            <Send size={14} /> Send
          </button>
        </div>
      </div>

      {/* Canon Merge / Fork Controls Modal */}
      {showMergeModal && gathering && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="bg-slate-900 border border-amber-400/50 rounded-2xl p-6 max-w-md w-full space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-indigo-500/20 pb-3">
              <h3 className="text-lg font-bold text-amber-200 flex items-center gap-2">
                <Share2 className="w-4 h-4 text-amber-400" />
                <span>Consent-Aware Canon Controls</span>
              </h3>
              <button onClick={() => setShowMergeModal(false)} className="text-slate-400 hover:text-slate-200">
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed font-serif">
              SoulSmith preserves individual agency when stories intersect. You can choose to merge shared gathering achievements into world canon, or fork your private timeline.
            </p>

            <div className="space-y-3 font-mono text-xs">
              <button
                onClick={handleMergeCanon}
                className="w-full p-3.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 border border-amber-400/50 text-amber-200 font-bold text-left space-y-1 transition cursor-pointer"
              >
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-amber-400" />
                  <span>Merge into Public World Canon</span>
                </div>
                <p className="text-[11px] text-slate-400 font-serif">
                  Promotes "{gathering.phenomenon_name}" to a public world symbol with consent from all participating Souls.
                </p>
              </button>

              <button
                onClick={handleForkCanon}
                className="w-full p-3.5 rounded-xl bg-indigo-950/80 hover:bg-indigo-900/80 border border-indigo-500/50 text-indigo-200 font-bold text-left space-y-1 transition cursor-pointer"
              >
                <div className="flex items-center gap-2">
                  <GitFork className="w-4 h-4 text-indigo-400" />
                  <span>Fork Private Timeline Branch</span>
                </div>
                <p className="text-[11px] text-slate-400 font-serif">
                  Separates your character's history into an isolated private campaign branch without altering shared world canon.
                </p>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Propose Symbol Modal */}
      {showCreateSymbolModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="bg-slate-900 border border-cyan-400/50 rounded-2xl p-6 max-w-md w-full space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-cyan-500/20 pb-3">
              <h3 className="text-lg font-bold text-cyan-200 flex items-center gap-2">
                <Globe className="w-4 h-4 text-cyan-400" />
                <span>Propose Community Symbol</span>
              </h3>
              <button onClick={() => setShowCreateSymbolModal(false)} className="text-slate-400 hover:text-slate-200">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateSymbolSubmit} className="space-y-4 text-xs font-mono">
              <div>
                <label className="block text-slate-300 mb-1">Symbol Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Salt Miner Covenant"
                  value={newSymbolName}
                  onChange={(e) => setNewSymbolName(e.target.value)}
                  className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl p-2.5 text-slate-100 focus:outline-none focus:border-cyan-400"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Description / Mythic Meaning</label>
                <textarea
                  required
                  rows={3}
                  placeholder="Describe the shared symbol forged through convergence..."
                  value={newSymbolDesc}
                  onChange={(e) => setNewSymbolDesc(e.target.value)}
                  className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl p-2.5 text-slate-100 focus:outline-none focus:border-cyan-400"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowCreateSymbolModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 font-bold hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-cyan-400 text-slate-950 font-bold hover:bg-cyan-300 shadow-md"
                >
                  Propose Symbol
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
