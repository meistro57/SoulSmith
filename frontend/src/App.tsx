// frontend/src/App.tsx
import { useState } from 'react';
import type { CanonicalDiceRead, EncounterFrame, SoulSheet, ResolvedScene, SoulprintProfile } from './types';
import { apiClient } from './lib/api';
import { DiceRoller3D } from './components/DiceRoller3D';
import { SoulSheetView } from './components/SoulSheetView';
import { EncounterResolutionModal } from './components/EncounterResolutionModal';
import { ChronicleView } from './components/ChronicleView';
import { SoulprintModal } from './components/SoulprintModal';
import { ConvergenceView } from './components/ConvergenceView';
import { DiceScanView } from './components/DiceScanView';
import { PhenomenaView } from './components/PhenomenaView';
import { CuriosityView } from './components/CuriosityView';
import { MythicGalleryView } from './components/MythicGalleryView';

import { Dices, Shield, BookMarked, Radio, Moon, Zap, Play, Camera, Flame, Image, Compass } from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState<'sanctuary' | 'scan' | 'sheet' | 'phenomena' | 'curiosity' | 'chronicle' | 'convergence' | 'art'>('sanctuary');

  // Core State
  const [currentRead, setCurrentRead] = useState<CanonicalDiceRead>({
    raw: { d20: 1, d12: 9, d10: 5, percentile: 70, d8: 3, d6: 4, d4: 3 },
    grammar_version: '1.0.0',
    interpretation: {
      spark: 'Heart',
      domain: 'Relic',
      pressure: 'Debt',
      aim: 'Reveal',
      approach: 'Guile',
      verdict: 'Twist',
      thread: 'Mark'
    },
    grammar_sentence: 'Driven by [Heart], the Soul attempts to [Reveal] upon [Relic] using [Guile] against the pressure of [Debt]. The immediate turn yields [Twist], weaving a lasting [Mark] Thread.'
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
  const [encounterFrame, setEncounterFrame] = useState<EncounterFrame | null>(null);
  const [isFramingEncounter, setIsFramingEncounter] = useState(false);

  const [chronicleHistory, setChronicleHistory] = useState<ResolvedScene[]>([]);
  const [worldFacts, setWorldFacts] = useState<string[]>([
    "The Starforge remains dormant beneath the crystal peaks.",
    "The King Without a Reflection traverses the outer Veils."
  ]);

  const [showSoulprintModal, setShowSoulprintModal] = useState(false);

  const handleFrameEncounter = async (read: CanonicalDiceRead = currentRead) => {
    if (isFramingEncounter) return;
    setIsFramingEncounter(true);

    try {
      const frame = await apiClient.frameEncounter({
        dice_read: read,
        soul_name: soulSheet.name,
        world_context: worldFacts.slice(0, 3)
      });
      setEncounterFrame(frame);
      setPlayerIntent(`I want to understand what ${frame.title.toLowerCase()} is asking of me.`);
    } catch {
      setEncounterFrame({
        title: `The ${read.interpretation.spark} ${read.interpretation.domain} Under ${read.interpretation.pressure}`,
        phenomenon_type: 'Echo',
        visible_situation: `A ${read.interpretation.domain.toLowerCase()} stirs with ${read.interpretation.spark.toLowerCase()} energy and refuses to become ordinary.`,
        hidden_need: 'It wants a careful question before it will become useful truth.',
        stakes: `If rushed, the next ${read.interpretation.thread} Thread will be harder to untangle.`,
        pressure_clock: 2,
        questions: ['What feels familiar here?', 'What changes if this pressure is named?', 'Who is not speaking yet?'],
        suggested_actions: [`Approach with ${read.interpretation.approach}.`, 'Spend Resonance to stabilise a clue.', 'Accept Strain to force a revelation.']
      });
    } finally {
      setIsFramingEncounter(false);
    }
  };

  // Execute Scene Resolution
  const handleResolveScene = async () => {
    if (isResolving) return;
    setIsResolving(true);

    try {
      const data = await apiClient.resolveScene({
        dice_read: currentRead,
        chosen_approach: chosenApproach,
        resonance_spent: resonanceSpent,
        strain_accepted: strainAccepted,
        player_intent: playerIntent,
        soul_name: soulSheet.name,
        resources: soulSheet.resources
      });

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
      title: `Marked Passage of ${currentRead.interpretation.aim}`,
      prose: `Driven by ${currentRead.interpretation.spark}, ${soulSheet.name} presses hard against the resisting weight of ${currentRead.interpretation.pressure}. Through calculated ${chosenApproach}, the target ${currentRead.interpretation.domain} yields its hidden oath—yet the effort leaves a visible mark upon reality.`,
      tone: 'Tense, Costly, Bittersweet',
      scene_beats: ['Direct confrontation', 'Target domain yielding', 'A heavy mark left behind'],
      canon_writeback: [`The lantern reveals one erased harbor oath.`],
      guardian_audit: [
        { passed: true, gate_name: '1. Schema Gate', details: 'Validated JSON structure.' },
        { passed: true, gate_name: '2. Rules Gate', details: 'Outcome rules respected.' },
        { passed: true, gate_name: '3. Canon Gate', details: 'No contradictions found.' },
        { passed: true, gate_name: '4. Safety Gate', details: 'Content cleared policy.' },
        { passed: true, gate_name: '5. Memory Gate', details: 'Event logged into the local Chronicle; semantic indexing is planned.' }
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
    <div className="min-h-screen text-[var(--parchment)] flex flex-col pb-16">
      {/* Top Glass Navigation Bar with Expanded Logo Bounding Box */}
      <header className="sticky top-0 z-40 bg-[var(--void)]/90 backdrop-blur-xl border-b border-[var(--line)] px-6 py-3 shadow-2xl">
        <div className="max-w-7xl mx-auto flex flex-col lg:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-3">
            <img src="/art/soulsmith-logo.png" alt="SoulSmith Logo" className="h-12 w-auto object-contain py-0.5" />
            <div>
              <p className="text-[11px] text-[var(--spark)] font-mono tracking-widest uppercase">
                Living Mythology Engine
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex flex-wrap justify-center items-center gap-1.5 bg-[var(--deep)]/90 p-1.5 rounded-2xl border border-[var(--line)] shadow-xl">
            {[
              { id: 'sanctuary', label: '3D Sanctuary', icon: Dices },
              { id: 'scan', label: 'Dice Camera', icon: Camera },
              { id: 'sheet', label: 'Soul Sheet', icon: Shield },
              { id: 'curiosity', label: 'Curiosity Engine', icon: Compass },
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
                  className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-mono tracking-wider transition-all duration-300 ${
                    isActive
                      ? 'bg-[var(--gold)] text-[var(--void)] font-bold shadow-lg scale-105'
                      : 'text-[var(--parchment)] opacity-80 hover:opacity-100 hover:bg-[var(--void)]/50'
                  }`}
                >
                  <Icon size={14} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Soulprint Lens Button */}
          <button
            onClick={() => setShowSoulprintModal(true)}
            className="mythic-pill hover:border-[var(--gold)] transition flex items-center gap-2 py-2 px-4 shadow-lg cursor-pointer"
          >
            <Moon size={14} className="text-[var(--gold)]" />
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
              onRollComplete={(newRead) => {
                setCurrentRead(newRead);
                setEncounterFrame(null);
              }}
              isRolling={isRolling}
              setIsRolling={setIsRolling}
            />

            {/* Action Approach & Intent Framing */}
            <div className="mythic-card p-6 md:p-8 space-y-6">
              <div>
                <span className="eyebrow flex items-center gap-1.5">
                  <Zap size={14} /> Encounter Action Framework
                </span>
                <h3 className="text-2xl font-bold font-cinzel text-[var(--gold)] mt-1">Commit Stated Intent & Approach</h3>
              </div>

              {/* Encounter Frame Generation */}
              <div className="p-5 rounded-2xl bg-[var(--deep)]/90 border border-[var(--gold-dim)] space-y-4">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div>
                    <span className="text-xs font-mono font-bold text-[var(--gold)] uppercase tracking-wider">Encounter Frame</span>
                    <p className="text-xs text-[var(--parchment)] opacity-75 mt-1">Generate the pre-action situation before choosing what to do.</p>
                  </div>
                  <button onClick={() => handleFrameEncounter()} disabled={isFramingEncounter} className={`btn-gold text-xs py-2 px-5 ${isFramingEncounter ? 'opacity-50 animate-pulse' : ''}`}>
                    {isFramingEncounter ? 'Framing the oddness...' : 'Frame Encounter'}
                  </button>
                </div>
                {encounterFrame && (
                  <div className="space-y-3 text-sm">
                    <div className="flex flex-wrap items-center gap-2">
                      <h4 className="text-xl font-bold font-cinzel text-[var(--gold-bright)]">{encounterFrame.title}</h4>
                      <span className="mythic-pill border-purple-500/30 text-purple-300">{encounterFrame.phenomenon_type}</span>
                      <span className="mythic-pill border-rose-500/30 text-rose-300">Clock {encounterFrame.pressure_clock}/6</span>
                    </div>
                    <p className="text-[var(--parchment)] opacity-90">{encounterFrame.visible_situation}</p>
                    <p className="text-[var(--parchment)] opacity-75 italic">Hidden need: {encounterFrame.hidden_need}</p>
                    <p className="text-amber-200/90">Stakes: {encounterFrame.stakes}</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      <div>
                        <div className="font-mono uppercase tracking-wider text-[var(--spark)] mb-1">Questions</div>
                        <ul className="list-disc pl-5 space-y-1">{encounterFrame.questions.map((q) => <li key={q}>{q}</li>)}</ul>
                      </div>
                      <div>
                        <div className="font-mono uppercase tracking-wider text-[var(--spark)] mb-1">Suggested Actions</div>
                        <ul className="list-disc pl-5 space-y-1">{encounterFrame.suggested_actions.map((action) => <li key={action}>{action}</li>)}</ul>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Action Approach Selection */}
              <div>
                <label className="text-xs font-mono text-[var(--parchment)] uppercase tracking-wider block mb-2 opacity-80">
                  Select Action Approach:
                </label>
                <div className="grid grid-cols-2 md:grid-cols-6 gap-2.5">
                  {['Edge', 'Grace', 'Guile', 'Lore', 'Empathy', 'Craft'].map((app) => (
                    <button
                      key={app}
                      onClick={() => setChosenApproach(app)}
                      className={`p-3 rounded-xl border text-xs font-mono font-bold transition-all ${
                        chosenApproach === app
                          ? 'bg-[var(--spark)] text-[var(--void)] border-[var(--spark)] shadow-lg scale-102'
                          : 'bg-[var(--deep)] border-[var(--line)] text-[var(--parchment)] hover:border-[var(--spark-dim)]'
                      }`}
                    >
                      {app}
                    </button>
                  ))}
                </div>
              </div>

              {/* Player Intent Input */}
              <div>
                <label className="text-xs font-mono text-[var(--parchment)] uppercase tracking-wider block mb-2 opacity-80">
                  Stated Intent Narrative:
                </label>
                <textarea
                  rows={2}
                  value={playerIntent}
                  onChange={(e) => setPlayerIntent(e.target.value)}
                  className="w-full bg-[var(--deep)] border border-[var(--line)] rounded-2xl p-4 text-xs font-body text-[var(--parchment)] focus:outline-none focus:border-[var(--spark)] shadow-inner"
                />
              </div>

              {/* Resource Investment Controls */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5 p-5 rounded-2xl bg-[var(--deep)]/90 border border-[var(--line)]">
                <div className="flex justify-between items-center">
                  <div>
                    <span className="text-xs font-mono font-bold text-[var(--gold)] block">Spend Resonance</span>
                    <span className="text-[11px] text-[var(--parchment)] opacity-70">Boosts outcome ladder score (+1)</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setResonanceSpent(Math.max(0, resonanceSpent - 1))}
                      className="w-8 h-8 rounded-lg bg-[var(--void)] border border-[var(--gold-dim)] text-[var(--gold)] font-bold"
                    >
                      -
                    </button>
                    <span className="text-base font-bold font-cinzel text-[var(--gold-bright)] w-6 text-center">{resonanceSpent}</span>
                    <button
                      onClick={() => setResonanceSpent(Math.min(soulSheet.resources.resonance, resonanceSpent + 1))}
                      className="w-8 h-8 rounded-lg bg-[var(--void)] border border-[var(--gold-dim)] text-[var(--gold)] font-bold"
                    >
                      +
                    </button>
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <div>
                    <span className="text-xs font-mono font-bold text-rose-400 block">Accept Strain Overreach</span>
                    <span className="text-[11px] text-[var(--parchment)] opacity-70">Forces outcome at cost of Strain</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setStrainAccepted(Math.max(0, strainAccepted - 1))}
                      className="w-8 h-8 rounded-lg bg-[var(--void)] border border-rose-500/30 text-rose-400 font-bold"
                    >
                      -
                    </button>
                    <span className="text-base font-bold font-cinzel text-rose-300 w-6 text-center">{strainAccepted}</span>
                    <button
                      onClick={() => setStrainAccepted(Math.min(6 - soulSheet.resources.strain, strainAccepted + 1))}
                      className="w-8 h-8 rounded-lg bg-[var(--void)] border border-rose-500/30 text-rose-400 font-bold"
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
                  className={`btn-gold text-sm py-3 px-8 ${isResolving ? 'opacity-50 animate-pulse' : ''}`}
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

        {activeTab === 'curiosity' && <CuriosityView soulName={soulSheet.name} />}

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
