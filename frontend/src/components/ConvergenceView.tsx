import React, { useState } from 'react';
import type { CanonicalDiceRead } from '../types';
import { Users, Radio, Sparkles, Send, Zap } from 'lucide-react';

interface ConvergenceViewProps {
  currentRead: CanonicalDiceRead;
  soulName: string;
}

interface ConvergenceMessage {
  id: string;
  sender: string;
  role: 'Focus' | 'Anchor' | 'Witness' | 'Tempest';
  text: string;
  timestamp: string;
}

export const ConvergenceView: React.FC<ConvergenceViewProps> = ({ currentRead, soulName }) => {
  const [roomId] = useState('Convergence-Room-Alpha');
  const [activeRole, setActiveRole] = useState<'Focus' | 'Anchor' | 'Witness' | 'Tempest'>('Focus');
  const [messages, setMessages] = useState<ConvergenceMessage[]>([
    {
      id: '1',
      sender: 'Kaelen the Seeker',
      role: 'Focus',
      text: 'Cast roll: Oracle + Water + Transformation. Attempting to decode the submerged archive.',
      timestamp: '13:42'
    },
    {
      id: '2',
      sender: 'Soren',
      role: 'Witness',
      text: 'Witnessing beat. Standard memory facts confirmed. No canon contradiction found.',
      timestamp: '13:43'
    }
  ]);
  const [inputText, setInputText] = useState('');

  const handleSendMessage = () => {
    if (!inputText.trim()) return;
    const newMsg: ConvergenceMessage = {
      id: Date.now().toString(),
      sender: soulName,
      role: activeRole,
      text: inputText.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages((prev) => [...prev, newMsg]);
    setInputText('');
  };

  const handleSynthesizeConvergence = () => {
    const synMsg: ConvergenceMessage = {
      id: Date.now().toString(),
      sender: 'SOULKEEPER WEAVER',
      role: 'Witness',
      text: `SYNTHESIS BEAT: [Focus] ${soulName}'s Spark (${currentRead.interpretation.spark}) merges with the [Tempest] pressure (${currentRead.interpretation.pressure}). A shared revelation emerges at the ${currentRead.interpretation.domain}!`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages((prev) => [...prev, synMsg]);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-panel p-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <span className="text-xs uppercase tracking-widest text-pink-400 font-semibold flex items-center gap-1">
              <Radio size={14} className="animate-pulse text-pink-400" /> Real-time Multiplayer Resonance
            </span>
            <h2 className="text-2xl font-bold font-cinzel text-slate-100">Convergence Room Sanctuary</h2>
            <p className="text-xs text-slate-400">
              Multiple Souls gather around a shared Chronicle, weaving separate rolls into one mythic event.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="glass-pill text-xs text-emerald-400 border-emerald-500/30 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" /> Room: {roomId}
            </span>
            <button onClick={handleSynthesizeConvergence} className="btn-primary py-2 px-4 text-xs">
              <Zap size={14} /> Synthesize Shared Beat
            </button>
          </div>
        </div>
      </div>

      {/* Role Selection */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { role: 'Focus', desc: 'Active Soul whose intention is on the line' },
          { role: 'Anchor', desc: 'Chooses which existing Bond/Thread is at stake' },
          { role: 'Witness', desc: 'Confirms canon write-back and validates lore' },
          { role: 'Tempest', desc: 'Speaks for the environment and phenomenon pressure' }
        ].map((r) => (
          <div
            key={r.role}
            onClick={() => setActiveRole(r.role as any)}
            className={`cursor-pointer p-4 rounded-xl transition-all ${
              activeRole === r.role
                ? 'bg-slate-900 border-2 border-purple-500 shadow-glow-purple'
                : 'bg-slate-900/60 border border-slate-800 hover:bg-slate-900/90'
            }`}
          >
            <div className="flex justify-between items-center mb-1">
              <span className="font-bold text-sm font-cinzel text-slate-100">{r.role}</span>
              {activeRole === r.role && <Sparkles size={14} className="text-purple-400" />}
            </div>
            <p className="text-[11px] text-slate-400">{r.desc}</p>
          </div>
        ))}
      </div>

      {/* Live Room Feed & Chat */}
      <div className="glass-panel p-6 space-y-4">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
          <Users size={16} className="text-cyan-400" /> Live Room Chronicle Stream
        </h3>

        <div className="space-y-3 max-h-80 overflow-y-auto p-4 rounded-xl bg-slate-950/80 border border-slate-800">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`p-3 rounded-lg border text-xs space-y-1 ${
                m.sender.includes('SOULKEEPER')
                  ? 'bg-purple-950/60 border-purple-500/40 text-purple-200'
                  : 'bg-slate-900 border-slate-800 text-slate-200'
              }`}
            >
              <div className="flex justify-between items-center">
                <span className="font-bold font-cinzel text-slate-100 flex items-center gap-2">
                  {m.sender} <span className="glass-pill py-0 px-2 text-[10px] text-cyan-300">{m.role}</span>
                </span>
                <span className="text-[10px] text-slate-500">{m.timestamp}</span>
              </div>
              <p className="leading-relaxed">{m.text}</p>
            </div>
          ))}
        </div>

        {/* Input box */}
        <div className="flex gap-2">
          <input
            type="text"
            placeholder={`Speak as [${activeRole}] in ${roomId}...`}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-purple-500"
          />
          <button onClick={handleSendMessage} className="btn-primary py-2.5 px-5 text-xs">
            <Send size={14} /> Send
          </button>
        </div>
      </div>
    </div>
  );
};
