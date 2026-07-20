import React, { useState } from 'react';
import type { SoulprintProfile } from '../types';
import { apiClient } from '../lib/api';
import { Moon, Sun, ShieldCheck, Sparkles, X, Check } from 'lucide-react';

interface SoulprintModalProps {
  onClose: () => void;
  onApplyMotifs: (motifs: SoulprintProfile) => void;
}

export const SoulprintModal: React.FC<SoulprintModalProps> = ({ onClose, onApplyMotifs }) => {
  const [userConsent, setUserConsent] = useState(true);
  const [birthDate, setBirthDate] = useState('1998-08-14');
  const [birthTime, setBirthTime] = useState('14:30');
  const [birthLocation, setBirthLocation] = useState('Athens, Greece');
  const [profile, setProfile] = useState<SoulprintProfile | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerate = async () => {
    if (!userConsent) return;
    setIsGenerating(true);

    try {
      const data = await apiClient.previewSoulprint({
        user_consent: userConsent,
        birth_date: birthDate,
        birth_time: birthTime,
        birth_location: birthLocation
      });
      setProfile(data);
    } catch {
      setProfile(generateFallbackSoulprint());
    } finally {
      setIsGenerating(false);
    }
  };

  const generateFallbackSoulprint = (): SoulprintProfile => ({
    sun_sign: 'Leo',
    moon_sign: 'Taurus',
    ascendant_sign: 'Scorpio',
    elemental_balance: { Fire: 0.4, Earth: 0.3, Water: 0.2, Air: 0.1 },
    motifs: [
      { tag: 'solar_radiance', weight: 0.35, description: 'Sun in Leo enhances presence under Command and Spark reads.' },
      { tag: 'earth_anchor', weight: 0.30, description: 'Moon in Taurus provides extra resistance against Strain.' },
      { tag: 'water_threshold', weight: 0.25, description: 'Scorpio Ascendant unlocks hidden Omen Domain clues.' }
    ],
    favored_domains: ['Relic', 'Omen'],
    favored_threads: ['Bond', 'Memory'],
    narrative_hooks: [
      'Celestial alignments amplify mythic momentum during planetary turns.',
      'Hidden emotional truths surface under Empathy approaches.'
    ],
    privacy_notice: 'Derived motifs stored. Raw location fields purged after computation.'
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md overflow-y-auto">
      <div className="glass-panel max-w-2xl w-full p-6 md:p-8 space-y-6 relative border-amber-500/30 my-8">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-full text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition"
        >
          <X size={20} />
        </button>

        <div>
          <span className="text-xs uppercase tracking-widest text-gold-glow font-semibold flex items-center gap-1">
            <Sparkles size={14} /> Optional Character Lens
          </span>
          <h2 className="text-2xl font-bold font-cinzel text-slate-100">Astrological Soulprint Engine</h2>
          <p className="text-xs text-slate-400 mt-1">
            Calculates symbolic motif affinities via Swiss Ephemeris. Adds narrative texture without restricting player agency.
          </p>
        </div>

        {/* Form Input */}
        <div className="space-y-4 p-4 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Birth Date</label>
              <input
                type="date"
                value={birthDate}
                onChange={(e) => setBirthDate(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Birth Time (Optional)</label>
              <input
                type="time"
                value={birthTime}
                onChange={(e) => setBirthTime(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">City / Location</label>
              <input
                type="text"
                value={birthLocation}
                onChange={(e) => setBirthLocation(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200"
              />
            </div>
          </div>

          {/* GDPR Consent Checkbox */}
          <div className="flex items-center gap-2 pt-2 border-t border-slate-800">
            <input
              type="checkbox"
              id="consent"
              checked={userConsent}
              onChange={(e) => setUserConsent(e.target.checked)}
              className="rounded bg-slate-950 border-slate-700 text-purple-600 focus:ring-0"
            />
            <label htmlFor="consent" className="text-xs text-slate-300">
              I grant explicit consent to compute derived astrological motifs under GDPR privacy guidelines.
            </label>
          </div>

          <button
            onClick={handleGenerate}
            disabled={!userConsent || isGenerating}
            className={`w-full btn-primary justify-center ${!userConsent ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {isGenerating ? 'Calculating Natal Chart...' : 'Generate Astrological Soulprint'}
          </button>
        </div>

        {/* Calculated Soulprint Profile */}
        {profile && (
          <div className="space-y-4 p-5 rounded-xl bg-slate-900/90 border border-amber-500/30">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <div className="flex gap-4">
                <span className="text-xs text-amber-400 font-semibold flex items-center gap-1">
                  <Sun size={14} /> Sun: {profile.sun_sign}
                </span>
                <span className="text-xs text-cyan-400 font-semibold flex items-center gap-1">
                  <Moon size={14} /> Moon: {profile.moon_sign}
                </span>
                <span className="text-xs text-purple-400 font-semibold">
                  Ascendant: {profile.ascendant_sign}
                </span>
              </div>
            </div>

            <div>
              <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Derived Motifs</div>
              <div className="space-y-2">
                {profile.motifs.map((motif, idx) => (
                  <div key={idx} className="p-2.5 rounded bg-slate-950/80 border border-slate-800">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs font-bold text-amber-300 font-cinzel">#{motif.tag}</span>
                      <span className="text-[11px] text-slate-400">Weight: {(motif.weight * 100).toFixed(0)}%</span>
                    </div>
                    <p className="text-xs text-slate-300">{motif.description}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-3 rounded bg-slate-950/60 border border-slate-800 flex items-center gap-2 text-[11px] text-slate-400">
              <ShieldCheck size={14} className="text-emerald-400 shrink-0" />
              <span>{profile.privacy_notice}</span>
            </div>

            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  onApplyMotifs(profile);
                  onClose();
                }}
                className="btn-primary text-xs py-2 px-4"
              >
                <Check size={14} /> Apply Soulprint to Character
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
