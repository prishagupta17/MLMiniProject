import React, { useState, useEffect } from 'react';
import { X, Clock, Award, CheckCircle2, AlertCircle, Sparkles, History } from 'lucide-react';
import { api } from '../api';

export default function LogStudyModal({ 
  user, 
  topics = [], 
  preselectedTopicId = null, 
  dashboardData = null,
  onClose, 
  onSuccess 
}) {
  const [topicId, setTopicId] = useState(preselectedTopicId || (topics[0]?.id || ''));
  const [minutes, setMinutes] = useState(30);
  const [confidence, setConfidence] = useState(0.7);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [lastSavedInfo, setLastSavedInfo] = useState(null);

  // Helper to load previous values for a given topic
  const loadSavedTopicValues = (tId) => {
    if (!tId || !user) return;
    const key = `study_session_${user.id}_${tId}`;
    const saved = localStorage.getItem(key);

    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed.minutes) setMinutes(parsed.minutes);
        if (parsed.confidence !== undefined) setConfidence(parsed.confidence);
        setLastSavedInfo(parsed);
        return;
      } catch (_) {}
    }

    // Fallback: check dashboardData raw_features
    if (dashboardData?.topics) {
      const match = dashboardData.topics.find((t) => t.topic_id === parseInt(tId, 10));
      if (match?.raw_features) {
        const prevMins = Math.round(match.raw_features.time_spent_studying_min) || 30;
        const prevConf = match.raw_features.self_reported_confidence ?? 0.7;
        setMinutes(prevMins);
        setConfidence(prevConf);
        setLastSavedInfo({ minutes: prevMins, confidence: prevConf });
        return;
      }
    }

    // Default if never studied
    setMinutes(30);
    setConfidence(0.7);
    setLastSavedInfo(null);
  };

  // Sync state when preselectedTopicId or modal opens
  useEffect(() => {
    const activeId = preselectedTopicId || topicId || (topics[0]?.id || '');
    if (activeId) {
      setTopicId(activeId);
      loadSavedTopicValues(activeId);
    }
  }, [preselectedTopicId]);

  // When student switches topic from the dropdown inside the modal
  const handleTopicChange = (newTopicId) => {
    setTopicId(newTopicId);
    loadSavedTopicValues(newTopicId);
  };

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

      // Persist the user's customized study settings for this topic so it's remembered
      const key = `study_session_${user.id}_${topicId}`;
      localStorage.setItem(key, JSON.stringify({ minutes, confidence }));

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
              <p className="text-xs text-slate-500">Record revision time & confidence</p>
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
              onChange={(e) => handleTopicChange(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-[#F8F9FE] border border-slate-200 rounded-xl text-xs font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-violet-500"
              required
            >
              {topics.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.module_name ? `[${t.module_name}] ` : ''}{t.name}
                </option>
              ))}
            </select>

            {/* Remembered Info Pill */}
            {lastSavedInfo && (
              <div className="mt-2 px-3 py-1.5 rounded-xl bg-violet-50/70 border border-violet-100 flex items-center gap-2 text-[11px] text-violet-800 font-medium">
                <History className="w-3.5 h-3.5 text-violet-600 shrink-0" />
                <span>
                  Previous study: <strong>{lastSavedInfo.minutes} mins</strong> • <strong>{Math.round(lastSavedInfo.confidence * 100)}% confidence</strong>
                </span>
              </div>
            )}
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
                      ? 'bg-violet-600 text-white border-violet-600 shadow-sm'
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
