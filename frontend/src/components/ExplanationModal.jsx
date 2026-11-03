import React, { useState } from 'react';
import { 
  X, 
  HelpCircle, 
  Sparkles,
  ChevronDown,
  ChevronUp,
  Clock,
  TrendingDown,
  TrendingUp,
  CheckCircle2,
  BookOpen,
  Info
} from 'lucide-react';

export default function ExplanationModal({ topicRisk, onClose }) {
  const [showMathDetails, setShowMathDetails] = useState(false);

  if (!topicRisk) return null;

  const expl = topicRisk.local_explanation;
  const isHighRisk = topicRisk.retention_status === 'high_risk';
  const isModRisk = topicRisk.retention_status === 'moderate_risk';

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-3xl max-w-xl w-full shadow-2xl border border-[#EDE9FE] overflow-hidden my-6 animate-in fade-in zoom-in-95 duration-150">
        
        {/* Friendly Header */}
        <div className="p-6 bg-gradient-to-r from-violet-50 to-[#FAF9FF] border-b border-[#EDE9FE] flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-violet-700">
                {topicRisk.module_name}
              </span>
            </div>
            <h2 className="text-lg font-extrabold text-[#1E1B4B]">
              {topicRisk.topic_name}
            </h2>
            <div className="flex items-center gap-2 pt-1">
              <span className={
                isHighRisk 
                  ? 'px-3 py-1 rounded-full text-xs font-bold bg-violet-100 text-violet-800'
                  : isModRisk 
                  ? 'px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-200'
                  : 'px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200'
              }>
                {isHighRisk ? 'Ready for a Quick Refresh' : isModRisk ? 'Review Within 2 Days' : 'Memory Retained'}
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 hover:bg-white rounded-full transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto">
          
          {/* Friendly Takeaway Box */}
          <div className="p-4 rounded-2xl bg-[#FAF9FF] border border-[#EDE9FE] flex items-start gap-3">
            <div className="w-8 h-8 rounded-xl bg-violet-100 text-violet-700 flex items-center justify-center shrink-0 mt-0.5">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-violet-900 mb-1">
                Why does your schedule suggest this?
              </h3>
              <p className="text-xs text-slate-600 leading-relaxed font-medium">
                {expl?.summary || "Spaced repetition works best when you review a topic just as it begins to fade from short-term recall. A short 10-15 minute review will cement this concept."}
              </p>
            </div>
          </div>

          {/* Key Influencing Factors (Friendly, clean list) */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Key Factors Noticed by Your Assistant
            </h4>

            <div className="space-y-2.5">
              {/* Positive Factors (Things suggesting a review is needed) */}
              {expl?.positive_factors?.slice(0, 2).map((factor, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-2xl bg-white border border-slate-200 flex items-start gap-3"
                >
                  <div className="w-7 h-7 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center shrink-0 mt-0.5">
                    <Clock className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-800 capitalize mb-0.5">
                      {factor.factor.replace(/_/g, ' ')}
                    </div>
                    <p className="text-xs text-slate-600 font-medium leading-relaxed">
                      {factor.explanation}
                    </p>
                  </div>
                </div>
              ))}

              {/* Negative Factors (Things working in your favor) */}
              {expl?.negative_factors?.slice(0, 2).map((factor, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-2xl bg-white border border-slate-200 flex items-start gap-3"
                >
                  <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0 mt-0.5">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-800 capitalize mb-0.5">
                      {factor.factor.replace(/_/g, ' ')}
                    </div>
                    <p className="text-xs text-slate-600 font-medium leading-relaxed">
                      {factor.explanation}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Technical ML Dropdown (Hidden by default for simplicity, expandable for evaluators) */}
          <div className="pt-2 border-t border-slate-100">
            <button
              onClick={() => setShowMathDetails(!showMathDetails)}
              className="w-full flex items-center justify-between py-2 text-xs font-bold text-slate-400 hover:text-violet-700 transition-colors"
            >
              <div className="flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5" />
                <span>Show Machine Learning Details (Log-Odds & Weights)</span>
              </div>
              {showMathDetails ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>

            {showMathDetails && expl && (
              <div className="mt-3 p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-4">
                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="p-2 bg-white rounded-xl border border-slate-200">
                    <span className="text-[10px] text-slate-400 uppercase font-bold block">Intercept</span>
                    <span className="font-mono font-bold text-slate-700">{expl.intercept.toFixed(3)}</span>
                  </div>
                  <div className="p-2 bg-white rounded-xl border border-slate-200">
                    <span className="text-[10px] text-slate-400 uppercase font-bold block">Log-Odds</span>
                    <span className="font-mono font-bold text-slate-700">{expl.predicted_log_odds.toFixed(3)}</span>
                  </div>
                  <div className="p-2 bg-white rounded-xl border border-slate-200">
                    <span className="text-[10px] text-slate-400 uppercase font-bold block">Model Risk</span>
                    <span className="font-mono font-bold text-violet-700">{(expl.reconstructed_probability * 100).toFixed(1)}%</span>
                  </div>
                </div>

                {expl.all_factors && (
                  <div className="overflow-x-auto rounded-xl border border-slate-200">
                    <table className="w-full text-left text-xs bg-white">
                      <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold">
                        <tr>
                          <th className="p-2">Feature</th>
                          <th className="p-2">Value</th>
                          <th className="p-2 text-right">Contribution</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {expl.all_factors.map((f, i) => (
                          <tr key={i}>
                            <td className="p-2 capitalize text-slate-700">{f.factor.replace(/_/g, ' ')}</td>
                            <td className="p-2 font-mono text-slate-500">{f.value}</td>
                            <td className={`p-2 font-mono text-right font-bold ${
                              f.contribution > 0 ? 'text-amber-600' :
                              f.contribution < 0 ? 'text-emerald-600' : 'text-slate-400'
                            }`}>
                              {f.contribution > 0 ? `+${f.contribution.toFixed(4)}` : f.contribution.toFixed(4)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>

        </div>

        {/* Footer */}
        <div className="p-4 bg-[#FAF9FF] border-t border-[#EDE9FE] flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2.5 bg-violet-600 hover:bg-violet-700 text-white rounded-xl text-xs font-bold shadow-soft transition-all"
          >
            Got it, thanks!
          </button>
        </div>

      </div>
    </div>
  );
}
