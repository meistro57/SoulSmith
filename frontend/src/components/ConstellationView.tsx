// frontend/src/components/ConstellationView.tsx
import React, { useCallback, useEffect, useState } from 'react';
import type { AwakeningStage, Constellation, ConstellationStageInfo } from '../types';
import { apiClient } from '../lib/api';
import { Sparkles, Compass, Shield, GitCommit, Layers, PlusCircle, ArrowRight, CheckCircle2, Link as LinkIcon } from 'lucide-react';

interface ConstellationViewProps {
  currentSoulName: string;
  onSelectAspect?: (aspectName: string) => void;
}

const STAGES: { stage: AwakeningStage; label: string }[] = [
  { stage: 'veiled', label: '1. Veiled' },
  { stage: 'echoing', label: '2. Echoing' },
  { stage: 'recognizing', label: '3. Recognizing' },
  { stage: 'resonant', label: '4. Resonant' },
  { stage: 'woven', label: '5. Woven' },
  { stage: 'lucid', label: '6. Lucid' },
];

export const ConstellationView: React.FC<ConstellationViewProps> = ({
  currentSoulName,
  onSelectAspect,
}) => {
  const [constellation, setConstellation] = useState<Constellation | null>(null);
  const [stageInfo, setStageInfo] = useState<ConstellationStageInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeAspectId, setActiveAspectId] = useState<string | null>(null);

  // New Aspect Form State
  const [showAspectModal, setShowAspectModal] = useState(false);
  const [newAspectName, setNewAspectName] = useState('');
  const [newCalling, setNewCalling] = useState('');
  const [newOrigin, setNewOrigin] = useState('');
  const [newEra, setNewEra] = useState('Ancient Era');

  // New Bond Form State
  const [showBondModal, setShowBondModal] = useState(false);
  const [sourceAspectId, setSourceAspectId] = useState('');
  const [targetAspectId, setTargetAspectId] = useState('');
  const [bondType, setBondType] = useState('memory_echo');
  const [bondDescription, setBondDescription] = useState('');

  const fetchConstellationData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiClient.getConstellation();
      setConstellation(res.constellation);
      setStageInfo(res.stage_info);

      // Set active aspect if matching current soul name or pick first
      const matched = res.constellation.aspects.find(
        (a) => a.aspect_name.toLowerCase() === currentSoulName.toLowerCase()
      );
      if (matched) {
        setActiveAspectId(matched.id);
      } else if (res.constellation.aspects.length > 0) {
        setActiveAspectId(res.constellation.aspects[0].id);
      }
    } catch (err) {
      console.error('Failed to load constellation data', err);
    } finally {
      setLoading(false);
    }
  }, [currentSoulName]);

  useEffect(() => {
    fetchConstellationData();
  }, [fetchConstellationData]);

  const handleCreateAspect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!constellation || !newAspectName || !newCalling) return;
    try {
      await apiClient.createAspect({
        constellation_id: constellation.id,
        aspect_name: newAspectName,
        calling: newCalling,
        origin: newOrigin || 'Uncharted World Boundary',
        era_or_world: newEra,
      });
      setNewAspectName('');
      setNewCalling('');
      setNewOrigin('');
      setShowAspectModal(false);
      await fetchConstellationData();
    } catch (err) {
      console.error('Failed to create aspect', err);
    }
  };

  const handleCreateBond = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!constellation || !sourceAspectId || !targetAspectId || !bondDescription) return;
    try {
      await apiClient.createCrossAspectBond({
        constellation_id: constellation.id,
        source_aspect_id: sourceAspectId,
        target_aspect_id: targetAspectId,
        bond_type: bondType,
        description: bondDescription,
      });
      setBondDescription('');
      setShowBondModal(false);
      await fetchConstellationData();
    } catch (err) {
      console.error('Failed to create cross-aspect bond', err);
    }
  };

  const handleAdvanceStage = async (nextStage?: AwakeningStage) => {
    if (!constellation) return;
    try {
      await apiClient.advanceAwakening({
        constellation_id: constellation.id,
        target_stage: nextStage,
      });
      await fetchConstellationData();
    } catch (err) {
      console.error('Failed to advance awakening stage', err);
    }
  };

  const getAspectNameById = (id: string): string => {
    const asp = constellation?.aspects.find((a) => a.id === id);
    return asp ? asp.aspect_name : 'Unknown Aspect';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px] text-indigo-300">
        <Sparkles className="w-8 h-8 animate-spin mr-3 text-amber-400" />
        <span className="text-lg font-mono">Tracing Soul Constellation Resonance...</span>
      </div>
    );
  }

  if (!constellation) {
    return (
      <div className="p-8 text-center text-slate-400">
        No active Constellation found. Please check backend connection.
      </div>
    );
  }

  const currentStageIndex = STAGES.findIndex((s) => s.stage === constellation.awakening_stage);

  return (
    <div className="max-w-7xl mx-auto space-y-8 p-4 md:p-6 text-slate-100">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950/80 to-slate-900 border border-indigo-500/30 p-6 md:p-8 shadow-2xl">
        <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
          <Sparkles className="w-64 h-64 text-indigo-300" />
        </div>

        <div className="relative z-10 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="flex items-center space-x-3 text-amber-400 font-mono text-sm tracking-wider uppercase">
                <Sparkles className="w-4 h-4" />
                <span>Phase 4 • Mythic Soul Constellation</span>
              </div>
              <h1 className="text-3xl md:text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-amber-200 via-indigo-200 to-sky-300">
                {constellation.name}
              </h1>
            </div>

            <button
              onClick={() => setShowAspectModal(true)}
              className="inline-flex items-center px-4 py-2.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 border border-amber-400/40 text-amber-200 font-medium transition-all shadow-lg hover:shadow-amber-500/10 cursor-pointer"
            >
              <PlusCircle className="w-4 h-4 mr-2" />
              Manifest New Aspect
            </button>
          </div>

          <p className="text-slate-300 text-sm md:text-base max-w-3xl leading-relaxed">
            <span className="text-amber-300 font-semibold">Unresolved Constellation Pattern:</span>{' '}
            {constellation.unresolved_pattern}
          </p>

          {/* Awakening Stage Tracker */}
          <div className="mt-6 pt-6 border-t border-indigo-500/20 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase tracking-widest text-indigo-300">
                Awakening Stage Progress
              </span>
              <span className="text-xs font-mono text-amber-400 font-bold uppercase">
                {stageInfo?.title || constellation.awakening_stage}
              </span>
            </div>

            {/* Stage Bar */}
            <div className="grid grid-cols-6 gap-2">
              {STAGES.map((s, idx) => {
                const isActive = idx <= currentStageIndex;
                const isCurrent = idx === currentStageIndex;
                return (
                  <button
                    key={s.stage}
                    onClick={() => handleAdvanceStage(s.stage)}
                    className={`py-2 px-2 rounded-lg text-xs font-mono text-center transition-all border cursor-pointer ${
                      isCurrent
                        ? 'bg-amber-500/30 border-amber-400 text-amber-200 shadow-md shadow-amber-500/20 font-bold ring-2 ring-amber-400/50'
                        : isActive
                        ? 'bg-indigo-950/60 border-indigo-500/40 text-indigo-200'
                        : 'bg-slate-900/40 border-slate-800 text-slate-500 hover:border-slate-700'
                    }`}
                  >
                    {s.label}
                  </button>
                );
              })}
            </div>

            {/* Current Stage Description */}
            <div className="bg-slate-900/60 border border-indigo-500/20 rounded-xl p-4 flex items-start space-x-3">
              <Compass className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-semibold text-amber-300">
                  Stage {currentStageIndex + 1}: {stageInfo?.title}
                </div>
                <p className="text-xs text-slate-300 mt-1">{stageInfo?.description}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Playable Aspects Column (2 Columns wide) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
              <Shield className="w-5 h-5 text-indigo-400" />
              <span>Manifested Aspects Across Eras</span>
            </h2>
            <span className="text-xs font-mono text-indigo-300 bg-indigo-950/80 px-2.5 py-1 rounded-full border border-indigo-500/30">
              {constellation.aspects.length} Playable Perspectives
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {constellation.aspects.map((aspect) => {
              const isSelected = aspect.id === activeAspectId;

              return (
                <div
                  key={aspect.id}
                  className={`relative rounded-xl p-5 transition-all border flex flex-col justify-between ${
                    isSelected
                      ? 'bg-gradient-to-b from-indigo-950/90 to-slate-900 border-amber-400/60 shadow-xl shadow-amber-500/10 ring-1 ring-amber-400/40'
                      : 'bg-slate-900/80 border-slate-800 hover:border-indigo-500/40'
                  }`}
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="text-xs font-mono text-amber-400 uppercase tracking-wider">
                          {aspect.era_or_world}
                        </div>
                        <h3 className="text-lg font-bold text-slate-100 mt-0.5">
                          {aspect.aspect_name}
                        </h3>
                      </div>
                      {isSelected ? (
                        <span className="inline-flex items-center text-xs font-mono text-amber-300 bg-amber-500/20 px-2 py-0.5 rounded-full border border-amber-400/30">
                          <CheckCircle2 className="w-3 h-3 mr-1 text-amber-400" /> Active
                        </span>
                      ) : (
                        <button
                          onClick={() => {
                            setActiveAspectId(aspect.id);
                            if (onSelectAspect) onSelectAspect(aspect.aspect_name);
                          }}
                          className="text-xs font-mono text-indigo-300 hover:text-amber-300 bg-indigo-950/50 hover:bg-indigo-900/60 px-2.5 py-1 rounded-lg border border-indigo-500/30 transition-all cursor-pointer"
                        >
                          Switch
                        </button>
                      )}
                    </div>

                    <div className="space-y-1 text-xs text-slate-300">
                      <div>
                        <span className="text-slate-400">Calling:</span>{' '}
                        <span className="text-slate-200 font-medium">{aspect.calling}</span>
                      </div>
                      <div>
                        <span className="text-slate-400">Origin:</span>{' '}
                        <span className="text-slate-200">{aspect.origin}</span>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-indigo-500/15 flex items-center justify-between text-xs text-slate-400 font-mono">
                    <span>Aspect ID: #{aspect.id.substring(0, 6)}</span>
                    <span className="text-indigo-400">Shared Deep Threads</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Deep Threads Section */}
          <div className="bg-slate-900/80 border border-indigo-500/30 rounded-xl p-6 space-y-4">
            <h3 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
              <Layers className="w-5 h-5 text-amber-400" />
              <span>Deep Threads (Shared Cross-Aspect Patterns)</span>
            </h3>
            <p className="text-xs text-slate-400">
              Patterns that persist across multiple Aspects, eras, or probable history paths. They
              are inferred from Chronicle evidence and cross-era bonds.
            </p>

            <div className="space-y-2">
              {constellation.deep_threads.map((thread, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between bg-indigo-950/40 border border-indigo-500/20 rounded-lg p-3 text-sm text-slate-200"
                >
                  <div className="flex items-center space-x-3">
                    <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                    <span className="font-medium text-amber-200">{thread}</span>
                  </div>
                  <span className="text-xs font-mono text-indigo-300 bg-indigo-900/40 px-2 py-0.5 rounded border border-indigo-500/30">
                    Active Deep Thread
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Sidebar Column: Anchors & Bonds */}
        <div className="space-y-6">
          {/* Constellation Anchors */}
          <div className="bg-slate-900/80 border border-indigo-500/30 rounded-xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
                <LinkIcon className="w-5 h-5 text-sky-400" />
                <span>Constellation Anchors</span>
              </h3>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Mythic relics that awaken across eras, binding multiple Aspects to one shared history.
            </p>

            <div className="space-y-3">
              {constellation.anchors.map((anchor) => (
                <div
                  key={anchor.id}
                  className="bg-slate-950/60 border border-sky-500/30 rounded-lg p-4 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-sky-200 text-sm">{anchor.anchor_name}</h4>
                    <span className="text-xs font-mono uppercase text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-400/30">
                      {anchor.status}
                    </span>
                  </div>
                  <div className="text-xs text-slate-300">
                    <span className="text-slate-400">Relic Form:</span> {anchor.relic_form}
                  </div>
                  <div className="text-xs text-slate-400 pt-1">
                    Connected to {anchor.connected_aspect_ids.length} Aspect(s) across time.
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Cross-Aspect Bonds */}
          <div className="bg-slate-900/80 border border-indigo-500/30 rounded-xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
                <GitCommit className="w-5 h-5 text-indigo-400" />
                <span>Cross-Aspect Bonds</span>
              </h3>
              <button
                onClick={() => {
                  if (constellation.aspects.length >= 2) {
                    setSourceAspectId(constellation.aspects[0].id);
                    setTargetAspectId(constellation.aspects[1].id);
                  }
                  setShowBondModal(true);
                }}
                className="text-xs font-mono text-amber-300 hover:text-amber-200 bg-amber-500/20 hover:bg-amber-500/30 px-2.5 py-1 rounded-lg border border-amber-400/40 transition-all cursor-pointer"
              >
                + Weave Bond
              </button>
            </div>

            <div className="space-y-3">
              {constellation.bonds.map((bond) => (
                <div
                  key={bond.id}
                  className="bg-indigo-950/30 border border-indigo-500/20 rounded-lg p-3 space-y-2"
                >
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-amber-300 font-bold uppercase">{bond.bond_type}</span>
                    <span className="text-slate-400">
                      {getAspectNameById(bond.source_aspect_id)} <ArrowRight className="w-3 h-3 inline text-indigo-400 mx-1" /> {getAspectNameById(bond.target_aspect_id)}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 italic">{bond.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Manifest New Aspect Modal */}
      {showAspectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="bg-slate-900 border border-amber-400/40 rounded-2xl p-6 max-w-md w-full space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-indigo-500/20 pb-3">
              <h3 className="text-lg font-bold text-amber-300 flex items-center">
                <Sparkles className="w-5 h-5 mr-2 text-amber-400" /> Manifest New Aspect
              </h3>
              <button
                onClick={() => setShowAspectModal(false)}
                className="text-slate-400 hover:text-slate-200 text-sm font-mono cursor-pointer"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateAspect} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">Aspect Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Seer Lyra of the Void"
                  value={newAspectName}
                  onChange={(e) => setNewAspectName(e.target.value)}
                  className="w-full bg-slate-950 border border-indigo-500/30 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-amber-400"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">Calling</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Keeper of Unwritten Stars"
                  value={newCalling}
                  onChange={(e) => setNewCalling(e.target.value)}
                  className="w-full bg-slate-950 border border-indigo-500/30 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-amber-400"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">Origin Location</label>
                <input
                  type="text"
                  placeholder="e.g., Threshold of the Outer Veils"
                  value={newOrigin}
                  onChange={(e) => setNewOrigin(e.target.value)}
                  className="w-full bg-slate-950 border border-indigo-500/30 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-amber-400"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">Era or World Perspective</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Future Era (Age of Silence)"
                  value={newEra}
                  onChange={(e) => setNewEra(e.target.value)}
                  className="w-full bg-slate-950 border border-indigo-500/30 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-amber-400"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowAspectModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono text-xs cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs cursor-pointer"
                >
                  Manifest Aspect
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Weave Cross-Aspect Bond Modal */}
      {showBondModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="bg-slate-900 border border-indigo-500/40 rounded-2xl p-6 max-w-md w-full space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-indigo-500/20 pb-3">
              <h3 className="text-lg font-bold text-indigo-300 flex items-center">
                <GitCommit className="w-5 h-5 mr-2 text-indigo-400" /> Weave Cross-Aspect Bond
              </h3>
              <button
                onClick={() => setShowBondModal(false)}
                className="text-slate-400 hover:text-slate-200 text-sm font-mono cursor-pointer"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateBond} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">Source Aspect</label>
                <select
                  value={sourceAspectId}
                  onChange={(e) => setSourceAspectId(e.target.value)}
                  className="w-full bg-slate-950 border border-indigo-500/30 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-400"
                >
                  {constellation.aspects.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.aspect_name} ({a.era_or_world})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">Target Aspect</label>
                <select
                  value={targetAspectId}
                  onChange={(e) => setTargetAspectId(e.target.value)}
                  className="w-full bg-slate-950 border border-indigo-500/30 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-400"
                >
                  {constellation.aspects.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.aspect_name} ({a.era_or_world})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">Bond Type</label>
                <select
                  value={bondType}
                  onChange={(e) => setBondType(e.target.value)}
                  className="w-full bg-slate-950 border border-indigo-500/30 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-400"
                >
                  <option value="memory_echo">Memory Echo</option>
                  <option value="scar">Shared Scar</option>
                  <option value="promise">Unbroken Promise</option>
                  <option value="relic_anchor">Relic Anchor</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">Bond Description</label>
                <textarea
                  required
                  rows={3}
                  placeholder="Describe the shared scar, echo, or promise connecting these Aspects across eras..."
                  value={bondDescription}
                  onChange={(e) => setBondDescription(e.target.value)}
                  className="w-full bg-slate-950 border border-indigo-500/30 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-400"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowBondModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono text-xs cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs cursor-pointer"
                >
                  Weave Bond
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
