// frontend/src/components/RelicLedgerView.tsx
import React, { useCallback, useEffect, useState } from 'react';
import type { Relic, RelicEvent, RelicStage } from '../types';
import { apiClient } from '../lib/api';
import { Sparkles, Shield, Flame, Wrench, GitCommit, HelpCircle, History, AlertTriangle, ChevronRight, X } from 'lucide-react';

interface RelicLedgerViewProps {
  soulName: string;
}

export const RelicLedgerView: React.FC<RelicLedgerViewProps> = ({ soulName }) => {
  const [relics, setRelics] = useState<Relic[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeModal, setActiveModal] = useState<'attune' | 'overdraw' | 'repair' | 'transfigure' | 'history' | null>(null);
  const [selectedRelic, setSelectedRelic] = useState<Relic | null>(null);
  const [relicHistory, setRelicHistory] = useState<RelicEvent[]>([]);

  // Form Inputs
  const [narrativeCondition, setNarrativeCondition] = useState('');
  const [evidenceSummary, setEvidenceSummary] = useState('');
  const [intensityBoost, setIntensityBoost] = useState('Ascendancy Score +2');
  const [anchorName, setAnchorName] = useState('');
  const [transfiguredForm, setTransfiguredForm] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchRelics = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiClient.listRelics(soulName);
      setRelics(res.relics);
    } catch (err) {
      console.error('Failed to load relics:', err);
    } finally {
      setLoading(false);
    }
  }, [soulName]);

  useEffect(() => {
    fetchRelics();
  }, [fetchRelics]);

  const handleOpenHistory = async (relic: Relic) => {
    setSelectedRelic(relic);
    setActiveModal('history');
    try {
      const res = await apiClient.getRelicHistory(relic.id);
      setRelicHistory(res.history);
    } catch (err) {
      console.error('Failed to load relic history:', err);
    }
  };

  const handleAttuneSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRelic || !narrativeCondition || !evidenceSummary) return;
    setSubmitting(true);
    try {
      await apiClient.attuneRelicNarrative({
        relic_id: selectedRelic.id,
        soul_id: soulName,
        narrative_condition_met: narrativeCondition,
        chronicle_evidence_summary: evidenceSummary,
      });
      setActiveModal(null);
      setNarrativeCondition('');
      setEvidenceSummary('');
      fetchRelics();
    } catch (err) {
      console.error('Failed to attune relic:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleOverdrawSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRelic) return;
    setSubmitting(true);
    try {
      await apiClient.overdrawRelic({
        relic_id: selectedRelic.id,
        soul_id: soulName,
        intensity_boost: intensityBoost,
      });
      setActiveModal(null);
      fetchRelics();
    } catch (err) {
      console.error('Failed to overdraw relic:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleRepairSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRelic || !evidenceSummary) return;
    setSubmitting(true);
    try {
      await apiClient.repairRelic({
        relic_id: selectedRelic.id,
        soul_id: soulName,
        repair_evidence_summary: evidenceSummary,
      });
      setActiveModal(null);
      setEvidenceSummary('');
      fetchRelics();
    } catch (err) {
      console.error('Failed to repair relic:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleTransfigureSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRelic || !anchorName || !transfiguredForm) return;
    setSubmitting(true);
    try {
      await apiClient.transfigureRelic({
        relic_id: selectedRelic.id,
        soul_id: soulName,
        anchor_name: anchorName,
        transfigured_form: transfiguredForm,
      });
      setActiveModal(null);
      setAnchorName('');
      setTransfiguredForm('');
      fetchRelics();
    } catch (err) {
      console.error('Failed to transfigure relic:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const getStageBadge = (stage: RelicStage) => {
    switch (stage) {
      case 'Dormant':
        return 'bg-slate-800/80 text-slate-400 border-slate-700';
      case 'Remembered':
        return 'bg-cyan-950/80 text-cyan-300 border-cyan-500/50 shadow-cyan-500/10';
      case 'Awakened':
        return 'bg-amber-950/80 text-amber-300 border-amber-400/60 shadow-amber-400/20';
      case 'Overdrawn':
        return 'bg-orange-950/90 text-orange-300 border-orange-500/80 shadow-orange-500/30 animate-pulse';
      case 'Fractured':
        return 'bg-red-950/90 text-red-300 border-red-500/90 shadow-red-500/40 ring-1 ring-red-500/50';
      case 'Transfigured':
        return 'bg-indigo-950/90 text-indigo-200 border-indigo-400/80 shadow-indigo-500/30';
      default:
        return 'bg-slate-800 text-slate-300';
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-slate-950 to-indigo-950 border border-amber-400/30 p-6 md:p-8 shadow-2xl">
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 space-y-3">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-400/10 border border-amber-400/30 text-amber-300 text-xs font-mono">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Phase 6: Relic Recognition & Constellation Anchors</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-amber-100 via-indigo-100 to-amber-200">
            Relic Recognition Ledger
          </h1>
          <p className="text-slate-300 text-xs md:text-sm max-w-3xl leading-relaxed font-serif">
            Relics in SoulSmith do not level through usage counters. They recognize the bearer through narrative conditions, deep thread choices, and Chronicle evidence. Overdrawn power risks structural fracture, while transfigured relics anchor memories across the Constellation.
          </p>
        </div>
      </div>

      {/* Relics Cards Deck */}
      {loading ? (
        <div className="text-center py-12 font-mono text-slate-400 animate-pulse">
          Consulting Chronicle Relic Vault...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {relics.map((relic) => (
            <div
              key={relic.id}
              className={`bg-slate-900/90 backdrop-blur-md rounded-2xl border p-6 flex flex-col justify-between space-y-5 shadow-xl transition-all duration-300 hover:border-amber-400/50 ${
                relic.is_anchor ? 'border-indigo-400/60 shadow-indigo-500/10' : 'border-indigo-500/20'
              }`}
            >
              <div className="space-y-4">
                {/* Header & Badges */}
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                      <Shield className="w-4 h-4 text-amber-400 shrink-0" />
                      <span>{relic.name}</span>
                    </h3>
                    {relic.is_anchor && (
                      <span className="inline-block text-[10px] font-mono font-bold text-indigo-300 bg-indigo-950 px-2 py-0.5 rounded border border-indigo-500/40 mt-1">
                        ❖ Constellation Anchor
                      </span>
                    )}
                  </div>
                  <span className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold border ${getStageBadge(relic.stage)}`}>
                    {relic.stage}
                  </span>
                </div>

                {/* Evocative Dormant Question */}
                <div className="p-3 rounded-xl bg-slate-950/80 border border-indigo-500/20 space-y-1.5">
                  <div className="flex items-center space-x-1.5 text-[11px] font-mono text-amber-300">
                    <HelpCircle className="w-3.5 h-3.5 shrink-0" />
                    <span className="font-bold">Evocative Question</span>
                  </div>
                  <p className="text-xs text-slate-300 italic font-serif leading-relaxed">
                    "{relic.evocative_question}"
                  </p>
                </div>

                {/* Active Effect & Consequences */}
                <div className="space-y-2 text-xs">
                  <div className="space-y-1">
                    <span className="font-mono text-slate-400 text-[11px]">Active Move / Effect:</span>
                    <p className="text-slate-200 bg-slate-950/40 p-2 rounded-lg border border-slate-800">
                      {relic.effect}
                    </p>
                  </div>

                  <div className="space-y-1">
                    <span className="font-mono text-amber-400 text-[11px] flex items-center gap-1">
                      <AlertTriangle className="w-3.5 h-3.5" /> Overdraw Risk:
                    </span>
                    <p className="text-amber-200/90 bg-amber-950/20 p-2 rounded-lg border border-amber-500/20">
                      {relic.overdraw_consequence}
                    </p>
                  </div>
                </div>

                {/* Cross-Aspect Forms */}
                {Object.keys(relic.cross_aspect_forms).length > 0 && (
                  <div className="space-y-1.5 pt-1">
                    <span className="text-[11px] font-mono text-indigo-300">Cross-Aspect Era Forms:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {Object.entries(relic.cross_aspect_forms).map(([era, formName]) => (
                        <span key={era} className="text-[10px] font-mono bg-indigo-950/60 border border-indigo-500/30 text-indigo-200 px-2 py-0.5 rounded-full">
                          {era}: <strong className="text-amber-200">{formName}</strong>
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Action Buttons Footer */}
              <div className="pt-4 border-t border-indigo-500/20 space-y-2">
                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  {relic.stage === 'Fractured' ? (
                    <button
                      onClick={() => {
                        setSelectedRelic(relic);
                        setActiveModal('repair');
                      }}
                      className="col-span-2 py-2 px-3 bg-red-950/80 hover:bg-red-900 border border-red-500/60 text-red-200 font-bold rounded-xl flex items-center justify-center gap-1.5 transition cursor-pointer shadow-lg shadow-red-950/50"
                    >
                      <Wrench className="w-3.5 h-3.5 text-red-400" />
                      <span>Mend Fracture</span>
                    </button>
                  ) : (
                    <>
                      <button
                        onClick={() => {
                          setSelectedRelic(relic);
                          setActiveModal('attune');
                        }}
                        className="py-2 px-3 bg-amber-500/20 hover:bg-amber-500/30 border border-amber-400/40 text-amber-200 font-bold rounded-xl flex items-center justify-center gap-1 transition cursor-pointer"
                      >
                        <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                        <span>Attune</span>
                      </button>

                      <button
                        onClick={() => {
                          setSelectedRelic(relic);
                          setActiveModal('overdraw');
                        }}
                        className="py-2 px-3 bg-orange-950/60 hover:bg-orange-900/60 border border-orange-500/40 text-orange-300 font-bold rounded-xl flex items-center justify-center gap-1 transition cursor-pointer"
                      >
                        <Flame className="w-3.5 h-3.5 text-orange-400" />
                        <span>Overdraw</span>
                      </button>
                    </>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  {relic.stage !== 'Transfigured' && relic.stage !== 'Fractured' && (
                    <button
                      onClick={() => {
                        setSelectedRelic(relic);
                        setActiveModal('transfigure');
                      }}
                      className="py-1.5 px-3 bg-indigo-950/80 hover:bg-indigo-900/80 border border-indigo-500/40 text-indigo-200 font-bold rounded-xl flex items-center justify-center gap-1 transition cursor-pointer"
                    >
                      <GitCommit className="w-3.5 h-3.5 text-indigo-400" />
                      <span>Anchor</span>
                    </button>
                  )}

                  <button
                    onClick={() => handleOpenHistory(relic)}
                    className={`py-1.5 px-3 bg-slate-950 hover:bg-slate-800 border border-slate-700 text-slate-300 font-bold rounded-xl flex items-center justify-center gap-1 transition cursor-pointer ${
                      relic.stage === 'Transfigured' || relic.stage === 'Fractured' ? 'col-span-2' : ''
                    }`}
                  >
                    <History className="w-3.5 h-3.5 text-slate-400" />
                    <span>Chronicle</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Attune Modal */}
      {activeModal === 'attune' && selectedRelic && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="bg-slate-900 border border-amber-400/50 rounded-2xl p-6 max-w-lg w-full space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-indigo-500/20 pb-3">
              <h3 className="text-lg font-bold text-amber-200 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-amber-400" />
                <span>Attune Relic: {selectedRelic.name}</span>
              </h3>
              <button onClick={() => setActiveModal(null)} className="text-slate-400 hover:text-slate-200">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleAttuneSubmit} className="space-y-4 text-xs font-mono">
              <div>
                <label className="block text-slate-300 mb-1">Narrative Condition Met</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Answered the open question of the Salt Bell"
                  value={narrativeCondition}
                  onChange={(e) => setNarrativeCondition(e.target.value)}
                  className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl p-2.5 text-slate-100 focus:outline-none focus:border-amber-400"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Chronicle Evidence Summary</label>
                <textarea
                  required
                  rows={3}
                  placeholder="Describe the story moment in the chronicle that supports this relic attunement..."
                  value={evidenceSummary}
                  onChange={(e) => setEvidenceSummary(e.target.value)}
                  className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl p-2.5 text-slate-100 focus:outline-none focus:border-amber-400"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setActiveModal(null)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 font-bold hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-xl bg-amber-400 text-slate-950 font-bold hover:bg-amber-300 shadow-md"
                >
                  {submitting ? 'Attuning...' : 'Record Attunement'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Overdraw Modal */}
      {activeModal === 'overdraw' && selectedRelic && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="bg-slate-900 border border-orange-500/50 rounded-2xl p-6 max-w-lg w-full space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-orange-500/20 pb-3">
              <h3 className="text-lg font-bold text-orange-200 flex items-center gap-2">
                <Flame className="w-4 h-4 text-orange-400" />
                <span>Overdraw Power: {selectedRelic.name}</span>
              </h3>
              <button onClick={() => setActiveModal(null)} className="text-slate-400 hover:text-slate-200">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-3 bg-orange-950/50 border border-orange-500/30 rounded-xl text-xs text-orange-200 space-y-1">
              <p className="font-bold flex items-center gap-1">
                <AlertTriangle className="w-4 h-4 text-orange-400" /> Warning: Acute Strain & Fracture Risk
              </p>
              <p className="text-orange-300/90">
                Overdrawing forces immediate ascendancy (+1 Strain). If overdrawn twice without cleansing, the relic will **FRACTURE**!
              </p>
            </div>

            <form onSubmit={handleOverdrawSubmit} className="space-y-4 text-xs font-mono">
              <div>
                <label className="block text-slate-300 mb-1">Ascendancy Intensity Boost</label>
                <input
                  type="text"
                  required
                  value={intensityBoost}
                  onChange={(e) => setIntensityBoost(e.target.value)}
                  className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl p-2.5 text-slate-100 focus:outline-none focus:border-amber-400"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setActiveModal(null)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 font-bold hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-xl bg-orange-500 text-slate-950 font-bold hover:bg-orange-400 shadow-md"
                >
                  {submitting ? 'Overdrawing...' : 'Channel Overdrawn Power'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Repair Modal */}
      {activeModal === 'repair' && selectedRelic && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="bg-slate-900 border border-red-500/50 rounded-2xl p-6 max-w-lg w-full space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-red-500/20 pb-3">
              <h3 className="text-lg font-bold text-red-200 flex items-center gap-2">
                <Wrench className="w-4 h-4 text-red-400" />
                <span>Mend Fractured Relic: {selectedRelic.name}</span>
              </h3>
              <button onClick={() => setActiveModal(null)} className="text-slate-400 hover:text-slate-200">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleRepairSubmit} className="space-y-4 text-xs font-mono">
              <div>
                <label className="block text-slate-300 mb-1">Chronicle Repair Evidence</label>
                <textarea
                  required
                  rows={3}
                  placeholder="Provide the Thread integration or revelatory narrative choice that mends this shattered relic..."
                  value={evidenceSummary}
                  onChange={(e) => setEvidenceSummary(e.target.value)}
                  className="w-full bg-slate-950 border border-red-500/30 rounded-xl p-2.5 text-slate-100 focus:outline-none focus:border-red-400"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setActiveModal(null)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 font-bold hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-xl bg-red-500 text-slate-950 font-bold hover:bg-red-400 shadow-md"
                >
                  {submitting ? 'Mending...' : 'Mend Vessel & Restore Awakened State'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Transfigure Modal */}
      {activeModal === 'transfigure' && selectedRelic && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="bg-slate-900 border border-indigo-400/50 rounded-2xl p-6 max-w-lg w-full space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-indigo-500/20 pb-3">
              <h3 className="text-lg font-bold text-indigo-200 flex items-center gap-2">
                <GitCommit className="w-4 h-4 text-indigo-400" />
                <span>Transfigure Constellation Anchor: {selectedRelic.name}</span>
              </h3>
              <button onClick={() => setActiveModal(null)} className="text-slate-400 hover:text-slate-200">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleTransfigureSubmit} className="space-y-4 text-xs font-mono">
              <div>
                <label className="block text-slate-300 mb-1">Constellation Anchor Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Anchor of Sol Suns"
                  value={anchorName}
                  onChange={(e) => setAnchorName(e.target.value)}
                  className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl p-2.5 text-slate-100 focus:outline-none focus:border-indigo-400"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Transfigured Mythic Form Across Eras</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Starlight Beacon Prism"
                  value={transfiguredForm}
                  onChange={(e) => setTransfiguredForm(e.target.value)}
                  className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl p-2.5 text-slate-100 focus:outline-none focus:border-indigo-400"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setActiveModal(null)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 font-bold hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-xl bg-indigo-500 text-slate-950 font-bold hover:bg-indigo-400 shadow-md"
                >
                  {submitting ? 'Transfiguring...' : 'Transfigure into Constellation Anchor'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Relic Chronicle History Drawer */}
      {activeModal === 'history' && selectedRelic && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="bg-slate-900 border border-indigo-500/40 rounded-2xl p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-indigo-500/20 pb-3">
              <h3 className="text-lg font-bold text-amber-200 flex items-center gap-2">
                <History className="w-4 h-4 text-amber-400" />
                <span>Chronicle Evidence Ledger: {selectedRelic.name}</span>
              </h3>
              <button onClick={() => setActiveModal(null)} className="text-slate-400 hover:text-slate-200">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 font-mono text-xs">
              {relicHistory.length === 0 ? (
                <div className="text-slate-400 py-6 text-center">No recorded history events found.</div>
              ) : (
                relicHistory.map((evt) => (
                  <div key={evt.id} className="p-3.5 bg-slate-950 border border-indigo-500/20 rounded-xl space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-amber-300 flex items-center gap-1.5">
                        <ChevronRight className="w-3.5 h-3.5 text-amber-400" />
                        <span>Action: {evt.action.toUpperCase()}</span>
                      </span>
                      <span className="text-[10px] text-slate-400">
                        {evt.previous_stage} → <strong className="text-amber-200">{evt.new_stage}</strong>
                      </span>
                    </div>

                    <div className="text-slate-300 font-serif text-xs bg-slate-900/60 p-2 rounded border border-slate-800">
                      <strong>Condition:</strong> {evt.narrative_condition_met}
                    </div>

                    <div className="text-slate-400 text-[11px]">
                      <strong>Evidence:</strong> {evt.chronicle_evidence_summary}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
