import React, { useState, useEffect } from 'react';
import { Flame, Eye, RefreshCw } from 'lucide-react';

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

export const PhenomenaView: React.FC = () => {
  const [phenomena, setPhenomena] = useState<Phenomenon[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchPhenomena();
  }, []);

  const fetchPhenomena = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/v1/phenomena');
      const data = res.ok ? await res.json() : generateFallbackPhenomena();
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
      <div className="glass-panel p-6">
        <div className="flex justify-between items-center">
          <div>
            <span className="text-xs uppercase tracking-widest text-rose-400 font-semibold flex items-center gap-1">
              <Flame size={14} /> Living Mythic Phenomena Codex
            </span>
            <h2 className="text-2xl font-bold font-cinzel text-slate-100">World Pressures & Non-Monster Encounters</h2>
            <p className="text-xs text-slate-400">
              Phenomena are world-scale conflicts governed by needs, origins, escalations, and transformation conditions.
            </p>
          </div>

          <button onClick={fetchPhenomena} className="btn-secondary text-xs py-2 px-3">
            <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} /> Refresh World Pressures
          </button>
        </div>
      </div>

      {/* Phenomena Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {phenomena.map((p) => (
          <div key={p.id} className="glass-panel p-6 space-y-4 border-rose-500/30">
            <div className="flex justify-between items-start border-b border-slate-800 pb-3">
              <div>
                <span className="glass-pill text-[10px] uppercase font-bold text-rose-300 border-rose-500/30">
                  {p.typology} Phenomenon
                </span>
                <h3 className="text-xl font-bold font-cinzel text-slate-100 mt-1">{p.name}</h3>
              </div>

              {/* Escalation Level Meter */}
              <div className="text-right">
                <div className="text-[10px] uppercase font-semibold text-slate-400">Escalation</div>
                <div className="flex gap-1 mt-1">
                  {[...Array(5)].map((_, i) => (
                    <div
                      key={i}
                      className={`w-3 h-3 rounded-full ${
                        i < p.escalation_level ? 'bg-rose-500 shadow-md' : 'bg-slate-800'
                      }`}
                    />
                  ))}
                </div>
              </div>
            </div>

            <p className="text-xs text-slate-300 italic">{p.origin}</p>

            {/* Visible Signs */}
            <div className="space-y-1">
              <div className="text-[11px] font-semibold uppercase text-slate-400 flex items-center gap-1">
                <Eye size={12} className="text-cyan-400" /> Visible Signs in Environment:
              </div>
              <ul className="space-y-0.5 text-xs text-slate-300 pl-4 list-disc">
                {p.visible_signs.map((sign, idx) => (
                  <li key={idx}>{sign}</li>
                ))}
              </ul>
            </div>

            {/* Hidden Need & Transformation */}
            <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1 text-xs">
              <div className="text-amber-400 font-semibold">Hidden Need: {p.hidden_need}</div>
              <div className="text-purple-300">Transformation: {p.transformation_condition}</div>
              <div className="text-emerald-400 font-semibold pt-1 border-t border-slate-800">
                Payoff: {p.reward_or_payoff}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
