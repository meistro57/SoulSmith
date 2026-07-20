import React, { useState } from 'react';
import type { CanonicalDiceRead, DiceInterpretation, NumericDiceRoll } from '../types';
import { apiClient } from '../lib/api';
import { Camera, CheckCircle2, Sparkles, Sliders } from 'lucide-react';

interface DiceScanViewProps {
  onApplyScanRead: (read: CanonicalDiceRead) => void;
}

interface DetectedDie {
  die_role: keyof DiceInterpretation;
  poly_type: string;
  detected_value: number;
  confidence: number;
  alternates: number[];
}

export const DiceScanView: React.FC<DiceScanViewProps> = ({ onApplyScanRead }) => {
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState<{
    status: string;
    detected_dice: DetectedDie[];
    overall_confidence: number;
  } | null>(null);

  const handleCapturePhoto = async () => {
    setIsScanning(true);
    try {
      const data = await apiClient.ingestDicePhoto<{ status: string; detected_dice: DetectedDie[]; overall_confidence: number }>();
      setScanResult(data);
    } catch {
      setScanResult(generateFallbackScan());
    } finally {
      setIsScanning(false);
    }
  };

  const generateFallbackScan = () => ({
    status: 'needs_confirmation',
    overall_confidence: 0.89,
    detected_dice: [
      { die_role: 'spark' as const, poly_type: 'd20', detected_value: 17, confidence: 0.96, alternates: [1, 10] },
      { die_role: 'domain' as const, poly_type: 'd12', detected_value: 11, confidence: 0.91, alternates: [9] },
      { die_role: 'pressure' as const, poly_type: 'd10', detected_value: 8, confidence: 0.76, alternates: [3, 5] },
      { die_role: 'aim' as const, poly_type: 'd%', detected_value: 70, confidence: 0.94, alternates: [1] },
      { die_role: 'approach' as const, poly_type: 'd8', detected_value: 5, confidence: 0.88, alternates: [8] },
      { die_role: 'verdict' as const, poly_type: 'd6', detected_value: 1, confidence: 0.92, alternates: [2] },
      { die_role: 'thread' as const, poly_type: 'd4', detected_value: 4, confidence: 0.95, alternates: [3] }
    ]
  });

  const handleFaceOverride = (role: keyof DiceInterpretation, newFace: number) => {
    if (!scanResult) return;
    const updated = scanResult.detected_dice.map((d) =>
      d.die_role === role ? { ...d, detected_value: newFace, confidence: 1.0 } : d
    );
    setScanResult({ ...scanResult, detected_dice: updated });
  };

  const handleConfirmAndApply = async () => {
    if (!scanResult) return;
    const valueFor = (role: keyof DiceInterpretation, fallback: number) =>
      scanResult.detected_dice.find((d) => d.die_role === role)?.detected_value || fallback;
    const roll: NumericDiceRoll = {
      d20: valueFor('spark', 1),
      d12: valueFor('domain', 1),
      d10: valueFor('pressure', 1),
      percentile: valueFor('aim', 1),
      d8: valueFor('approach', 1),
      d6: valueFor('verdict', 1),
      d4: valueFor('thread', 1),
      grammar_version: '1.0.0'
    };
    onApplyScanRead(await apiClient.interpretDice(roll));
  };

  return (
    <div className="glass-panel p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <span className="text-xs uppercase tracking-widest text-cyan-400 font-semibold flex items-center gap-1">
            <Camera size={14} /> Computer Vision Optical Capture
          </span>
          <h2 className="text-2xl font-bold font-cinzel text-slate-100">Dice Tray Camera Scanner</h2>
        </div>

        <button
          onClick={handleCapturePhoto}
          disabled={isScanning}
          className={`btn-primary ${isScanning ? 'opacity-50 animate-pulse' : ''}`}
        >
          <Camera size={18} />
          {isScanning ? 'Analyzing Dice Tray...' : 'Capture Camera Photo'}
        </button>
      </div>

      {/* Camera Viewfinder Simulation */}
      <div className="relative h-56 rounded-xl bg-slate-950 border-2 border-dashed border-cyan-500/40 flex flex-col items-center justify-center text-center p-6 overflow-hidden">
        <div className="absolute inset-0 bg-radial-glow opacity-20 pointer-events-none" />
        <Camera size={48} className="text-cyan-400 opacity-60 mb-2 animate-pulse" />
        <p className="text-sm font-semibold text-slate-200">Position 7 Polyhedral Dice in Tray</p>
        <p className="text-xs text-slate-400">Adaptive thresholding & Simulated optical recognition proposes numeric face values for confirmation.</p>
      </div>

      {/* Scan Results */}
      {scanResult && (
        <div className="space-y-4 p-5 rounded-xl bg-slate-900/90 border border-slate-800">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1">
              <CheckCircle2 size={16} className="text-emerald-400" /> Overall Optical Confidence: {(scanResult.overall_confidence * 100).toFixed(0)}%
            </span>
            <span className="glass-pill text-xs text-cyan-300 border-cyan-500/30">
              {scanResult.status.replace('_', ' ')}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {scanResult.detected_dice.map((d) => {
              const isLow = d.confidence < 0.85;
              return (
                <div
                  key={d.die_role}
                  className={`p-3 rounded-lg border text-xs space-y-1 ${
                    isLow ? 'bg-amber-950/60 border-amber-500/50' : 'bg-slate-950 border-slate-800'
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <span className="font-bold uppercase text-slate-400">{d.die_role} ({d.poly_type})</span>
                    <span className={`font-semibold ${isLow ? 'text-amber-400' : 'text-emerald-400'}`}>
                      {(d.confidence * 100).toFixed(0)}%
                    </span>
                  </div>

                  <div className="text-base font-bold font-cinzel text-cyan-300">{d.detected_value}</div>

                  {/* Manual Face Override selector */}
                  <div className="pt-1 flex items-center gap-1">
                    <Sliders size={12} className="text-slate-500" />
                    <select
                      value={d.detected_value}
                      onChange={(e) => handleFaceOverride(d.die_role, Number(e.target.value))}
                      className="w-full bg-slate-900 border border-slate-800 text-[11px] text-slate-300 rounded px-1.5 py-0.5"
                    >
                      <option value={d.detected_value}>{d.detected_value} (Detected)</option>
                      {d.alternates.map((alt) => (
                        <option key={alt} value={alt}>
                          {alt} (Candidate)
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="flex justify-end pt-2">
            <button onClick={handleConfirmAndApply} className="btn-primary py-2 px-6 text-xs">
              <Sparkles size={14} /> Confirm & Apply to 3D Sanctuary
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
