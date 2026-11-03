import React, { useState } from 'react';
import { 
  X, 
  HelpCircle, 
  ArrowUpRight, 
  ArrowDownRight, 
  Minus,
  Sparkles,
  Info,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

export default function ExplanationModal({ topicRisk, onClose }) {
  const [showAllFactors, setShowAllFactors] = useState(false);

  if (!topicRisk) return null;

  const expl = topicRisk.local_explanation;
  const prob = (topicRisk.forgetting_probability * 100).toFixed(1);

  const getStatusBadge = (status) => {
    if (status === 'high_risk') {
      return (
        <span className="px-3 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200">
          High Risk (≥ 60%)
        </span>
      );
    }
    if (status === 'moderate_risk') {
      return (
        <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200">
          Moderate Risk (35% – 60%)
        </span>
      );
    }
    return (
      <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
        Retained (&lt; 35%)
      </span>
    );
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-3xl max-w-2xl w-full shadow-2xl border border-[#EDE9FE] overflow-hidden my-8 animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-6 bg-gradient-to-r from-violet-50 to-[#FAF9FF] border-b border-[#EDE9FE] flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold uppercase tracking-wider text-violet-700">
                {topicRisk.module_name}
              </span>
              <span className="text-slate-300">•</span>
              <span className="text-xs text-slate-500 font-medium">Topic #{topicRisk.topic_id}</span>
            </div>
            <h2 className="text-xl font-extrabold text-[#1E1B4B]">
              {topicRisk.topic_name}
            </h2>
            <div className="flex items-center gap-3 mt-3">
              <div className="text-2xl font-black text-[#1E1B4B]">
                {prob}%
                <span className="text-xs font-semibold text-slate-500 ml-1.5 font-normal">
                  predicted forgetting risk
                </span>
              </div>
              {getStatusBadge(topicRisk.retention_status)}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 hover:bg-white rounded-full transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto">
          {/* Mathematical Summary Card */}
          {expl && (
            <div className="p-4 rounded-2xl bg-white border border-[#EDE9FE] shadow-card">
              <div className="flex items-center gap-2 mb-2 text-xs font-bold text-violet-900">
                <Sparkles className="w-4 h-4 text-violet-600" />
                <span>Explainable Model Reasoning (Log-Odds Space)</span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed mb-3">
                {expl.summary || "Predictions are generated via Logistic Regression with feature contributions measured in log-odds relative to the baseline intercept."}
              </p>
              <div className="grid grid-cols-3 gap-2.5 pt-2 border-t border-slate-100 text-center">
                <div className="p-2 rounded-xl bg-slate-50">
                  <div className="text-[10px] uppercase font-bold text-slate-400">Model Intercept</div>
                  <div className="text-sm font-extrabold text-slate-700">{expl.intercept.toFixed(3)}</div>
                </div>
                <div className="p-2 rounded-xl bg-slate-50">
                  <div className="text-[10px] uppercase font-bold text-slate-400">Total Log-Odds</div>
                  <div className="text-sm font-extrabold text-slate-700">{expl.predicted_log_odds.toFixed(3)}</div>
                </div>
                <div className="p-2 rounded-xl bg-slate-50">
                  <div className="text-[10px] uppercase font-bold text-slate-400">Sigmoid Probability</div>
                  <div className="text-sm font-extrabold text-violet-700">{(expl.reconstructed_probability * 100).toFixed(1)}%</div>
                </div>
              </div>
            </div>
          )}

          {/* Top Positive Factors (Increasing Risk) */}
          {expl?.positive_factors && expl.positive_factors.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <div className="w-6 h-6 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center">
                  <ArrowUpRight className="w-4 h-4" />
                </div>
                <h3 className="text-sm font-bold text-[#1E1B4B]">
                  Factors Increasing Forgetting Risk ({expl.positive_factors.length})
                </h3>
              </div>
              <div className="space-y-2.5">
                {expl.positive_factors.map((factor, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-2xl bg-rose-50/50 border border-rose-100 flex items-start justify-between gap-3"
                  >
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-bold text-xs text-rose-900 capitalize">
                          {factor.factor.replace(/_/g, ' ')}
                        </span>
                        <span className="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-white text-rose-700 border border-rose-200">
                          Observed: {factor.value}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 leading-relaxed">
                        {factor.explanation}
                      </p>
                    </div>
                    <div className="shrink-0 text-right">
                      <span className="text-xs font-black text-rose-600 px-2 py-1 rounded-lg bg-white border border-rose-200 shadow-sm">
                        +{factor.contribution.toFixed(3)}
                      </span>
                      <div className="text-[10px] text-slate-400 mt-1">log-odds</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Top Negative Factors (Reducing Risk) */}
          {expl?.negative_factors && expl.negative_factors.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <div className="w-6 h-6 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                  <ArrowDownRight className="w-4 h-4" />
                </div>
                <h3 className="text-sm font-bold text-[#1E1B4B]">
                  Factors Decreasing Forgetting Risk ({expl.negative_factors.length})
                </h3>
              </div>
              <div className="space-y-2.5">
                {expl.negative_factors.map((factor, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-2xl bg-emerald-50/50 border border-emerald-100 flex items-start justify-between gap-3"
                  >
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-bold text-xs text-emerald-900 capitalize">
                          {factor.factor.replace(/_/g, ' ')}
                        </span>
                        <span className="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-white text-emerald-700 border border-emerald-200">
                          Observed: {factor.value}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 leading-relaxed">
                        {factor.explanation}
                      </p>
                    </div>
                    <div className="shrink-0 text-right">
                      <span className="text-xs font-black text-emerald-600 px-2 py-1 rounded-lg bg-white border border-emerald-200 shadow-sm">
                        {factor.contribution.toFixed(3)}
                      </span>
                      <div className="text-[10px] text-slate-400 mt-1">log-odds</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Fallback if local explanation not available */}
          {(!expl || (!expl.positive_factors?.length && !expl.negative_factors?.length)) && (
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-center">
              <p className="text-xs text-slate-600">
                No individual factors exceeded the significance threshold. The risk score aligns with the cohort baseline.
              </p>
            </div>
          )}

          {/* Expandable All 13 Factors Accordion */}
          {expl?.all_factors && (
            <div className="pt-2 border-t border-slate-100">
              <button
                onClick={() => setShowAllFactors(!showAllFactors)}
                className="w-full flex items-center justify-between text-xs font-bold text-slate-600 hover:text-violet-700 py-2 transition-colors"
              >
                <span>Complete 13-Feature Decomposition</span>
                {showAllFactors ? (
                  <ChevronUp className="w-4 h-4 text-slate-400" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-slate-400" />
                )}
              </button>

              {showAllFactors && (
                <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-[#FAF9FF] text-slate-600 font-bold border-b border-slate-200">
                      <tr>
                        <th className="p-2.5">Feature</th>
                        <th className="p-2.5">Observed Value</th>
                        <th className="p-2.5 text-right">Contribution</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 font-medium">
                      {expl.all_factors.map((f, i) => (
                        <tr key={i} className="hover:bg-slate-50">
                          <td className="p-2.5 capitalize text-slate-700">
                            {f.factor.replace(/_/g, ' ')}
                          </td>
                          <td className="p-2.5 text-slate-600 font-mono">
                            {f.value}
                          </td>
                          <td className="p-2.5 text-right font-mono font-bold">
                            <span className={
                              f.contribution > 0 ? 'text-rose-600' :
                              f.contribution < 0 ? 'text-emerald-600' : 'text-slate-400'
                            }>
                              {f.contribution > 0 ? `+${f.contribution.toFixed(4)}` : f.contribution.toFixed(4)}
                            </span>
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

        {/* Footer */}
        <div className="p-4 bg-[#FAF9FF] border-t border-[#EDE9FE] flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2.5 bg-violet-600 hover:bg-violet-700 text-white rounded-xl text-xs font-bold shadow-soft transition-all"
          >
            Close Explanation
          </button>
        </div>
      </div>
    </div>
  );
}
