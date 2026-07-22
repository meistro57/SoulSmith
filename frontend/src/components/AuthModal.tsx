// frontend/src/components/AuthModal.tsx
import React, { useState } from 'react';
import type { User } from '../types';
import { apiClient, setStoredAuthToken } from '../lib/api';
import { Sparkles, KeyRound, Mail, User as UserIcon, Lock, ArrowRight, ShieldCheck } from 'lucide-react';

interface AuthModalProps {
  onClose: () => void;
  onSuccess: (user: User) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ onClose, onSuccess }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form Fields
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isLogin) {
        const res = await apiClient.login({
          username_or_email: username || email,
          password,
        });
        setStoredAuthToken(res.access_token);
        onSuccess(res.user);
        onClose();
      } else {
        const res = await apiClient.signup({
          email,
          username,
          password,
          display_name: displayName || username,
        });
        setStoredAuthToken(res.access_token);
        onSuccess(res.user);
        onClose();
      }
    } catch (err: any) {
      setError(err?.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md">
      <div className="bg-slate-900 border border-amber-400/50 rounded-2xl p-6 md:p-8 max-w-md w-full space-y-6 shadow-2xl relative overflow-hidden">
        {/* Decorative Background Glow */}
        <div className="absolute -top-12 -right-12 w-40 h-40 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-12 -left-12 w-40 h-40 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-indigo-500/20 pb-4">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-5 h-5 text-amber-400" />
            <h2 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-amber-200 to-indigo-200">
              {isLogin ? 'SoulKeeper Authentication' : 'Create SoulSmith Account'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 text-sm font-mono cursor-pointer"
          >
            ✕
          </button>
        </div>

        {/* Tab Toggle */}
        <div className="grid grid-cols-2 gap-1 bg-slate-950 p-1 rounded-xl border border-indigo-500/20 text-xs font-mono">
          <button
            type="button"
            onClick={() => {
              setIsLogin(true);
              setError(null);
            }}
            className={`py-2 rounded-lg font-bold transition-all cursor-pointer ${
              isLogin
                ? 'bg-amber-500/20 text-amber-200 border border-amber-400/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Log In
          </button>
          <button
            type="button"
            onClick={() => {
              setIsLogin(false);
              setError(null);
            }}
            className={`py-2 rounded-lg font-bold transition-all cursor-pointer ${
              !isLogin
                ? 'bg-amber-500/20 text-amber-200 border border-amber-400/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Sign Up
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-3 rounded-lg bg-red-950/80 border border-red-500/40 text-red-200 text-xs font-mono space-y-1">
            <div className="font-bold flex items-center">
              <KeyRound className="w-3.5 h-3.5 mr-1.5 shrink-0 text-red-400" /> Authentication Error
            </div>
            <p className="text-red-300">{error}</p>
          </div>
        )}

        {/* Auth Form */}
        <form onSubmit={handleSubmit} className="space-y-4 text-sm">
          {!isLogin && (
            <div>
              <label className="block text-xs font-mono text-slate-300 mb-1">Display Name</label>
              <div className="relative">
                <UserIcon className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="text"
                  required
                  placeholder="e.g. Kaelen Star-Watcher"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl pl-9 pr-3 py-2 text-slate-100 focus:outline-none focus:border-amber-400"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-mono text-slate-300 mb-1">
              {isLogin ? 'Username or Email' : 'Username'}
            </label>
            <div className="relative">
              <UserIcon className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                required
                placeholder={isLogin ? 'e.g. kaelen or kaelen@star.org' : 'e.g. kaelen'}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl pl-9 pr-3 py-2 text-slate-100 focus:outline-none focus:border-amber-400"
              />
            </div>
          </div>

          {!isLogin && (
            <div>
              <label className="block text-xs font-mono text-slate-300 mb-1">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="email"
                  required
                  placeholder="e.g. kaelen@starforge.org"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl pl-9 pr-3 py-2 text-slate-100 focus:outline-none focus:border-amber-400"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-mono text-slate-300 mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-950 border border-indigo-500/30 rounded-xl pl-9 pr-3 py-2 text-slate-100 focus:outline-none focus:border-amber-400"
              />
            </div>
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={loading}
              className={`w-full py-2.5 rounded-xl font-bold font-mono text-xs text-slate-950 bg-amber-400 hover:bg-amber-300 transition-all flex items-center justify-center cursor-pointer shadow-lg shadow-amber-500/10 ${
                loading ? 'opacity-50 animate-pulse' : ''
              }`}
            >
              <ShieldCheck className="w-4 h-4 mr-2" />
              {loading
                ? 'Verifying Soul Token...'
                : isLogin
                ? 'Log In to SoulSmith'
                : 'Create Account & Sign In'}
              <ArrowRight className="w-4 h-4 ml-2" />
            </button>
          </div>
        </form>

        <p className="text-[11px] text-center text-slate-500 font-mono">
          SoulSmith authentication uses encrypted bcrypt hashing & JWT tokens.
        </p>
      </div>
    </div>
  );
};
