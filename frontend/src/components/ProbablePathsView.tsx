// frontend/src/components/ProbablePathsView.tsx
import React, { useCallback, useEffect, useState } from 'react';
import type { AlternateSceneResult, ManifestationType, ProbablePath } from '../types';
import { apiClient } from '../lib/api';
import { GitBranch, Sparkles, Moon, Volume2, Eye, Compass, ShieldCheck, Play, PlusCircle } from 'lucide-react';

interface ProbablePathsViewProps {
  soulName: string;
}

export const ProbablePathsView: React.FC<ProbablePathsViewProps> = ({ soulName }) => {
  const [paths, setPaths] = useState<ProbablePath[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedFilter, setSelectedFilter] = useState<string>('all');

  // Exploration Modal State
  const [exploringPath, setExploringPath] = useState<ProbablePath | null>(null);
  const [alternateScene, setAlternateScene] = useState<AlternateSceneResult | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);

  // New Path Form State
  const [showLogModal, setShowLogModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newChosenPath, setNewChosenPath] = useState('');
  const [newUnchosenApproach, setNewUnchosenApproach] = useState('');
  const [newManifestation, setNewManifestation] = useState<ManifestationType>('dream');

  const fetchPaths = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiClient.listProbablePaths(soulName);
      setPaths(res.probable_paths || []);
    } catch (err) {
      console.error('Failed to load probable paths', err);
    } finally {
      setLoading(false);
    }
  }, [soulName]);

  useEffect(() => {
    fetchPaths();
  }, [fetchPaths]);

  const handleManifestType = async (pathId: string, manifestationType: ManifestationType) => {
    try {
      await apiClient.manifestProbablePath({
        path_id: pathId,
        manifestation_type: manifestationType,
        status: 'echoing',
      });
      await fetchPaths();
    } catch (err) {
      console.error('Failed to update manifestation', err);
    }
  };

  const handleSimulateWhatIf = async (path: ProbablePath) => {
    setExploringPath(path);
    setIsSimulating(true);
    setAlternateScene(null);
    try {
      const res = await apiClient.exploreProbablePath({
        path_id: path.id,
        soul_name: soulName,
      });
      setAlternateScene(res.alternate_scene);
    } catch (err) {
      console.error('Failed to simulate alternate path', err);
    } finally {
      setIsSimulating(false);
    }
  };

  const handleLogNewPath = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle || !newChosenPath || !newUnchosenApproach) return;
    try {
      await apiClient.logProbablePath({
        soul_id: soulName,
        path_title: newTitle,
        chosen_path: newChosenPath,
        unchosen_approach: newUnchosenApproach,
        manifestation_type: newManifestation,
      });
      setNewTitle('');
      setNewChosenPath('');
      setNewUnchosenApproach('');
      setShowLogModal(false);
      await fetchPaths();
    } catch (err) {
      console.error('Failed to log new probable path', err);
    }
  };

  const filteredPaths = paths.filter((p) => {
    if (selectedFilter === 'all') return true;
    return p.manifestation_type === selectedFilter;
  });

  const getManifestationIcon = (type: ManifestationType) => {
    switch (type) {
      case 'dream':
        return <Moon className="w-4 h-4 text-purple-400" />;
      case 'rumor':
        return <Volume2 className="w-4 h-4 text-amber-400" />;
      case 'alternate_scene':
        return <Eye className="w-4 h-4 text-sky-400" />;
      case 'echo_aspect':
        return <Sparkles className="w-4 h-4 text-indigo-400" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px] text-indigo-300">
        <GitBranch className="w-8 h-8 animate-spin mr-3 text-amber-400" />
        <span className="text-lg font-mono">Unspooling Probability Branches...</span>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8 p-4 md:p-6 text-slate-100">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-purple-950/80 to-slate-900 border border-purple-500/30 p-6 md:p-8 shadow-2xl">
        <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
          <GitBranch className="w-64 h-64 text-purple-300" />
        </div>

        <div className="relative z-10 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="flex items-center space-x-3 text-purple-400 font-mono text-sm tracking-wider uppercase">
                <GitBranch className="w-4 h-4" />
                <span>Phase 5 • Probable Paths Engine</span>
              </div>
              <h1 className="text-3xl md:text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-200 via-amber-200 to-sky-300">
                Probability Branches & Unchosen Paths
              </h1>
            </div>

            <button
              onClick={() => setShowLogModal(true)}
              className="inline-flex items-center px-4 py-2.5 rounded-xl bg-purple-500/20 hover:bg-purple-500/30 border border-purple-400/40 text-purple-200 font-medium transition-all shadow-lg cursor-pointer"
            >
              <PlusCircle className="w-4 h-4 mr-2" />
              Log Probable Fork
            </button>
          </div>

          <p className="text-slate-300 text-sm md:text-base max-w-3xl leading-relaxed">
            Choices produce consequences, but <span className="text-amber-300 font-semibold">unchosen paths remain narratively potent</span>. They return as dreams, whispers in the world, or interactive What-If scenes—without corrupting canonical event history.
          </p>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center gap-2 pt-4 border-t border-purple-500/20">
            {[
              { id: 'all', label: 'All Branches' },
              { id: 'dream', label: 'Dreams' },
              { id: 'rumor', label: 'Rumors' },
              { id: 'alternate_scene', label: 'Alternate Scenes' },
              { id: 'echo_aspect', label: 'Echo Aspects' },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setSelectedFilter(f.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all cursor-pointer ${
                  selectedFilter === f.id
                    ? 'bg-purple-500/30 border border-purple-400 text-purple-200 font-bold shadow-md'
                    : 'bg-slate-900/60 border border-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Probable Paths List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredPaths.map((path) => (
          <div
            key={path.id}
            className="bg-slate-900/80 border border-purple-500/30 rounded-xl p-5 hover:border-purple-400/60 transition-all flex flex-col justify-between space-y-4 shadow-xl"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="inline-flex items-center space-x-1.5 text-xs font-mono uppercase bg-purple-950/80 border border-purple-500/30 px-2.5 py-1 rounded-full text-purple-300">
                  {getManifestationIcon(path.manifestation_type)}
                  <span className="ml-1 font-bold">{path.manifestation_type.replace('_', ' ')}</span>
                </span>
                <span className="text-xs font-mono uppercase text-slate-400">{path.status}</span>
              </div>

              <h3 className="text-lg font-bold text-slate-100">{path.path_title}</h3>

              <div className="space-y-1 text-xs">
                <div>
                  <span className="text-slate-400 font-mono">Chosen Path:</span>{' '}
                  <span className="text-slate-200 font-medium">{path.chosen_path}</span>
                </div>
                <div>
                  <span className="text-slate-400 font-mono">Unchosen Approach:</span>{' '}
                  <span className="text-amber-300 font-semibold">{path.unchosen_approach}</span>
                </div>
              </div>

              <p className="text-xs text-slate-300 italic bg-slate-950/60 p-3 rounded-lg border border-purple-500/15">
                "{path.provenance_summary}"
              </p>
            </div>

            {/* Actions */}
            <div className="space-y-2 pt-3 border-t border-purple-500/15">
              <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                <span>Manifest as:</span>
                <div className="flex space-x-1">
                  {(['dream', 'rumor', 'alternate_scene'] as ManifestationType[]).map((t) => (
                    <button
                      key={t}
                      onClick={() => handleManifestType(path.id, t)}
                      className={`px-1.5 py-0.5 rounded text-[10px] uppercase font-mono cursor-pointer ${
                        path.manifestation_type === t
                          ? 'bg-purple-500/40 text-purple-200 font-bold border border-purple-400/50'
                          : 'bg-slate-950 text-slate-500 hover:text-slate-300'
                      }`}
                    >
                      {t[0].toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={() => handleSimulateWhatIf(path)}
                className="w-full py-2 px-3 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 border border-amber-400/40 text-amber-200 font-mono text-xs font-semibold flex items-center justify-center transition-all cursor-pointer"
              >
                <Play className="w-3.5 h-3.5 mr-2 text-amber-400" />
                Simulate What-If Scene
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* What-If Exploration Modal */}
      {exploringPath && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="bg-slate-900 border border-amber-400/50 rounded-2xl p-6 max-w-2xl w-full space-y-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-purple-500/20 pb-3">
              <div className="flex items-center space-x-2 text-amber-300 font-bold text-lg">
                <Compass className="w-5 h-5 text-amber-400" />
                <span>What-If Narrative Simulation</span>
              </div>
              <button
                onClick={() => setExploringPath(null)}
                className="text-slate-400 hover:text-slate-200 text-sm font-mono cursor-pointer"
              >
                ✕
              </button>
            </div>

            {isSimulating ? (
              <div className="flex items-center justify-center py-12 text-indigo-300">
                <Sparkles className="w-8 h-8 animate-spin mr-3 text-amber-400" />
                <span className="text-sm font-mono">Consulting Soulkeeper for Probability Divergence...</span>
              </div>
            ) : alternateScene ? (
              <div className="space-y-5">
                <div className="bg-slate-950/80 border border-purple-500/30 rounded-xl p-4 space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-amber-400 font-bold uppercase">{alternateScene.path_title}</span>
                    <span className="text-emerald-400 inline-flex items-center">
                      <ShieldCheck className="w-3.5 h-3.5 mr-1" /> Main Canon Intact
                    </span>
                  </div>
                  <div className="text-xs text-slate-400">
                    Simulating Unchosen Approach:{' '}
                    <span className="text-amber-300 font-semibold">{alternateScene.unchosen_approach}</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <h4 className="text-xs font-mono text-indigo-300 uppercase tracking-widest">
                    Soulkeeper Alternate Prose
                  </h4>
                  <p className="text-sm text-slate-200 italic leading-relaxed bg-purple-950/20 border border-purple-500/20 p-4 rounded-xl">
                    "{alternateScene.alternate_prose}"
                  </p>
                </div>

                <div className="space-y-2">
                  <h4 className="text-xs font-mono text-amber-400 uppercase tracking-widest">
                    Curiosity Questions Born From Divergence
                  </h4>
                  <ul className="space-y-1 text-xs text-slate-300">
                    {alternateScene.suggested_insights.map((insight, idx) => (
                      <li key={idx} className="flex items-start space-x-2">
                        <span className="text-amber-400 mt-0.5">•</span>
                        <span>{insight}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="pt-4 border-t border-purple-500/20 flex justify-end">
                  <button
                    onClick={() => setExploringPath(null)}
                    className="px-5 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs font-mono cursor-pointer"
                  >
                    Return to Timeline
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}

      {/* Log Probable Path Modal */}
      {showLogModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="bg-slate-900 border border-purple-400/40 rounded-2xl p-6 max-w-md w-full space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-purple-500/20 pb-3">
              <h3 className="text-lg font-bold text-purple-300 flex items-center">
                <GitBranch className="w-5 h-5 mr-2 text-purple-400" /> Log Probability Fork
              </h3>
              <button
                onClick={() => setShowLogModal(false)}
                className="text-slate-400 hover:text-slate-200 text-sm font-mono cursor-pointer"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleLogNewPath} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">Fork Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., The Crystal Gate Choice"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-purple-500/30 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-purple-400"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">Chosen Path (Canon)</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Opened with Light Token"
                  value={newChosenPath}
                  onChange={(e) => setNewChosenPath(e.target.value)}
                  className="w-full bg-slate-950 border border-purple-500/30 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-purple-400"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">Unchosen Approach (Probable Branch)</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Smashing the Crystal Key"
                  value={newUnchosenApproach}
                  onChange={(e) => setNewUnchosenApproach(e.target.value)}
                  className="w-full bg-slate-950 border border-purple-500/30 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-purple-400"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">Manifestation Type</label>
                <select
                  value={newManifestation}
                  onChange={(e) => setNewManifestation(e.target.value as ManifestationType)}
                  className="w-full bg-slate-950 border border-purple-500/30 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-purple-400"
                >
                  <option value="dream">Dream Vision</option>
                  <option value="rumor">World Rumor</option>
                  <option value="alternate_scene">Alternate Scene</option>
                  <option value="echo_aspect">Echo Aspect</option>
                </select>
              </div>

              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowLogModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono text-xs cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs cursor-pointer"
                >
                  Log Fork
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
