import React from 'react';
import { 
  Sparkles,
  CheckCircle2, 
  Clock, 
  ArrowRight, 
  BookOpen, 
  HelpCircle,
  Play,
  RotateCcw,
  Zap,
  Target,
  Smile,
  ShieldCheck
} from 'lucide-react';

export default function DashboardScreen({ 
  dashboardData, 
  courses, 
  loading, 
  user,
  onOpenStudyModal, 
  onOpenSelfCheckModal,
  onOpenExplanation 
}) {
  if (loading && !dashboardData) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] gap-3">
        <div className="w-9 h-9 border-3 border-violet-200 border-t-violet-600 rounded-full animate-spin" />
        <p className="text-xs font-medium text-slate-400">Preparing your personalized study flow...</p>
      </div>
    );
  }

  const topics = dashboardData?.topics || [];
  const urgentTopics = topics.filter((t) => t.retention_status === 'high_risk');
  const moderateTopics = topics.filter((t) => t.retention_status === 'moderate_risk');
  const retainedTopics = topics.filter((t) => t.retention_status === 'retained');

  // The single top focus topic for the student right now
  const focusTopic = topics[0] || null;
  // Up to 3 next recommendations (bite-sized, not overwhelming)
  const upNextTopics = topics.slice(1, 4);

  const firstName = user?.name ? user.name.split('_')[0] : 'Learner';

  return (
    <div className="space-y-8 max-w-5xl mx-auto animate-in fade-in duration-200">
      
      {/* 1. Calm, Friendly Header Banner */}
      <div className="p-7 rounded-3xl bg-white border border-[#EDE9FE] shadow-card flex flex-col md:flex-row md:items-center justify-between gap-6 relative overflow-hidden">
        <div className="space-y-2 z-10">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-violet-50 text-violet-700 text-xs font-bold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Today's Memory Plan</span>
          </div>
          <h2 className="text-2xl font-black text-[#1E1B4B] tracking-tight">
            Hi, {firstName}! What are we revising today?
          </h2>
          <p className="text-xs text-slate-500 font-medium max-w-lg leading-relaxed">
            {urgentTopics.length > 0 
              ? `You have ${urgentTopics.length} topic${urgentTopics.length > 1 ? 's' : ''} ready for a quick refresher. Reviewing just one topic keeps your memory sharp!`
              : "All your studied topics are looking healthy and fresh! Feel free to explore new topics or do a quick self-check."}
          </p>
        </div>

        {/* Bite-sized summary pill */}
        <div className="flex items-center gap-3 shrink-0 z-10">
          <div className="px-4 py-3 rounded-2xl bg-[#FAF9FF] border border-[#EDE9FE] text-center min-w-[90px]">
            <div className="text-xl font-black text-violet-700">{urgentTopics.length}</div>
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Due Today</div>
          </div>
          <div className="px-4 py-3 rounded-2xl bg-[#FAF9FF] border border-[#EDE9FE] text-center min-w-[90px]">
            <div className="text-xl font-black text-amber-600">{moderateTopics.length}</div>
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Soon</div>
          </div>
          <div className="px-4 py-3 rounded-2xl bg-[#FAF9FF] border border-[#EDE9FE] text-center min-w-[90px]">
            <div className="text-xl font-black text-emerald-600">{retainedTopics.length}</div>
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Remembered</div>
          </div>
        </div>
      </div>

      {/* 2. "Focus on One Thing" Hero Card */}
      {focusTopic && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 px-1">
            <Target className="w-4 h-4 text-violet-600" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Recommended Right Now (Quick 15-Minute Win)
            </h3>
          </div>

          <div className="p-6 rounded-3xl bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-soft relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-2 z-10 max-w-xl">
              <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-lg bg-white/20 backdrop-blur-md text-[11px] font-bold text-violet-100">
                <span>{focusTopic.module_name}</span>
                <span>•</span>
                <span className="text-white">Refresher Recommended</span>
              </div>
              <h4 className="text-xl font-extrabold tracking-tight text-white">
                {focusTopic.topic_name}
              </h4>
              <p className="text-xs text-violet-100/90 leading-relaxed font-medium">
                {focusTopic.local_explanation?.summary || "A brief 15-minute review session today will lock this concept into long-term recall."}
              </p>
            </div>

            {/* Quick Actions on the Focus Card */}
            <div className="flex items-center gap-3 shrink-0 z-10 flex-wrap">
              <button
                onClick={() => onOpenExplanation(focusTopic)}
                className="px-4 py-2.5 rounded-xl bg-white/15 hover:bg-white/25 text-white text-xs font-bold transition-all flex items-center gap-1.5 backdrop-blur-md"
              >
                <HelpCircle className="w-4 h-4" />
                <span>Why this?</span>
              </button>

              <button
                onClick={() => onOpenStudyModal(focusTopic.topic_id)}
                className="px-5 py-2.5 rounded-xl bg-white text-violet-700 hover:bg-violet-50 text-xs font-extrabold shadow-sm transition-all flex items-center gap-1.5"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Start Review (15m)</span>
              </button>

              <button
                onClick={() => onOpenSelfCheckModal(focusTopic.topic_id)}
                className="px-4 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-extrabold transition-all flex items-center gap-1.5 shadow-sm"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>Quick Quiz</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 3. Up Next (Only 3 calm cards, not a huge overwhelming wall) */}
      {upNextTopics.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between px-1">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Up Next When You're Ready
            </h3>
            <span className="text-xs text-slate-400 font-medium">
              Take it one topic at a time
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {upNextTopics.map((topic, i) => (
              <div
                key={topic.topic_id}
                className="p-5 rounded-2xl bg-white border border-[#EDE9FE] shadow-card hover:border-violet-200 transition-all flex flex-col justify-between gap-4"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-violet-50 text-violet-700">
                      Step {i + 2}
                    </span>
                    <span className="text-[10px] font-bold text-slate-400 truncate max-w-[120px]">
                      {topic.module_name}
                    </span>
                  </div>
                  <h5 className="text-sm font-extrabold text-[#1E1B4B] leading-snug line-clamp-2">
                    {topic.topic_name}
                  </h5>
                </div>

                <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
                  <button
                    onClick={() => onOpenExplanation(topic)}
                    className="text-xs font-bold text-violet-600 hover:text-violet-800 flex items-center gap-1"
                  >
                    <HelpCircle className="w-3.5 h-3.5" />
                    <span>Why?</span>
                  </button>

                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => onOpenStudyModal(topic.topic_id)}
                      className="px-3 py-1.5 bg-violet-50 hover:bg-violet-100 text-violet-700 text-xs font-bold rounded-xl transition-all"
                    >
                      Review
                    </button>
                    <button
                      onClick={() => onOpenSelfCheckModal(topic.topic_id)}
                      className="px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 text-xs font-bold rounded-xl transition-all"
                    >
                      Quiz
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 4. Encouraging Habit Footer */}
      <div className="p-5 rounded-2xl bg-[#FAF9FF] border border-[#EDE9FE] flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-violet-100 text-violet-700 flex items-center justify-center shrink-0">
          <Smile className="w-5 h-5" />
        </div>
        <p className="text-xs text-slate-600 leading-relaxed font-medium">
          <span className="font-bold text-violet-900">Study Tip:</span> Short 10-15 minute retrieval sessions spaced a few days apart are 3x more effective than cramming for hours. Be kind to yourself and take breaks!
        </p>
      </div>

    </div>
  );
}
