import React, { useState } from 'react';
import type { SoulSheet, Relic } from '../types';
import { Shield, Package, AlertTriangle, PlusCircle, UserCheck } from 'lucide-react';

interface SoulSheetViewProps {
  sheet: SoulSheet;
  onUpdateSheet: (updated: SoulSheet) => void;
}

const PORTRAIT_OPTIONS = [
  { id: 'archivist', name: 'Archivist', src: '/art/portraits_full/archivist.png' },
  { id: 'wanderer', name: 'Wanderer', src: '/art/portraits_full/wanderer.png' },
  { id: 'shadow', name: 'Shadow Weaver', src: '/art/portraits_full/shadow.png' },
  { id: 'blue-being', name: 'Starforged Sentinel', src: '/art/portraits_full/blue-being.png' },
  { id: 'dwarf', name: 'Rune Smith', src: '/art/portraits_full/dwarf.png' },
  { id: 'dragonborn', name: 'Ember Dragonborn', src: '/art/portraits_full/dragonborn.png' },
  { id: 'moon-elf', name: 'Moon Elf Oracle', src: '/art/portraits_full/moon-elf.png' },
  { id: 'shadow-knight', name: 'Void Knight', src: '/art/portraits_full/shadow-knight.png' },
  { id: 'flame-sentinel', name: 'Flame Warden', src: '/art/portraits_full/flame-sentinel.png' },
  { id: 'demon-queen', name: 'Veil Sovereign', src: '/art/portraits_full/demon-queen.png' },
];

const PRESET_RELICS = [
  { name: 'Compass of Better Questions', icon: '/art/relics_full/compass-questions.png', effect: 'Reroll one die once per journey.' },
  { name: 'Echo Lantern', icon: '/art/relics_full/echo-lantern.png', effect: 'Reveals hidden oaths in forgotten ruins.' },
  { name: 'Heart of the Forge', icon: '/art/relics_full/heart-forge.png', effect: 'Prevents Strain fracture once per session.' },
  { name: 'Veilweaver Cloak Pin', icon: '/art/relics_full/veilweaver-pin.png', effect: 'Bypasses threshold barriers without fear.' },
  { name: 'Oracle\'s Monocle', icon: '/art/relics_full/oracles-monocle.png', effect: 'Inspects hidden intent of Foe or Ally.' },
  { name: 'Starforge Key', icon: '/art/relics_full/starforge-key.png', effect: 'Unlocks ancient machinery & celestial gates.' },
  { name: 'Dreamwalker Mask', icon: '/art/relics_full/dreamwalker-mask.png', effect: 'Enters the dreamscape to alter past scars.' },
  { name: 'Crown of Embers', icon: '/art/relics_full/crown-embers.png', effect: 'Converts 1 Strain into Ascendancy score.' },
  { name: 'Phoenix Feather', icon: '/art/relics_full/phoenix-feather.png', effect: 'Restores 2 Resonance upon collapse.' },
];

export const SoulSheetView: React.FC<SoulSheetViewProps> = ({ sheet, onUpdateSheet }) => {
  const [selectedPortrait, setSelectedPortrait] = useState(PORTRAIT_OPTIONS[0]);
  const [showPortraitPicker, setShowPortraitPicker] = useState(false);
  const [newRelicName, setNewRelicName] = useState('');

  const adjustResource = (key: 'resonance' | 'strain' | 'thread_count', delta: number) => {
    const caps = { resonance: 6, strain: 6, thread_count: 5 };
    const current = sheet.resources[key];
    const updatedVal = Math.max(0, Math.min(caps[key], current + delta));

    onUpdateSheet({
      ...sheet,
      resources: {
        ...sheet.resources,
        [key]: updatedVal
      }
    });
  };

  const handleEquipPresetRelic = (preset: typeof PRESET_RELICS[0]) => {
    const created: Relic = {
      id: Date.now().toString(),
      name: preset.name,
      stage: 'Awakened',
      effect: preset.effect,
      overdraw_consequence: 'Adds +1 automatic Strain upon overdraw.'
    };
    onUpdateSheet({
      ...sheet,
      relics: [...sheet.relics, created]
    });
  };

  const handleAddRelic = () => {
    if (!newRelicName.trim()) return;
    const created: Relic = {
      id: Date.now().toString(),
      name: newRelicName.trim(),
      stage: 'Dormant',
      effect: 'Grants passive story alignment reroll on favored Domains.',
      overdraw_consequence: 'Adds +1 automatic Strain upon overdraw.'
    };
    onUpdateSheet({
      ...sheet,
      relics: [...sheet.relics, created]
    });
    setNewRelicName('');
  };

  return (
    <div className="space-y-6">
      {/* Strain Max Fracture Banner */}
      {sheet.resources.strain >= 6 && (
        <div className="p-5 rounded-2xl bg-red-950/90 border-2 border-red-500/80 flex items-center gap-4 text-red-200 shadow-2xl animate-pulse">
          <AlertTriangle className="text-red-400 shrink-0" size={28} />
          <div>
            <div className="font-extrabold font-cinzel text-red-400 text-lg">CRITICAL SOUL FRACTURE WARNING (6/6 Strain)</div>
            <div className="text-xs text-red-300">
              The Soul is overreached. Convert a Bond into a Scar, sacrifice a Relic stage, or trigger a Fracture beat immediately!
            </div>
          </div>
        </div>
      )}

      {/* Header & Character Portrait */}
      <div className="mythic-card p-6 md:p-8 space-y-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 border-b border-[var(--line)] pb-6">
          <div className="flex items-center gap-5">
            {/* NPC Cropped Portrait Avatar with Selector */}
            <div
              onClick={() => setShowPortraitPicker(!showPortraitPicker)}
              className="relative rounded-2xl overflow-hidden border-2 border-[var(--gold)] shadow-2xl w-24 h-32 shrink-0 bg-[var(--void)] cursor-pointer group"
            >
              <img src={selectedPortrait.src} alt={sheet.name} className="w-full h-full object-cover transition group-hover:scale-105" />
              <div className="absolute inset-0 bg-[var(--void)]/60 opacity-0 group-hover:opacity-100 flex items-center justify-center text-[10px] font-mono text-[var(--gold)] text-center p-1">
                Change Portrait
              </div>
            </div>

            <div>
              <span className="eyebrow flex items-center gap-1.5">
                <Shield size={14} /> Sacred Chronicle Character Record
              </span>
              <h2 className="text-3xl md:text-4xl font-black font-cinzel text-[var(--gold)] mt-1">{sheet.name}</h2>
              <p className="text-sm font-body text-[var(--parchment)] mt-1 opacity-90">
                <span className="text-[var(--spark)] font-bold">{sheet.calling}</span> • Origin: {sheet.origin}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <span className="mythic-pill text-[var(--gold)] border-[var(--gold-dim)]">
              Desire: {sheet.desire}
            </span>
            <span className="mythic-pill text-rose-300 border-rose-500/40">
              Fear: {sheet.fear}
            </span>
          </div>
        </div>

        {/* Character Portrait Picker */}
        {showPortraitPicker && (
          <div className="p-4 rounded-2xl bg-[var(--deep)] border border-[var(--line)] space-y-3">
            <div className="text-xs font-mono font-bold text-[var(--gold)] flex items-center gap-1.5">
              <UserCheck size={14} /> Select Character Avatar Portrait:
            </div>
            <div className="flex flex-wrap gap-3">
              {PORTRAIT_OPTIONS.map((p) => (
                <div
                  key={p.id}
                  onClick={() => {
                    setSelectedPortrait(p);
                    setShowPortraitPicker(false);
                  }}
                  className={`cursor-pointer rounded-xl overflow-hidden border-2 p-1 text-center w-20 transition ${
                    selectedPortrait.id === p.id ? 'border-[var(--gold)] bg-[var(--void)] shadow-lg' : 'border-transparent opacity-75 hover:opacity-100'
                  }`}
                >
                  <img src={p.src} alt={p.name} className="h-16 w-full object-cover rounded-lg" />
                  <span className="text-[9px] font-mono text-[var(--parchment)] truncate block mt-1">{p.name}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Core Resource Token Counters */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Resonance */}
          <div className="p-5 rounded-2xl bg-[var(--deep)]/90 border border-[var(--line)] flex flex-col justify-between shadow-xl">
            <div className="flex justify-between items-center mb-3">
              <div className="flex items-center gap-3">
                <img src="/art/resources/resonance.png" alt="Resonance Token" className="h-10 w-auto object-contain" />
                <span className="text-xs uppercase font-mono font-bold text-[var(--spark)]">Resonance</span>
              </div>
              <span className="text-lg font-black text-[var(--gold-bright)] font-cinzel">{sheet.resources.resonance} / 6</span>
            </div>
            <p className="text-xs font-body text-[var(--parchment)] opacity-75 mb-4">Mythic alignment. Spend to tune reads, awaken relics, or reroll.</p>
            <div className="flex justify-between items-center">
              <div className="flex gap-1.5">
                {[...Array(6)].map((_, i) => (
                  <div
                    key={i}
                    className={`w-4 h-4 rounded-full border border-[var(--spark-dim)] ${
                      i < sheet.resources.resonance ? 'bg-[var(--spark)] shadow-md' : 'bg-[var(--void)]'
                    }`}
                  />
                ))}
              </div>
              <div className="flex gap-1">
                <button
                  onClick={() => adjustResource('resonance', -1)}
                  className="w-8 h-8 rounded-lg bg-[var(--void)] border border-[var(--line)] text-[var(--spark)] font-bold"
                >
                  -
                </button>
                <button
                  onClick={() => adjustResource('resonance', 1)}
                  className="w-8 h-8 rounded-lg bg-[var(--void)] border border-[var(--line)] text-[var(--spark)] font-bold"
                >
                  +
                </button>
              </div>
            </div>
          </div>

          {/* Strain */}
          <div className="p-5 rounded-2xl bg-[var(--deep)]/90 border border-[var(--line)] flex flex-col justify-between shadow-xl">
            <div className="flex justify-between items-center mb-3">
              <div className="flex items-center gap-3">
                <img src="/art/resources/strain.png" alt="Strain Token" className="h-10 w-auto object-contain" />
                <span className="text-xs uppercase font-mono font-bold text-rose-400">Strain</span>
              </div>
              <span className="text-lg font-black text-rose-300 font-cinzel">{sheet.resources.strain} / 6</span>
            </div>
            <p className="text-xs font-body text-[var(--parchment)] opacity-75 mb-4">Overreach load. Accepted to force outcomes or resist fear.</p>
            <div className="flex justify-between items-center">
              <div className="flex gap-1.5">
                {[...Array(6)].map((_, i) => (
                  <div
                    key={i}
                    className={`w-4 h-4 rounded-full border border-rose-500/50 ${
                      i < sheet.resources.strain ? 'bg-rose-500 shadow-md' : 'bg-[var(--void)]'
                    }`}
                  />
                ))}
              </div>
              <div className="flex gap-1">
                <button
                  onClick={() => adjustResource('strain', -1)}
                  className="w-8 h-8 rounded-lg bg-[var(--void)] border border-rose-500/30 text-rose-400 font-bold"
                >
                  -
                </button>
                <button
                  onClick={() => adjustResource('strain', 1)}
                  className="w-8 h-8 rounded-lg bg-[var(--void)] border border-rose-500/30 text-rose-400 font-bold"
                >
                  +
                </button>
              </div>
            </div>
          </div>

          {/* Thread */}
          <div className="p-5 rounded-2xl bg-[var(--deep)]/90 border border-[var(--line)] flex flex-col justify-between shadow-xl">
            <div className="flex justify-between items-center mb-3">
              <div className="flex items-center gap-3">
                <img src="/art/resources/thread.png" alt="Thread Token" className="h-10 w-auto object-contain" />
                <span className="text-xs uppercase font-mono font-bold text-[var(--gold)]">Threads</span>
              </div>
              <span className="text-lg font-black text-[var(--gold-bright)] font-cinzel">{sheet.resources.thread_count} / 5</span>
            </div>
            <p className="text-xs font-body text-[var(--parchment)] opacity-75 mb-4">Persistent continuity tokens used to write facts & summon callbacks.</p>
            <div className="flex justify-between items-center">
              <div className="flex gap-1.5">
                {[...Array(5)].map((_, i) => (
                  <div
                    key={i}
                    className={`w-4 h-4 rounded-full border border-[var(--gold-dim)] ${
                      i < sheet.resources.thread_count ? 'bg-[var(--gold)] shadow-md' : 'bg-[var(--void)]'
                    }`}
                  />
                ))}
              </div>
              <div className="flex gap-1">
                <button
                  onClick={() => adjustResource('thread_count', -1)}
                  className="w-8 h-8 rounded-lg bg-[var(--void)] border border-[var(--line)] text-[var(--gold)] font-bold"
                >
                  -
                </button>
                <button
                  onClick={() => adjustResource('thread_count', 1)}
                  className="w-8 h-8 rounded-lg bg-[var(--void)] border border-[var(--line)] text-[var(--gold)] font-bold"
                >
                  +
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Relics & Artifacts Arsenal */}
      <div className="mythic-card p-6 md:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h3 className="text-2xl font-bold font-cinzel text-[var(--gold)] flex items-center gap-2">
            <Package size={22} className="text-[var(--spark)]" /> Relics & Artifacts Arsenal
          </h3>
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <input
              type="text"
              placeholder="Custom Relic name..."
              value={newRelicName}
              onChange={(e) => setNewRelicName(e.target.value)}
              className="bg-[var(--deep)] border border-[var(--line)] rounded-xl px-4 py-2 text-xs font-mono text-[var(--parchment)] focus:outline-none focus:border-[var(--spark)] flex-1 sm:w-48"
            />
            <button onClick={handleAddRelic} className="btn-spark py-2 px-4 text-xs shrink-0">
              <PlusCircle size={14} /> Add Custom
            </button>
          </div>
        </div>

        {/* Quick Equip Preset Relics Gallery */}
        <div className="space-y-2">
          <span className="text-xs font-mono uppercase text-[var(--spark)] block">Quick Equip Mythic Relic:</span>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {PRESET_RELICS.map((preset, i) => (
              <div
                key={i}
                onClick={() => handleEquipPresetRelic(preset)}
                className="cursor-pointer p-3 rounded-xl bg-[var(--deep)] border border-[var(--line)] hover:border-[var(--gold)] transition text-center group"
              >
                <img src={preset.icon} alt={preset.name} className="h-12 w-auto mx-auto object-contain group-hover:scale-110 transition" />
                <div className="font-cinzel text-xs text-[var(--gold)] font-bold truncate mt-1">{preset.name}</div>
                <span className="text-[10px] font-mono text-[var(--spark)] block mt-0.5">+ Equip</span>
              </div>
            ))}
          </div>
        </div>

        {/* Currently Equipped Relics */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pt-4 border-t border-[var(--line)]">
          {sheet.relics.map((relic) => (
            <div key={relic.id} className="p-5 rounded-2xl bg-[var(--deep)]/90 border border-[var(--line)] space-y-2">
              <div className="flex justify-between items-center">
                <span className="font-bold text-[var(--parchment)] font-cinzel text-lg">{relic.name}</span>
                <span className="mythic-pill">
                  {relic.stage}
                </span>
              </div>
              <p className="text-xs font-body text-[var(--parchment)] opacity-85 leading-relaxed">{relic.effect}</p>
              <div className="text-xs font-body text-rose-400 italic pt-1 border-t border-[var(--line)]">
                Overdraw Consequence: {relic.overdraw_consequence}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
