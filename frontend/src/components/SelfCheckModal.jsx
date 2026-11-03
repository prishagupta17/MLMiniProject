import React, { useState } from 'react';
import { X, CheckCircle2, XCircle, AlertCircle, HelpCircle } from 'lucide-react';
import { api } from '../api';

export default function SelfCheckModal({ 
  user, 
  topics = [], 
  preselectedTopicId = null, 
  onClose, 
  onSuccess 
}) {
  const [topicId, setTopicId] = useState(preselectedTopicId || (topics[0]?.id || ''));
  const [isCorrect, setIsCorrect] = useState(true);
  const [prepForAssessment, setPrepForAssessment] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!topicId || !user) return;
    setSubmitting(true);
    setError(null);

    try {
      await api.logSelfCheckEvent(
        user.id,
        parseInt(topicId, 10),
        isCorrect,
        60, // 60 seconds standard recall check duration
        prepForAssessment
      );
      onSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to submit recall check.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-md w-full shadow-2xl border border-[#EDE9FE] overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-6 bg-gradient-to-r from-emerald-50 to-[#FAF9FF] border-b border-[#EDE9FE] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-emerald-600 text-white flex items-center justify-center shadow-soft">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-extrabold text-[#1E1B4B]">Recall Self-Check</h2>
              <p className="text-xs text-slate-500">Test memory retrieval on a topic</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 hover:bg-white rounded-full transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {error && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Topic Select */}
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5 uppercase tracking-wider">
              Topic Under Test
            </label>
            <select
              value={topicId}
              onChange={(e) => setTopicId(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-[#F8F9FE] border border-slate-200 rounded-xl text-xs font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              required
            >
              {topics.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.module_name ? `[${t.module_name}] ` : ''}{t.name}
                </option>
              ))}
            </select>
          </div>

          {/* Correct / Incorrect Toggle */}
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-2 uppercase tracking-wider">
              Recall Outcome
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setIsCorrect(true)}
                className={`p-3.5 rounded-2xl border flex flex-col items-center gap-1.5 transition-all ${
                  isCorrect
                    ? 'bg-emerald-50 border-emerald-500 text-emerald-800 shadow-soft font-bold'
                    : 'bg-white border-slate-200 text-slate-500 hover:bg-slate-50'
                }`}
              >
                <CheckCircle2 className={`w-6 h-6 ${isCorrect ? 'text-emerald-600' : 'text-slate-400'}`} />
                <span className="text-xs">Recalled Correctly</span>
              </button>

              <button
                type="button"
                onClick={() => setIsCorrect(false)}
                className={`p-3.5 rounded-2xl border flex flex-col items-center gap-1.5 transition-all ${
                  !isCorrect
                    ? 'bg-rose-50 border-rose-500 text-rose-800 shadow-soft font-bold'
                    : 'bg-white border-slate-200 text-slate-500 hover:bg-slate-50'
                }`}
              >
                <XCircle className={`w-6 h-6 ${!isCorrect ? 'text-rose-600' : 'text-slate-400'}`} />
                <span className="text-xs">Forgot / Incorrect</span>
              </button>
            </div>
          </div>

          {/* Upcoming Assessment Checkbox */}
          <div className="p-3.5 rounded-2xl bg-[#F8F9FE] border border-[#EDE9FE] flex items-center gap-3">
            <input
              type="checkbox"
              id="prepAssessment"
              checked={prepForAssessment}
              onChange={(e) => setPrepForAssessment(e.target.checked)}
              className="w-4 h-4 rounded text-emerald-600 accent-emerald-600 cursor-pointer"
            />
            <label htmlFor="prepAssessment" className="text-xs font-semibold text-slate-700 cursor-pointer">
              Preparing for upcoming exam or assessment
            </label>
          </div>

          <p className="text-[11px] text-slate-400 leading-relaxed italic">
            Note: Recall checks refine crowd difficulty and ground-truth validation; they are never fed back as input features into the forgetting model (zero leakage guarantee).
          </p>

          {/* Buttons */}
          <div className="pt-2 flex items-center justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl border border-slate-200 text-xs font-bold text-slate-600 hover:bg-slate-50 transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-soft transition-all disabled:opacity-50"
            >
              {submitting ? 'Submitting...' : 'Record Check'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
