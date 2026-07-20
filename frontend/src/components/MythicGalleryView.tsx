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
    id: 'bundle',
    title: 'SoulSmith Graphics & UI Sprite Bundle',
    src: '/art/graphics_bundle.png',
    tag: 'Official UI Sprite Sheet',
    description: 'Complete master graphics bundle including 7-dice set, resource tokens, phenomena badges, NPC portraits, magic circles, and ornate frames.'
  },
  {
    id: 'hero',
    title: 'The Soulkeeper & Celestial Sanctuary',
    src: '/soulsmith-hero.png',
    tag: 'Hero Key Artwork',
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
      <div className="mythic-card p-6">
        <div className="flex justify-between items-center">
          <div>
            <span className="eyebrow flex items-center gap-1.5">
              <Image size={14} /> Sacred Visual Mythology
            </span>
            <h2 className="text-2xl font-bold font-cinzel text-[var(--gold)]">SoulSmith Concept & Artwork Gallery</h2>
            <p className="text-xs font-body text-[var(--parchment)] opacity-75">
              High-resolution concept art, visual sitemaps, and official UI graphics bundle.
            </p>
          </div>
          <span className="mythic-pill flex items-center gap-1">
            <Layers size={12} /> 4 Official Assets
          </span>
        </div>
      </div>

      {/* Featured Graphics Bundle Banner */}
      <div className="relative rounded-2xl overflow-hidden mythic-card border-[var(--gold-dim)] group cursor-pointer" onClick={() => setSelectedArt(ART_ITEMS[0])}>
        <img
          src="/art/graphics_bundle.png"
          alt="Graphics Bundle"
          className="w-full h-80 object-cover object-center transition duration-500 group-hover:scale-102"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#070A12] via-[#070A12]/40 to-transparent p-6 flex flex-col justify-end">
          <span className="mythic-pill w-fit mb-2">
            Master UI Graphics Bundle (300 DPI)
          </span>
          <h3 className="text-3xl font-bold font-cinzel text-[var(--gold)] mb-1">
            Official SoulSmith Sprite & Token Asset Sheet
          </h3>
          <p className="text-xs font-body text-[var(--parchment)] max-w-2xl opacity-90">
            Contains 7 polyhedral dice, 6 resource tokens, 5 phenomena icons, 5 NPC portraits, magic circles, and ornate borders.
          </p>
        </div>
      </div>

      {/* Artwork Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {ART_ITEMS.slice(1).map((art) => (
          <div
            key={art.id}
            onClick={() => setSelectedArt(art)}
            className="mythic-card overflow-hidden cursor-pointer group hover:border-[var(--spark)] transition-all duration-300 flex flex-col justify-between"
          >
            <div className="relative h-52 overflow-hidden bg-[var(--void)]">
              <img
                src={art.src}
                alt={art.title}
                className="w-full h-full object-cover transition duration-500 group-hover:scale-105"
              />
              <div className="absolute top-3 right-3 p-2 rounded-full bg-[var(--void)]/80 text-[var(--parchment)] opacity-0 group-hover:opacity-100 transition">
                <Maximize2 size={16} />
              </div>
            </div>

            <div className="p-4 space-y-2">
              <span className="mythic-pill text-[10px]">
                {art.tag}
              </span>
              <h4 className="text-base font-bold font-cinzel text-[var(--gold)]">{art.title}</h4>
              <p className="text-xs font-body text-[var(--parchment)] opacity-75 leading-relaxed">{art.description}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Fullscreen Art Modal */}
      {selectedArt && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#070A12]/95 backdrop-blur-md"
          onClick={() => setSelectedArt(null)}
        >
          <div
            className="mythic-card max-w-5xl w-full p-4 space-y-4 relative my-8"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center px-2">
              <div>
                <span className="text-xs font-mono text-[var(--spark)]">{selectedArt.tag}</span>
                <h3 className="text-xl font-bold font-cinzel text-[var(--gold)]">{selectedArt.title}</h3>
              </div>
              <button
                onClick={() => setSelectedArt(null)}
                className="btn-glass text-xs"
              >
                Close Fullscreen
              </button>
            </div>

            <div className="max-h-[75vh] overflow-hidden rounded-xl bg-[var(--void)] border border-[var(--line)] flex items-center justify-center p-2">
              <img
                src={selectedArt.src}
                alt={selectedArt.title}
                className="max-h-[75vh] w-auto object-contain"
              />
            </div>

            <p className="text-xs font-body text-[var(--parchment)] px-2 italic opacity-85">{selectedArt.description}</p>
          </div>
        </div>
      )}
    </div>
  );
};
