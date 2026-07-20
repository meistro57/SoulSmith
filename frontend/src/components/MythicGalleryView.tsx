import React, { useState } from 'react';
import { Image, Maximize2, Layers } from 'lucide-react';

interface ArtItem {
  id: string;
  title: string;
  src: string;
  tag: string;
  description: string;
}

const ART_ITEMS: ArtItem[] = [
  {
    id: 'hero',
    title: 'The Soulkeeper & Celestial Sanctuary',
    src: '/soulsmith-hero.png',
    tag: 'Hero Artwork',
    description: 'The Soulkeeper connecting fragments of chance, player choices, and persistent world memory.'
  },
  {
    id: 'index',
    title: 'World Chronicle & Living Mythology Map',
    src: '/soulsmith-index.png',
    tag: 'Chronicle Index',
    description: 'An expansive overview of the seven-dice narrative grammar, active phenomena, and world states.'
  },
  {
    id: 'product',
    title: 'The Sacred Seven-Dice Polyhedral Engine',
    src: '/soulsmith-product.png',
    tag: 'Product & Dice',
    description: 'Physical polyhedral dice set (d20, d12, d10, d%, d8, d6, d4) sparking mythic encounters.'
  }
];

export const MythicGalleryView: React.FC = () => {
  const [selectedArt, setSelectedArt] = useState<ArtItem | null>(null);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-panel p-6">
        <div className="flex justify-between items-center">
          <div>
            <span className="text-xs uppercase tracking-widest text-gold-glow font-semibold flex items-center gap-1">
              <Image size={14} /> Sacred Visual Mythology
            </span>
            <h2 className="text-2xl font-bold font-cinzel text-slate-100">SoulSmith Concept & Artwork Gallery</h2>
            <p className="text-xs text-slate-400">
              High-resolution concept art, visual sitemaps, and official key art for the living mythology engine.
            </p>
          </div>
          <span className="glass-pill text-xs text-cyan-300 border-cyan-500/30 flex items-center gap-1">
            <Layers size={12} /> 3 Official Assets
          </span>
        </div>
      </div>

      {/* Featured Hero Banner */}
      <div className="relative rounded-2xl overflow-hidden glass-panel border-amber-500/30 group">
        <img
          src="/soulsmith-hero.png"
          alt="SoulSmith Hero Banner"
          className="w-full h-80 object-cover object-center transition duration-500 group-hover:scale-105"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/40 to-transparent p-6 flex flex-col justify-end">
          <span className="glass-pill text-xs font-semibold text-amber-300 border-amber-500/40 w-fit mb-2">
            Key Vision Artwork
          </span>
          <h3 className="text-3xl font-bold font-cinzel text-slate-100 mb-1">
            Roll the Spark. Write the Legend.
          </h3>
          <p className="text-xs text-slate-300 max-w-2xl">
            A living mythology where seven dice, shared human imagination, and AI forge stories that remember.
          </p>
        </div>
      </div>

      {/* Artwork Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {ART_ITEMS.map((art) => (
          <div
            key={art.id}
            onClick={() => setSelectedArt(art)}
            className="glass-panel overflow-hidden cursor-pointer group hover:border-purple-500/50 transition-all duration-300 flex flex-col justify-between"
          >
            <div className="relative h-52 overflow-hidden bg-slate-950">
              <img
                src={art.src}
                alt={art.title}
                className="w-full h-full object-cover transition duration-500 group-hover:scale-110"
              />
              <div className="absolute top-3 right-3 p-2 rounded-full bg-slate-950/70 text-slate-200 opacity-0 group-hover:opacity-100 transition">
                <Maximize2 size={16} />
              </div>
            </div>

            <div className="p-4 space-y-2">
              <span className="glass-pill text-[10px] uppercase font-bold text-cyan-300 border-cyan-500/30">
                {art.tag}
              </span>
              <h4 className="text-base font-bold font-cinzel text-slate-100">{art.title}</h4>
              <p className="text-xs text-slate-400 leading-relaxed">{art.description}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Fullscreen Art Modal */}
      {selectedArt && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/90 backdrop-blur-md"
          onClick={() => setSelectedArt(null)}
        >
          <div
            className="glass-panel max-w-4xl w-full p-4 space-y-4 border-purple-500/40 relative my-8"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center px-2">
              <div>
                <span className="text-xs text-amber-400 font-semibold">{selectedArt.tag}</span>
                <h3 className="text-xl font-bold font-cinzel text-slate-100">{selectedArt.title}</h3>
              </div>
              <button
                onClick={() => setSelectedArt(null)}
                className="btn-secondary py-1 px-3 text-xs"
              >
                Close Fullscreen
              </button>
            </div>

            <div className="max-h-[70vh] overflow-hidden rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-center">
              <img
                src={selectedArt.src}
                alt={selectedArt.title}
                className="max-h-[70vh] w-auto object-contain"
              />
            </div>

            <p className="text-xs text-slate-300 px-2 italic">{selectedArt.description}</p>
          </div>
        </div>
      )}
    </div>
  );
};
