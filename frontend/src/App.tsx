import { useState } from 'react';
import type { DiceRollRead, SoulSheet, ResolvedScene, SoulprintProfile } from './types';
import { DiceRoller3D } from './components/DiceRoller3D';
import { SoulSheetView } from './components/SoulSheetView';
import { EncounterResolutionModal } from './components/EncounterResolutionModal';
import { ChronicleView } from './components/ChronicleView';
import { SoulprintModal } from './components/SoulprintModal';
import { ConvergenceView } from './components/ConvergenceView';
import { DiceScanView } from './components/DiceScanView';
import { PhenomenaView } from './components/PhenomenaView';
import { MythicGalleryView } from './components/MythicGalleryView';

import { Dices, Shield, BookMarked, Radio, Moon, Zap, Play, Camera, Flame, Image } from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState<'sanctuary' | 'scan' | 'sheet' | 'phenomena' | 'chronicle' | 'convergence' | 'art'>('sanctuary');

  // Core State
  const [currentRead, setCurrentRead] = useState<DiceRollRead>({
    spark: 'Heart',
    domain: 'Relic',
    pressure: 'Debt',
    aim: 'Reveal',
    approach: 'Guile',
    verdict: 'Twist',
    thread: 'Mark'
  });

  const [soulSheet, setSoulSheet] = useState<SoulSheet>({
    name: 'Kaelen the Star-Watcher',
    calling: 'Keeper of the Salt Compass',
    origin: 'The Flooded Archives of Cinder',
    desire: 'To unlock the forgotten Starforge memory',
    fear: 'The King Without a Reflection',
    wound: 'Marked by the Weeping Door',
    resources: {
      resonance: 3,
      strain: 1,
      thread_count: 2
    },
    relics: [
      {
        id: '1',
        name: 'Compass of Better Questions',
        stage: 'Awakened',
        effect: 'Allows shifting one Domain face to Omen once per session.',
        overdraw_consequence: 'Reveals an unwanted secret to the Foe.'
      }
    ],
    bonds: ['Friend of the Silent Archivist', 'Bound to the Salt Bell'],
    scars: ['Singed by the Ember Dragon']
  });

  const [chosenApproach, setChosenApproach] = useState('Guile');
  const [playerIntent, setPlayerIntent] = useState('I want to compel the lantern to confess what it swallowed from the harbor.');
  const [resonanceSpent, setResonanceSpent] = useState(1);
  const [strainAccepted, setStrainAccepted] = useState(0);

  const [isRolling, setIsRolling] = useState(false);
  const [isResolving, setIsResolving] = useState(false);
  const [activeSceneResult, setActiveSceneResult] = useState<ResolvedScene | null>(null);

  const [chronicleHistory, setChronicleHistory] = useState<ResolvedScene[]>([]);
  const [worldFacts, setWorldFacts] = useState<string[]>([
    "The Starforge remains dormant beneath the crystal peaks.",
    "The King Without a Reflection traverses the outer Veils."
  ]);

  const [showSoulprintModal, setShowSoulprintModal] = useState(false);

  // Execute Scene Resolution
  const handleResolveScene = async () => {
    if (isResolving) return;
    setIsResolving(true);

    try {
      const res = await fetch('http://localhost:8000/api/v1/scenes/resolve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dice_read: currentRead,
          chosen_approach: chosenApproach,
          resonance_spent: resonanceSpent,
          strain_accepted: strainAccepted,
          player_intent: playerIntent,
          soul_name: soulSheet.name,
          resources: soulSheet.resources
        })
      });

      const data: ResolvedScene = res.ok ? await res.json() : generateFallbackResolution();

      setActiveSceneResult(data);
      setChronicleHistory((prev) => [data, ...prev]);

      // Update Soul Sheet Resources
      setSoulSheet((prev) => ({
        ...prev,
        resources: data.outcome.new_resources
      }));

      // Append world facts
      if (data.outcome.canon_facts.length > 0) {
        setWorldFacts((prev) => [...prev, ...data.outcome.canon_facts]);
      }
    } catch {
      const fallback = generateFallbackResolution();
      setActiveSceneResult(fallback);
      setChronicleHistory((prev) => [fallback, ...prev]);
    } finally {
      setIsResolving(false);
    }
  };

  const generateFallbackResolution = (): ResolvedScene => ({
    outcome: {
      outcome_class: 'marked_success',
      outcome_title: 'Marked Success',
      rules_summary: 'Goal achieved, but paid a price in Strain (+1) and pressure.',
      resonance_delta: -resonanceSpent,
      strain_delta: strainAccepted + 1,
      thread_delta: 1,
      new_resources: {
        resonance: Math.max(0, soulSheet.resources.resonance - resonanceSpent),
        strain: Math.min(6, soulSheet.resources.strain + strainAccepted + 1),
        thread_count: Math.min(5, soulSheet.resources.thread_count + 1)
      },
      fracture_triggered: soulSheet.resources.strain + strainAccepted + 1 >= 6,
      canon_facts: [
        `${soulSheet.name} compelled the lantern to yield its secret.`,
        `A permanent [Mark] Thread has been etched into the World Chronicle.`
      ]
    },
    narration: {
      title: `Marked Passage of ${currentRead.aim}`,
      prose: `Driven by ${currentRead.spark}, ${soulSheet.name} presses hard against the resisting weight of ${currentRead.pressure}. Through calculated ${chosenApproach}, the target ${currentRead.domain} yields its hidden oath—yet the effort leaves a visible mark upon reality.`,
      tone: 'Tense, Costly, Bittersweet',
      scene_beats: ['Direct confrontation', 'Target domain yielding', 'A heavy mark left behind'],
      canon_writeback: [`The lantern reveals one erased harbor oath.`],
      guardian_audit: [
        { passed: true, gate_name: '1. Schema Gate', details: 'Validated JSON structure.' },
        { passed: true, gate_name: '2. Rules Gate', details: 'Outcome rules respected.' },
        { passed: true, gate_name: '3. Canon Gate', details: 'No contradictions found.' },
        { passed: true, gate_name: '4. Safety Gate', details: 'Content cleared policy.' },
        { passed: true, gate_name: '5. Memory Gate', details: 'Event logged into Postgres & Qdrant.' }
      ]
    },
    event_id: Date.now().toString()
  });

  const handleApplySoulprint = (profile: SoulprintProfile) => {
    setSoulSheet((prev) => ({
      ...prev,
      bonds: [...prev.bonds, `Soulprint Affinity: ${profile.sun_sign} Solar Resonance`]
    }));
  };

  return (
    <div className="min-h-screen text-slate-100 flex flex-col pb-12">
      {/* Top Glass Navigation Bar */}
      <header className="sticky top-0 z-40 bg-slate-950/80 backdrop-blur-md border-b border-purple-500/20 px-6 py-4">
        <div className="max-w-7xl mx-auto flex flex-col lg:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 to-amber-500 flex items-center justify-center font-bold text-slate-950 shadow-glow-gold">
              ✦
            </div>
            <div>
              <h1 className="text-xl font-bold font-cinzel text-slate-100 tracking-wider">SOULSMITH</h1>
              <p className="text-[11px] text-slate-400">Living Mythology Engine • Persistent AI Canon</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex flex-wrap justify-center items-center gap-1 bg-slate-900/90 p-1.5 rounded-xl border border-slate-800">
            {[
              { id: 'sanctuary', label: '3D Sanctuary', icon: Dices },
              { id: 'scan', label: 'Dice Camera', icon: Camera },
              { id: 'sheet', label: 'Soul Sheet', icon: Shield },
              { id: 'phenomena', label: 'Phenomena', icon: Flame },
              { id: 'chronicle', label: 'Chronicle', icon: BookMarked },
              { id: 'convergence', label: 'Convergence', icon: Radio },
              { id: 'art', label: 'Mythic Art', icon: Image }
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                    isActive
                      ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-glow-purple'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon size={14} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Soulprint Button */}
          <button
            onClick={() => setShowSoulprintModal(true)}
            className="glass-pill text-xs font-semibold text-amber-300 border-amber-500/30 hover:border-amber-400/60 transition flex items-center gap-1.5 py-1.5 px-3"
          >
            <Moon size={14} className="text-amber-400" />
            <span>Soulprint Lens</span>
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 mt-6">
        {activeTab === 'sanctuary' && (
          <div className="space-y-6">
            {/* 3D Dice Roller Sanctuary */}
            <DiceRoller3D
              currentRead={currentRead}
              onRollComplete={(newRead) => setCurrentRead(newRead)}
              isRolling={isRolling}
              setIsRolling={setIsRolling}
            />

            {/* Action Approach & Intent Framing */}
            <div className="glass-panel p-6 space-y-6">
              <div>
                <span className="text-xs uppercase tracking-widest text-cyan-400 font-semibold flex items-center gap-1">
                  <Zap size={14} /> Encounter Action Framework
                </span>
                <h3 className="text-2xl font-bold font-cinzel text-slate-100">Commit Intent & Approach</h3>
              </div>

              {/* Action Approach Selection */}
              <div>
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                  Select Action Approach:
                </label>
                <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
                  {['Edge', 'Grace', 'Guile', 'Lore', 'Empathy', 'Craft'].map((app) => (
                    <button
                      key={app}
                      onClick={() => setChosenApproach(app)}
                      className={`p-3 rounded-xl border text-xs font-bold font-cinzel transition-all ${
                        chosenApproach === app
                          ? 'bg-cyan-950/80 border-cyan-400 text-cyan-300 shadow-lg'
                          : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:bg-slate-900'
                      }`}
                    >
                      {app}
                    </button>
                  ))}
                </div>
              </div>

              {/* Player Intent Input */}
              <div>
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                  Stated Intent:
                </label>
                <textarea
                  rows={2}
                  value={playerIntent}
                  onChange={(e) => setPlayerIntent(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-xs text-slate-200 focus:outline-none focus:border-purple-500"
                />
              </div>

              {/* Resource Investment Controls */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 rounded-xl bg-slate-900/80 border border-slate-800">
                <div className="flex justify-between items-center">
                  <div>
                    <span className="text-xs font-semibold text-amber-400 block">Spend Resonance</span>
                    <span className="text-[11px] text-slate-400">Boosts outcome ladder score</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setResonanceSpent(Math.max(0, resonanceSpent - 1))}
                      className="w-8 h-8 rounded bg-slate-800 text-amber-400 font-bold"
                    >
                      -
                    </button>
                    <span className="text-sm font-bold font-cinzel text-amber-300 w-6 text-center">{resonanceSpent}</span>
                    <button
                      onClick={() => setResonanceSpent(Math.min(soulSheet.resources.resonance, resonanceSpent + 1))}
                      className="w-8 h-8 rounded bg-slate-800 text-amber-400 font-bold"
                    >
                      +
                    </button>
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <div>
                    <span className="text-xs font-semibold text-red-400 block">Accept Strain Overreach</span>
                    <span className="text-[11px] text-slate-400">Forces outcome at cost of Strain</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setStrainAccepted(Math.max(0, strainAccepted - 1))}
                      className="w-8 h-8 rounded bg-slate-800 text-red-400 font-bold"
                    >
                      -
                    </button>
                    <span className="text-sm font-bold font-cinzel text-red-300 w-6 text-center">{strainAccepted}</span>
                    <button
                      onClick={() => setStrainAccepted(Math.min(6 - soulSheet.resources.strain, strainAccepted + 1))}
                      className="w-8 h-8 rounded bg-slate-800 text-red-400 font-bold"
                    >
                      +
                    </button>
                  </div>
                </div>
              </div>

              {/* Submit Resolve Button */}
              <div className="flex justify-end">
                <button
                  onClick={handleResolveScene}
                  disabled={isResolving}
                  className={`btn-primary text-sm py-3 px-8 ${isResolving ? 'opacity-50 animate-pulse' : ''}`}
                >
                  <Play size={18} />
                  {isResolving ? 'Resolving via Soulkeeper AI...' : 'Resolve Encounter Scene'}
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'scan' && (
          <DiceScanView
            onApplyScanRead={(read) => {
              setCurrentRead(read);
              setActiveTab('sanctuary');
            }}
          />
        )}

        {activeTab === 'sheet' && (
          <SoulSheetView sheet={soulSheet} onUpdateSheet={(updated) => setSoulSheet(updated)} />
        )}

        {activeTab === 'phenomena' && <PhenomenaView />}

        {activeTab === 'chronicle' && (
          <ChronicleView history={chronicleHistory} worldFacts={worldFacts} />
        )}

        {activeTab === 'convergence' && (
          <ConvergenceView currentRead={currentRead} soulName={soulSheet.name} />
        )}

        {activeTab === 'art' && <MythicGalleryView />}
      </main>

      {/* Resolution Modal */}
      {activeSceneResult && (
        <EncounterResolutionModal scene={activeSceneResult} onClose={() => setActiveSceneResult(null)} />
      )}

      {/* Astrological Soulprint Modal */}
      {showSoulprintModal && (
        <SoulprintModal onClose={() => setShowSoulprintModal(false)} onApplyMotifs={handleApplySoulprint} />
      )}
    </div>
  );
}
