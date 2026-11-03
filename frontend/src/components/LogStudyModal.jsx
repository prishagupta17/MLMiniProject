import React, { useState } from 'react';
import { X, Clock, Award, CheckCircle2, AlertCircle } from 'lucide-react';
import { api } from '../api';

export default function LogStudyModal({ 
  user, 
  topics = [], 
  preselectedTopicId = null, 
  onClose, 
  onSuccess 
}) {
  const [topicId, setTopicId] = useState(preselectedTopicId || (topics[0]?.id || ''));
  const [minutes, setMinutes] = useState(30);
  const [confidence, setConfidence] = useState(0.7);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!topicId || !user) return;
    setSubmitting(true);
    setError(null);

    try {
      await api.logLearningEvent(
        user.id,
        parseInt(topicId, 10),
        minutes * 60,
        parseFloat(confidence)
      );
      onSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to log study session.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-md w-full shadow-2xl border border-[#EDE9FE] overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-6 bg-gradient-to-r from-violet-50 to-[#FAF9FF] border-b border-[#EDE9FE] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-violet-600 text-white flex items-center justify-center shadow-soft">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-extrabold text-[#1E1B4B]">Log Study Session</h2>
              <p className="text-xs text-slate-500">Record revision time & self-confidence</p>
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
              Topic
            </label>
            <select
              value={topicId}
              onChange={(e) => setTopicId(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-[#F8F9FE] border border-slate-200 rounded-xl text-xs font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-violet-500"
              required
            >
              {topics.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.module_name ? `[${t.module_name}] ` : ''}{t.name}
                </option>
              ))}
            </select>
          </div>

          {/* Study Duration */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Time Spent (Minutes)
              </label>
              <span className="text-xs font-black text-violet-700">{minutes} min</span>
            </div>
            <div className="flex items-center gap-2 mb-2">
              {[15, 30, 45, 60].map((preset) => (
                <button
                  type="button"
                  key={preset}
                  onClick={() => setMinutes(preset)}
                  className={`flex-1 py-1.5 rounded-lg text-xs font-bold border transition-all ${
                    minutes === preset
                      ? 'bg-violet-600 text-white border-violet-600'
                      : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  {preset}m
                </button>
              ))}
            </div>
            <input
              type="range"
              min="5"
              max="180"
              step="5"
              value={minutes}
              onChange={(e) => setMinutes(parseInt(e.target.value, 10))}
              className="w-full accent-violet-600 cursor-pointer"
            />
          </div>

          {/* Confidence Rating */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Self-Reported Confidence
              </label>
              <span className="text-xs font-black text-violet-700">
                {Math.round(confidence * 100)}%
              </span>
            </div>
            <input
              type="range"
              min="0.1"
              max="1.0"
              step="0.05"
              value={confidence}
              onChange={(e) => setConfidence(parseFloat(e.target.value))}
              className="w-full accent-violet-600 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-400 mt-1 font-medium">
              <span>Low (Needs review)</span>
              <span>Medium</span>
              <span>High (Mastered)</span>
            </div>
          </div>

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
              className="px-5 py-2.5 bg-violet-600 hover:bg-violet-700 text-white rounded-xl text-xs font-bold shadow-soft transition-all disabled:opacity-50"
            >
              {submitting ? 'Saving...' : 'Save Study Event'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
