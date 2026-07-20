import React, { useState, useEffect } from 'react';
import { Flame, Eye, RefreshCw } from 'lucide-react';
import { apiClient } from '../lib/api';

interface Phenomenon {
  id: string;
  name: string;
  typology: string;
  origin: string;
  visible_signs: string[];
  hidden_need: string;
  escalation_level: number;
  transformation_condition: string;
  reward_or_payoff: string;
}

const PHENOMENA_ICON_MAP: Record<string, string> = {
  Echo: '/art/phenomena/echoes.png',
  Knot: '/art/phenomena/knots.png',
  Veil: '/art/phenomena/veils.png',
  Well: '/art/phenomena/wells.png',
  Awakening: '/art/phenomena/awakenings.png',
  Mirror: '/art/phenomena/echoes.png',
  Breach: '/art/phenomena/veils.png'
};

export const PhenomenaView: React.FC = () => {
  const [phenomena, setPhenomena] = useState<Phenomenon[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchPhenomena();
  }, []);

  const fetchPhenomena = async () => {
    setIsLoading(true);
    try {
      const data = await apiClient.listPhenomena<Phenomenon[]>();
      setPhenomena(data);
    } catch {
      setPhenomena(generateFallbackPhenomena());
    } finally {
      setIsLoading(false);
    }
  };

  const generateFallbackPhenomena = (): Phenomenon[] => [
    {
      id: 'phen-1',
      name: 'The Weeping Floodgate of Cinder',
      typology: 'Echo',
      origin: 'Formed during the drowning of the Starforge Archive.',
      visible_signs: ['Water dripping upwards', 'Echoes of unsaid goodbyes in cold air'],
      hidden_need: 'Requires a forgotten secret to be confessed aloud.',
      escalation_level: 2,
      transformation_condition: 'When a Soul offers a Memory Thread without fear.',
      reward_or_payoff: 'Transforms into the Well of Clear Answers.'
    },
    {
      id: 'phen-2',
      name: 'The King Without a Reflection',
      typology: 'Mirror',
      origin: 'Forged from the collective doubt of lost Keepers.',
      visible_signs: ['Mirrors showing different faces', 'Shadows detaching from walls'],
      hidden_need: 'Needs a Soul to embrace their inner Shadow without violence.',
      escalation_level: 3,
      transformation_condition: 'When a Revelatory Failure yields an Empathy approach.',
      reward_or_payoff: 'Awakens the Relic [Glass Oath].'
    }
  ];

  return (
    <div className="space-y-6">
      <div className="mythic-card p-6">
        <div className="flex justify-between items-center">
          <div>
            <span className="eyebrow flex items-center gap-1.5">
              <Flame size={14} /> Living Mythic Phenomena Codex
            </span>
            <h2 className="text-2xl font-bold font-cinzel text-[var(--gold)]">World Pressures & Non-Monster Encounters</h2>
            <p className="text-xs font-body text-[var(--parchment)] opacity-75">
              Phenomena are world-scale conflicts governed by needs, origins, escalations, and transformation conditions.
            </p>
          </div>

          <button onClick={fetchPhenomena} className="btn-glass text-xs py-2 px-3">
            <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} /> Refresh World Pressures
          </button>
        </div>
      </div>

      {/* Phenomena Cards Grid with Cropped Icons */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {phenomena.map((p) => {
          const iconSrc = PHENOMENA_ICON_MAP[p.typology] || '/art/phenomena/echoes.png';
          return (
            <div key={p.id} className="mythic-card p-6 space-y-4">
              <div className="flex justify-between items-start border-b border-[var(--line)] pb-3">
                <div className="flex items-center gap-3">
                  <img src={iconSrc} alt={p.typology} className="h-12 w-auto object-contain shrink-0" />
                  <div>
                    <span className="mythic-pill text-[10px]">
                      {p.typology} Phenomenon
                    </span>
                    <h3 className="text-xl font-bold font-cinzel text-[var(--gold)] mt-1">{p.name}</h3>
                  </div>
                </div>

                {/* Escalation Level Meter */}
                <div className="text-right">
                  <div className="text-[10px] uppercase font-mono text-[var(--parchment)] opacity-75">Escalation</div>
                  <div className="flex gap-1 mt-1">
                    {[...Array(5)].map((_, i) => (
                      <div
                        key={i}
                        className={`w-3 h-3 rounded-full ${
                          i < p.escalation_level ? 'bg-rose-500 shadow-md' : 'bg-[var(--void)]'
                        }`}
                      />
                    ))}
                  </div>
                </div>
              </div>

              <p className="text-xs font-body text-[var(--parchment)] italic opacity-85">{p.origin}</p>

              {/* Visible Signs */}
              <div className="space-y-1">
                <div className="text-[11px] font-mono uppercase text-[var(--spark)] flex items-center gap-1">
                  <Eye size={12} /> Visible Signs in Environment:
                </div>
                <ul className="space-y-0.5 text-xs font-body text-[var(--parchment)] pl-4 list-disc opacity-90">
                  {p.visible_signs.map((sign, idx) => (
                    <li key={idx}>{sign}</li>
                  ))}
                </ul>
              </div>

              {/* Hidden Need & Transformation */}
              <div className="p-3.5 rounded-xl bg-[var(--deep)]/90 border border-[var(--line)] space-y-1 text-xs font-body">
                <div className="text-[var(--gold-bright)] font-semibold">Hidden Need: {p.hidden_need}</div>
                <div className="text-purple-300">Transformation: {p.transformation_condition}</div>
                <div className="text-emerald-400 font-semibold pt-1 border-t border-[var(--line)]">
                  Payoff: {p.reward_or_payoff}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
