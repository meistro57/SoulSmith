// frontend/src/components/visual-memory/AvatarIdentityPanel.tsx
import React from 'react';
import type { AvatarIdentity, EquipmentAppearance } from '../../types';
import { Sparkles, Shield } from 'lucide-react';

interface AvatarIdentityPanelProps {
  identity: AvatarIdentity;
  equipment: EquipmentAppearance;
}

export const AvatarIdentityPanel: React.FC<AvatarIdentityPanelProps> = ({ identity, equipment }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 font-mono text-xs">
      {/* Permanent Identity Card */}
      <div className="p-6 rounded-2xl bg-slate-900/90 border border-purple-500/20 space-y-4 shadow-xl">
        <div className="flex justify-between items-center border-b border-purple-500/20 pb-3">
          <h3 className="font-bold text-slate-100 text-sm flex items-center gap-2">
            <Sparkles size={16} className="text-purple-400" />
            <span>Permanent Identity Layer</span>
          </h3>
          <span className="text-[10px] text-slate-400">Rarely Changes</span>
        </div>

        <div className="space-y-3">
          <div>
            <span className="text-slate-500 block text-[10px]">CHARACTER NAME</span>
            <span className="text-slate-100 font-bold text-sm">{identity.soul_id}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">SPECIES & ASPECT</span>
            <span className="text-purple-300">{identity.species}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">FACIAL STRUCTURE</span>
            <span className="text-slate-300 font-serif">{identity.face}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">EYES & VISION</span>
            <span className="text-amber-300">{identity.eyes}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">HAIR & CROWN</span>
            <span className="text-slate-300 font-serif">{identity.hair}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">BODY BUILD</span>
            <span className="text-slate-300 font-serif">{identity.body}</span>
          </div>
        </div>
      </div>

      {/* Equipment Appearance Layer */}
      <div className="p-6 rounded-2xl bg-slate-900/90 border border-indigo-500/20 space-y-4 shadow-xl">
        <div className="flex justify-between items-center border-b border-indigo-500/20 pb-3">
          <h3 className="font-bold text-slate-100 text-sm flex items-center gap-2">
            <Shield size={16} className="text-indigo-400" />
            <span>Equipment Layer</span>
          </h3>
          <span className="text-[10px] text-indigo-400">Dynamic</span>
        </div>

        <div className="space-y-3">
          <div>
            <span className="text-slate-500 block text-[10px]">ARMOR</span>
            <span className="text-slate-200 font-serif">{equipment.armor}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">CLOTHING & EMBROIDERY</span>
            <span className="text-slate-200 font-serif">{equipment.clothing}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">WEAPONS</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {equipment.weapons.map((w) => (
                <span key={w} className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-[10px] text-cyan-300">
                  {w}
                </span>
              ))}
            </div>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">RELICS</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {equipment.relics.map((r) => (
                <span key={r} className="px-2 py-0.5 rounded bg-amber-950 border border-amber-500/30 text-[10px] text-amber-300">
                  {r}
                </span>
              ))}
            </div>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">BACKPACKS & CLOAKS</span>
            <span className="text-slate-200 font-serif">{equipment.backpacks_cloaks}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
