import React from 'react';
import { 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  BookOpen, 
  ArrowRight, 
  Sparkles,
  HelpCircle,
  TrendingDown,
  ShieldAlert,
  ChevronRight,
  Flame,
  GraduationCap
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
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
        <div className="w-10 h-10 border-4 border-violet-200 border-t-violet-600 rounded-full animate-spin" />
        <p className="text-xs font-semibold text-slate-500">Calculating cognitive retention scores...</p>
      </div>
    );
  }

  const topics = dashboardData?.topics || [];
  const highRiskTopics = topics.filter((t) => t.retention_status === 'high_risk');
  const modRiskTopics = topics.filter((t) => t.retention_status === 'moderate_risk');
  const retainedTopics = topics.filter((t) => t.retention_status === 'retained');

  // Top 5 topics to revise (already sorted by forgetting_probability descending from dashboard API)
  const top5Revise = topics.slice(0, 5);

  const overallRetentionPct = dashboardData 
    ? Math.round(dashboardData.overall_retention_score * 100) 
    : 100;

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Welcome Banner */}
      <div className="p-8 rounded-3xl bg-gradient-to-r from-violet-600 via-indigo-600 to-purple-700 text-white shadow-soft relative overflow-hidden">
        <div className="relative z-10 max-w-xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/20 backdrop-blur-md text-xs font-bold mb-3 tracking-wide">
            <Sparkles className="w-3.5 h-3.5" />
            AI Forgetting Prediction Engine
          </div>
          <h2 className="text-2xl font-black tracking-tight mb-2">
            Targeted Cognitive Retention Dashboard
          </h2>
          <p className="text-sm text-violet-100 leading-relaxed font-medium">
            Personalized recall decay estimates generated from your study frequency, elapsed days, and curriculum load.
          </p>
        </div>
        {/* Subtle decorative elements */}
        <div className="absolute right-0 top-0 bottom-0 w-80 bg-white/5 rounded-l-full pointer-events-none" />
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        {/* Overall Retention Score */}
        <div className="p-6 rounded-3xl bg-white border border-[#EDE9FE] shadow-card flex items-center justify-between">
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">
              Retention Score
            </div>
            <div className="text-3xl font-black text-[#1E1B4B]">
              {overallRetentionPct}%
            </div>
            <div className="text-[11px] text-slate-500 font-semibold mt-1 flex items-center gap-1">
              <span className={overallRetentionPct >= 70 ? 'text-emerald-600' : 'text-amber-600'}>
                {overallRetentionPct >= 70 ? 'Strong baseline' : 'Needs attention'}
              </span>
              <span>across studied concepts</span>
            </div>
          </div>
          <div className="w-14 h-14 rounded-2xl bg-violet-50 text-violet-600 flex items-center justify-center font-black text-xl border border-violet-100">
            {overallRetentionPct}%
          </div>
        </div>

        {/* High Risk Topics */}
        <div className="p-6 rounded-3xl bg-white border border-[#EDE9FE] shadow-card flex items-center justify-between">
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">
              High Risk (≥ 60%)
            </div>
            <div className="text-3xl font-black text-rose-600">
              {highRiskTopics.length}
            </div>
            <div className="text-[11px] text-slate-500 font-semibold mt-1">
              Critical priority for revision
            </div>
          </div>
          <div className="w-14 h-14 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center border border-rose-100">
            <ShieldAlert className="w-7 h-7" />
          </div>
        </div>

        {/* Moderate Risk Topics */}
        <div className="p-6 rounded-3xl bg-white border border-[#EDE9FE] shadow-card flex items-center justify-between">
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">
              Moderate Risk (35-60%)
            </div>
            <div className="text-3xl font-black text-amber-600">
              {modRiskTopics.length}
            </div>
            <div className="text-[11px] text-slate-500 font-semibold mt-1">
              Review within 2-3 days
            </div>
          </div>
          <div className="w-14 h-14 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center border border-amber-100">
            <Clock className="w-7 h-7" />
          </div>
        </div>

        {/* Retained Topics */}
        <div className="p-6 rounded-3xl bg-white border border-[#EDE9FE] shadow-card flex items-center justify-between">
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">
              Retained (&lt; 35%)
            </div>
            <div className="text-3xl font-black text-emerald-600">
              {retainedTopics.length}
            </div>
            <div className="text-[11px] text-slate-500 font-semibold mt-1">
              Memory consolidated
            </div>
          </div>
          <div className="w-14 h-14 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100">
            <CheckCircle2 className="w-7 h-7" />
          </div>
        </div>
      </div>

      {/* Main Grid: Top 5 Urgent Revisions + Course Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column (2 spans): Top 5 Topics to Revise */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center">
                <Flame className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-extrabold text-[#1E1B4B]">
                  Top 5 Urgent Revisions
                </h3>
                <p className="text-xs text-slate-500 font-medium">
                  Ranked by predicted forgetting probability
                </p>
              </div>
            </div>
            <span className="text-xs font-bold text-slate-400">
              Showing 5 of {topics.length} studied concepts
            </span>
          </div>

          {top5Revise.length === 0 ? (
            <div className="p-8 rounded-3xl bg-white border border-[#EDE9FE] text-center space-y-3">
              <GraduationCap className="w-10 h-10 text-slate-300 mx-auto" />
              <p className="text-sm font-bold text-slate-700">No studied topics recorded yet</p>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Log a study session for any topic in the curriculum to activate the personalized forgetting engine.
              </p>
              <button
                onClick={() => onOpenStudyModal()}
                className="px-4 py-2 bg-violet-600 text-white rounded-xl text-xs font-bold hover:bg-violet-700 transition-all shadow-soft"
              >
                Log First Study Session
              </button>
            </div>
          ) : (
            <div className="space-y-3.5">
              {top5Revise.map((topic, index) => {
                const probPct = (topic.forgetting_probability * 100).toFixed(1);
                const isHigh = topic.retention_status === 'high_risk';

                return (
                  <div
                    key={topic.topic_id}
                    className="p-5 rounded-2xl bg-white border border-[#EDE9FE] shadow-card hover:shadow-hover transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 group"
                  >
                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[11px] font-bold px-2 py-0.5 rounded-md bg-violet-50 text-violet-700">
                          #{index + 1} Priority
                        </span>
                        <span className="text-xs text-slate-400 font-medium truncate max-w-[200px]">
                          {topic.module_name}
                        </span>
                        <span className={
                          isHigh 
                            ? 'text-[11px] font-bold px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200'
                            : 'text-[11px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200'
                        }>
                          {isHigh ? 'High Risk' : 'Moderate Risk'}
                        </span>
                      </div>
                      <h4 className="text-sm font-extrabold text-[#1E1B4B] group-hover:text-violet-700 transition-colors">
                        {topic.topic_name}
                      </h4>
                      {topic.local_explanation?.summary && (
                        <p className="text-xs text-slate-500 line-clamp-1 font-medium">
                          {topic.local_explanation.summary}
                        </p>
                      )}
                    </div>

                    {/* Risk Stat & Actions */}
                    <div className="flex items-center gap-4 shrink-0 sm:border-l sm:border-slate-100 sm:pl-5">
                      <div className="text-right">
                        <div className="text-lg font-black text-rose-600">
                          {probPct}%
                        </div>
                        <div className="text-[10px] font-bold text-slate-400 uppercase">
                          Forgetting Risk
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {/* Why? Explanation trigger */}
                        <button
                          onClick={() => onOpenExplanation(topic)}
                          className="p-2 text-violet-600 hover:text-violet-800 bg-violet-50 hover:bg-violet-100 rounded-xl text-xs font-bold transition-all flex items-center gap-1"
                          title="View local topic-specific explainability decomposition"
                        >
                          <HelpCircle className="w-4 h-4" />
                          <span className="hidden sm:inline">Why?</span>
                        </button>

                        {/* Quick Study */}
                        <button
                          onClick={() => onOpenStudyModal(topic.topic_id)}
                          className="px-3 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-xl text-xs font-bold transition-all shadow-soft"
                          title="Log study session for this topic"
                        >
                          Study
                        </button>

                        {/* Quick Self-Check */}
                        <button
                          onClick={() => onOpenSelfCheckModal(topic.topic_id)}
                          className="px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition-all shadow-soft"
                          title="Submit a recall test check"
                        >
                          Test
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Course Overview */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-xl bg-violet-50 text-violet-600 flex items-center justify-center">
                <BookOpen className="w-5 h-5" />
              </div>
              <h3 className="text-base font-extrabold text-[#1E1B4B]">
                Curriculum Overview
              </h3>
            </div>
            <span className="text-xs font-bold text-slate-400">4 Courses</span>
          </div>

          <div className="space-y-3.5">
            {courses.map((course) => {
              // Count studied topics for this course from dashboardData
              // (match via course modules or topic names)
              return (
                <div
                  key={course.id}
                  className="p-5 rounded-2xl bg-white border border-[#EDE9FE] shadow-card hover:shadow-hover transition-all"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[11px] font-black uppercase tracking-wider text-violet-600">
                      Course #{course.id}
                    </span>
                    <span className="text-xs text-slate-400 font-semibold">Active</span>
                  </div>
                  <h4 className="text-sm font-extrabold text-[#1E1B4B] mb-2 leading-snug">
                    {course.name}
                  </h4>
                  <div className="flex items-center justify-between text-xs text-slate-500 font-medium pt-2 border-t border-slate-100">
                    <span>Curriculum coverage</span>
                    <span className="font-bold text-slate-700">Enrolled</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
