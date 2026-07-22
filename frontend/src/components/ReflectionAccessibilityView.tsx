// frontend/src/components/ReflectionAccessibilityView.tsx
import React, { useCallback, useEffect, useState } from 'react';
import type { NarrativeIntensity, PlayerPreferences, PrivateNote, ReflectionSession, SpiritualFraming } from '../types';
import { apiClient } from '../lib/api';
import { BookOpen, ShieldCheck, Lock, Eye, EyeOff, Sliders, Sparkles, Download, Plus, X, HeartHandshake } from 'lucide-react';

interface ReflectionAccessibilityViewProps {
  soulName: string;
}

const PROMPT_PRESETS = [
  "What pattern did you notice in today's choices that was not visible before?",
  "Which thread or symbol resonated most deeply during your encounters?",
  "What promise or debt was created today that still demands an answer?",
  "If your Aspect could speak to their future form, what warning would they give?",
];

export const ReflectionAccessibilityView: React.FC<ReflectionAccessibilityViewProps> = ({ soulName }) => {
  const [activeTab, setActiveTab] = useState<'reflection' | 'notes' | 'settings'>('reflection');
  
  // Reflection State
  const [promptQuestion, setPromptQuestion] = useState<string>(PROMPT_PRESETS[0]);
  const [reflectionText, setReflectionText] = useState<string>('');
  const [shareWithAi, setShareWithAi] = useState<boolean>(false);
  const [sessions, setSessions] = useState<ReflectionSession[]>([]);

  // Private Notes State
  const [privateNotes, setPrivateNotes] = useState<PrivateNote[]>([]);
  const [showNoteModal, setShowNoteModal] = useState<boolean>(false);
  const [noteTitle, setNoteTitle] = useState<string>('');
  const [noteContent, setNoteContent] = useState<string>('');

  // Preferences State
  const [preferences, setPreferences] = useState<PlayerPreferences>({
    soul_id: soulName,
    narrative_intensity: 'balanced',
    spiritual_framing: 'secular_mythology',
    reduced_motion: false,
    high_contrast: false,
    allow_ai_indexing_default: false,
  });

  const [loading, setLoading] = useState<boolean>(true);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const prefRes = await apiClient.getPlayerPreferences(soulName);
      setPreferences(prefRes.preferences);

      const refRes = await apiClient.listReflectionSessions(soulName);
      setSessions(refRes.sessions);

      const notesRes = await apiClient.listPrivateNotes(soulName);
      setPrivateNotes(notesRes.notes);
    } catch (err) {
      console.error('Failed to load reflection & accessibility data:', err);
    } finally {
      setLoading(false);
    }
  }, [soulName]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleReflectionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reflectionText.trim()) return;
    try {
      await apiClient.createReflectionSession({
        soul_id: soulName,
        prompt_question: promptQuestion,
        player_reflection: reflectionText.trim(),
        share_with_ai: shareWithAi,
      });
      setReflectionText('');
      setStatusMessage('Optional reflection recorded in player memory.');
      fetchData();
      setTimeout(() => setStatusMessage(null), 4000);
    } catch (err) {
      console.error('Failed to save reflection:', err);
    }
  };

  const handleNoteSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!noteTitle.trim() || !noteContent.trim()) return;
    try {
      await apiClient.createPrivateNote({
        soul_id: soulName,
        title: noteTitle.trim(),
        content: noteContent.trim(),
        allow_ai_indexing: false,
      });
      setShowNoteModal(false);
      setNoteTitle('');
      setNoteContent('');
      fetchData();
    } catch (err) {
      console.error('Failed to save private note:', err);
    }
  };

  const handleUpdatePreferences = async (newPrefs: Partial<PlayerPreferences>) => {
    const updated = { ...preferences, ...newPrefs };
    setPreferences(updated);
    try {
      await apiClient.updatePlayerPreferences({
        soul_id: soulName,
        narrative_intensity: updated.narrative_intensity,
        spiritual_framing: updated.spiritual_framing,
        reduced_motion: updated.reduced_motion,
        high_contrast: updated.high_contrast,
        allow_ai_indexing_default: updated.allow_ai_indexing_default,
      });
      setStatusMessage('Preferences updated successfully.');
      setTimeout(() => setStatusMessage(null), 3000);
    } catch (err) {
      console.error('Failed to update preferences:', err);
    }
  };

  const handleExportData = () => {
    const exportData = {
      soul_id: soulName,
      preferences,
      reflection_sessions: sessions,
      private_notes: privateNotes,
      exported_at: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `soulsmith_${soulName.toLowerCase().replace(/\s+/g, '_')}_memory_export.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 border border-emerald-500/30 p-6 md:p-8 shadow-2xl">
        <div className="relative z-10 space-y-3">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-400/10 border border-emerald-400/30 text-emerald-300 text-xs font-mono">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Phase 8: Reflection & Privacy Sovereignty</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-200 via-teal-100 to-indigo-200">
            Reflection & Accessibility Control Vault
          </h1>
          <p className="text-slate-300 text-xs md:text-sm max-w-3xl leading-relaxed font-serif">
            "Experience can be accumulated. Transformation must be integrated." Reflection is always optional, private notes are strictly excluded from AI models unless explicitly permitted, and content controls preserve player sovereignty.
          </p>
        </div>
      </div>

      {statusMessage && (
        <div className="p-3.5 rounded-xl bg-emerald-950/80 border border-emerald-500/40 text-emerald-200 text-xs font-mono flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{statusMessage}</span>
          </div>
          <button onClick={() => setStatusMessage(null)} className="text-slate-400 hover:text-slate-200">
            ✕
          </button>
        </div>
      )}

      {/* Sub-Tab Navigation */}
      <div className="flex border-b border-indigo-500/20 font-mono text-xs">
        <button
          onClick={() => setActiveTab('reflection')}
          className={`py-3 px-5 font-bold transition flex items-center gap-2 border-b-2 cursor-pointer ${
            activeTab === 'reflection'
              ? 'border-emerald-400 text-emerald-300 bg-emerald-950/20'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <BookOpen size={14} />
          <span>End-of-Session Reflection</span>
        </button>

        <button
          onClick={() => setActiveTab('notes')}
          className={`py-3 px-5 font-bold transition flex items-center gap-2 border-b-2 cursor-pointer ${
            activeTab === 'notes'
              ? 'border-emerald-400 text-emerald-300 bg-emerald-950/20'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Lock size={14} />
          <span>Private Notes ({privateNotes.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('settings')}
          className={`py-3 px-5 font-bold transition flex items-center gap-2 border-b-2 cursor-pointer ${
            activeTab === 'settings'
              ? 'border-emerald-400 text-emerald-300 bg-emerald-950/20'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Sliders size={14} />
          <span>Intensity & Accessibility</span>
        </button>
      </div>

      {/* TAB 1: END-OF-SESSION REFLECTION */}
      {activeTab === 'reflection' && (
        <div className="space-y-6">
          <div className="bg-slate-900/90 backdrop-blur-md rounded-2xl border border-emerald-500/30 p-6 space-y-4 shadow-xl">
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <HeartHandshake className="w-4 h-4 text-emerald-400" />
              <span>Optional End-of-Session Narrative Reflection</span>
            </h3>

            <div className="space-y-3 font-mono text-xs">
              <div>
                <label className="block text-slate-300 mb-1.5 font-bold">Select Reflection Prompt</label>
                <select
                  value={promptQuestion}
                  onChange={(e) => setPromptQuestion(e.target.value)}
                  className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl p-3 text-slate-100 focus:outline-none focus:border-emerald-400"
                >
                  {PROMPT_PRESETS.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </div>

              <form onSubmit={handleReflectionSubmit} className="space-y-4">
                <div>
                  <label className="block text-slate-300 mb-1">Your Personal Reflection</label>
                  <textarea
                    required
                    rows={4}
                    placeholder="Write your thoughts or insights here. This is your safe space..."
                    value={reflectionText}
                    onChange={(e) => setReflectionText(e.target.value)}
                    className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl p-3 text-slate-100 focus:outline-none focus:border-emerald-400 font-serif leading-relaxed text-sm"
                  />
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/80 border border-indigo-500/20">
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="shareAiCheck"
                      checked={shareWithAi}
                      onChange={(e) => setShareWithAi(e.target.checked)}
                      className="rounded border-slate-700 bg-slate-900 text-emerald-400 focus:ring-emerald-400"
                    />
                    <label htmlFor="shareAiCheck" className="text-slate-300 text-xs cursor-pointer">
                      Allow Soulkeeper AI to use this reflection for future subtle prompts
                    </label>
                  </div>
                  <span className="text-[10px] text-slate-500 flex items-center gap-1">
                    {shareWithAi ? <Eye size={12} className="text-emerald-400" /> : <EyeOff size={12} className="text-amber-400" />}
                    {shareWithAi ? 'AI Access Granted' : 'AI Excluded'}
                  </span>
                </div>

                <button
                  type="submit"
                  className="py-2.5 px-6 rounded-xl bg-emerald-400 text-slate-950 font-bold font-mono text-xs hover:bg-emerald-300 transition cursor-pointer shadow-lg"
                >
                  Record Session Reflection
                </button>
              </form>
            </div>
          </div>

          {/* Past Reflection Sessions List */}
          <div className="space-y-3">
            <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
              Past Session Reflections ({sessions.length})
            </h4>

            {sessions.length === 0 ? (
              <div className="text-slate-500 text-center py-6 font-mono text-xs">
                No past session reflections logged yet.
              </div>
            ) : (
              <div className="space-y-3">
                {sessions.map((s) => (
                  <div key={s.id} className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2 text-xs">
                    <div className="flex justify-between items-center text-slate-400 font-mono text-[11px]">
                      <span className="font-bold text-amber-300">"{s.prompt_question}"</span>
                      <span className="text-slate-500">{s.created_at || 'Recent Session'}</span>
                    </div>
                    <p className="text-slate-200 font-serif text-sm leading-relaxed italic">
                      "{s.player_reflection}"
                    </p>
                    <div className="flex justify-end text-[10px] font-mono">
                      <span className={s.share_with_ai ? 'text-emerald-400' : 'text-slate-500'}>
                        {s.share_with_ai ? '• Shared with AI' : '• Private (AI Excluded)'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: VAULT OF PRIVATE NOTES */}
      {activeTab === 'notes' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Lock className="w-4 h-4 text-emerald-400" />
                <span>Vault of Private Journal Notes</span>
              </h3>
              <p className="text-xs text-slate-400">
                Private notes are strictly excluded from AI models and vector memory indices.
              </p>
            </div>
            <button
              onClick={() => setShowNoteModal(true)}
              className="py-2 px-4 rounded-xl bg-emerald-400 text-slate-950 font-mono text-xs font-bold flex items-center gap-1.5 hover:bg-emerald-300 transition cursor-pointer shadow-lg"
            >
              <Plus size={14} />
              <span>New Private Note</span>
            </button>
          </div>

          {loading ? (
            <div className="text-center py-6 font-mono text-slate-400 animate-pulse text-xs">
              Decrypting private notes vault...
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {privateNotes.map((note) => (
                <div key={note.id} className="p-5 rounded-2xl bg-slate-900/90 border border-indigo-500/20 space-y-3 shadow-xl">
                  <div className="flex justify-between items-start">
                    <h4 className="font-bold text-slate-100 text-sm">{note.title}</h4>
                    <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-500/30 flex items-center gap-1">
                      <Lock size={10} /> Excluded from AI
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 font-serif leading-relaxed whitespace-pre-wrap">
                    {note.content}
                  </p>
                  <div className="text-[10px] font-mono text-slate-500 text-right">
                    {note.created_at || 'Saved in Vault'}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* New Private Note Modal */}
          {showNoteModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
              <div className="bg-slate-900 border border-emerald-400/50 rounded-2xl p-6 max-w-md w-full space-y-4 shadow-2xl">
                <div className="flex items-center justify-between border-b border-indigo-500/20 pb-3">
                  <h3 className="text-lg font-bold text-emerald-200 flex items-center gap-2">
                    <Lock className="w-4 h-4 text-emerald-400" />
                    <span>Create Private Note</span>
                  </h3>
                  <button onClick={() => setShowNoteModal(false)} className="text-slate-400 hover:text-slate-200">
                    <X className="w-4 h-4" />
                  </button>
                </div>

                <form onSubmit={handleNoteSubmit} className="space-y-4 text-xs font-mono">
                  <div>
                    <label className="block text-slate-300 mb-1">Note Title</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Unspoken Thoughts on the Salt Spire"
                      value={noteTitle}
                      onChange={(e) => setNoteTitle(e.target.value)}
                      className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl p-2.5 text-slate-100 focus:outline-none focus:border-emerald-400"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-300 mb-1">Private Content</label>
                    <textarea
                      required
                      rows={5}
                      placeholder="Write your private note..."
                      value={noteContent}
                      onChange={(e) => setNoteContent(e.target.value)}
                      className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl p-2.5 text-slate-100 focus:outline-none focus:border-emerald-400 font-serif leading-relaxed text-xs"
                    />
                  </div>

                  <div className="pt-2 flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => setShowNoteModal(false)}
                      className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 font-bold hover:bg-slate-700"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 rounded-xl bg-emerald-400 text-slate-950 font-bold hover:bg-emerald-300 shadow-md"
                    >
                      Save to Vault
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: INTENSITY & ACCESSIBILITY SETTINGS */}
      {activeTab === 'settings' && (
        <div className="space-y-6">
          <div className="bg-slate-900/90 backdrop-blur-md rounded-2xl border border-indigo-500/20 p-6 space-y-6 shadow-xl">
            {/* Narrative Intensity */}
            <div className="space-y-3">
              <h4 className="text-sm font-bold text-slate-100 font-mono uppercase tracking-wider">
                Narrative Intensity Level
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
                {[
                  { id: 'gentle', label: 'Gentle', desc: 'Mild stakes, calm pacing' },
                  { id: 'balanced', label: 'Balanced', desc: 'Standard mythic tension' },
                  { id: 'deep_mythic', label: 'Deep Mythic', desc: 'High psychological resonance' },
                  { id: 'unfiltered', label: 'Unfiltered', desc: 'Raw consequence weight' },
                ].map((item) => (
                  <button
                    key={item.id}
                    onClick={() => handleUpdatePreferences({ narrative_intensity: item.id as NarrativeIntensity })}
                    className={`p-3.5 rounded-xl border text-left space-y-1 transition cursor-pointer ${
                      preferences.narrative_intensity === item.id
                        ? 'bg-emerald-950/80 border-emerald-400 text-emerald-200 shadow-md'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <div className="font-bold text-slate-100">{item.label}</div>
                    <p className="text-[11px] font-serif text-slate-400">{item.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Spiritual Framing */}
            <div className="space-y-3 pt-4 border-t border-slate-800">
              <h4 className="text-sm font-bold text-slate-100 font-mono uppercase tracking-wider">
                Spiritual Framing Controls
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
                {[
                  { id: 'secular_mythology', label: 'Pure Secular Mythology', desc: 'Framed strictly as symbolic storytelling without spiritual claims.' },
                  { id: 'opt_in_spiritual', label: 'Opt-In Spiritual Framing', desc: 'Allows archetypal, esoteric, and spiritual narrative motifs.' },
                ].map((item) => (
                  <button
                    key={item.id}
                    onClick={() => handleUpdatePreferences({ spiritual_framing: item.id as SpiritualFraming })}
                    className={`p-3.5 rounded-xl border text-left space-y-1 transition cursor-pointer ${
                      preferences.spiritual_framing === item.id
                        ? 'bg-emerald-950/80 border-emerald-400 text-emerald-200 shadow-md'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <div className="font-bold text-slate-100">{item.label}</div>
                    <p className="text-[11px] font-serif text-slate-400">{item.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Accessibility & Visual Toggles */}
            <div className="space-y-3 pt-4 border-t border-slate-800 font-mono text-xs">
              <h4 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
                Accessibility Toggles
              </h4>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                  <div>
                    <span className="font-bold text-slate-200 block">Reduced Motion</span>
                    <span className="text-[11px] text-slate-400 font-serif">Disables fast 3D dice spinning & heavy background animations.</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={preferences.reduced_motion}
                    onChange={(e) => handleUpdatePreferences({ reduced_motion: e.target.checked })}
                    className="rounded border-slate-700 bg-slate-900 text-emerald-400 focus:ring-emerald-400 cursor-pointer"
                  />
                </div>

                <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                  <div>
                    <span className="font-bold text-slate-200 block">High Contrast Mode</span>
                    <span className="text-[11px] text-slate-400 font-serif">Enforces maximum WCAG contrast for legibility.</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={preferences.high_contrast}
                    onChange={(e) => handleUpdatePreferences({ high_contrast: e.target.checked })}
                    className="rounded border-slate-700 bg-slate-900 text-emerald-400 focus:ring-emerald-400 cursor-pointer"
                  />
                </div>
              </div>
            </div>

            {/* Data Sovereignty & Export */}
            <div className="pt-4 border-t border-slate-800 space-y-3 font-mono text-xs">
              <h4 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
                Data Sovereignty & Disengagement
              </h4>

              <div className="flex flex-wrap gap-3">
                <button
                  onClick={handleExportData}
                  className="py-2.5 px-4 rounded-xl bg-indigo-950 hover:bg-indigo-900 border border-indigo-500/40 text-indigo-200 font-bold flex items-center gap-2 transition cursor-pointer"
                >
                  <Download size={14} />
                  <span>Export Complete Memory Vault (JSON)</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
