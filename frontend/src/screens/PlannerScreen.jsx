import React from 'react';
import { 
  Calendar, 
  Clock, 
  AlertCircle, 
  CheckCircle2, 
  ArrowRight,
  Flame,
  HelpCircle,
  Sparkles,
  BookOpen
} from 'lucide-react';

export default function PlannerScreen({ 
  dashboardData, 
  onOpenStudyModal, 
  onOpenSelfCheckModal,
  onOpenExplanation 
}) {
  const topics = dashboardData?.topics || [];
  const highRisk = topics.filter((t) => t.retention_status === 'high_risk');
  const modRisk = topics.filter((t) => t.retention_status === 'moderate_risk');
  const retained = topics.filter((t) => t.retention_status === 'retained');

  // Estimate total recommended revision time: 30 min per high risk, 15 min per moderate risk
  const estTotalMins = (highRisk.length * 30) + (modRisk.length * 15);
  const estHours = (estTotalMins / 60).toFixed(1);

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-[#1E1B4B] tracking-tight">
            Personalized Study Planner & Schedule
          </h2>
          <p className="text-xs text-slate-500 font-medium">
            Cognitive spaced repetition schedule prioritizing decay risk and assessment alignment
          </p>
        </div>
      </div>

      {/* Schedule Summary Banner */}
      <div className="p-6 rounded-3xl bg-white border border-[#EDE9FE] shadow-card flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-violet-50 text-violet-600 flex items-center justify-center border border-violet-100 shrink-0">
            <Calendar className="w-7 h-7" />
          </div>
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Recommended Revision Backlog
            </div>
            <div className="text-xl font-extrabold text-[#1E1B4B] mt-0.5">
              {highRisk.length + modRisk.length} concepts need review
            </div>
            <p className="text-xs text-slate-500 font-medium mt-0.5">
              Estimated study time needed to restore baseline retention: <span className="font-bold text-violet-700">{estHours} hours</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-4 py-2 rounded-2xl bg-rose-50 border border-rose-200 text-center">
            <div className="text-lg font-black text-rose-700">{highRisk.length}</div>
            <div className="text-[10px] font-bold uppercase text-rose-600">Urgent Today</div>
          </div>
          <div className="px-4 py-2 rounded-2xl bg-amber-50 border border-amber-200 text-center">
            <div className="text-lg font-black text-amber-700">{modRisk.length}</div>
            <div className="text-[10px] font-bold uppercase text-amber-600">This Week</div>
          </div>
          <div className="px-4 py-2 rounded-2xl bg-emerald-50 border border-emerald-200 text-center">
            <div className="text-lg font-black text-emerald-700">{retained.length}</div>
            <div className="text-[10px] font-bold uppercase text-emerald-600">Stable</div>
          </div>
        </div>
      </div>

      {/* Section 1: Urgent Revisions (Today) */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center">
            <Flame className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-base font-extrabold text-[#1E1B4B]">
              Immediate Priority: Review Today (High Risk ≥ 60%)
            </h3>
            <p className="text-xs text-slate-500 font-medium">
              These topics have the steepest cognitive decay and require retrieval practice immediately.
            </p>
          </div>
        </div>

        {highRisk.length === 0 ? (
          <div className="p-6 rounded-2xl bg-white border border-[#EDE9FE] text-center text-xs text-slate-500 font-medium">
            🎉 Great job! No topics currently in the High Risk threshold.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {highRisk.map((topic) => (
              <div
                key={topic.topic_id}
                className="p-5 rounded-2xl bg-white border border-rose-100 shadow-card hover:shadow-hover transition-all flex flex-col justify-between gap-4"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[11px] font-bold px-2 py-0.5 rounded-md bg-rose-50 text-rose-700 border border-rose-200">
                      {Math.round(topic.forgetting_probability * 100)}% Risk
                    </span>
                    <span className="text-xs text-slate-400 font-medium truncate max-w-[150px]">
                      {topic.module_name}
                    </span>
                  </div>
                  <h4 className="text-sm font-extrabold text-[#1E1B4B] leading-snug">
                    {topic.topic_name}
                  </h4>
                  {topic.local_explanation?.summary && (
                    <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                      {topic.local_explanation.summary}
                    </p>
                  )}
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                  <button
                    onClick={() => onOpenExplanation(topic)}
                    className="text-xs font-bold text-violet-600 hover:text-violet-800 flex items-center gap-1"
                  >
                    <HelpCircle className="w-3.5 h-3.5" />
                    Why?
                  </button>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => onOpenStudyModal(topic.topic_id)}
                      className="px-3 py-1.5 bg-violet-600 hover:bg-violet-700 text-white rounded-xl text-xs font-bold transition-all shadow-soft"
                    >
                      Study (30m)
                    </button>
                    <button
                      onClick={() => onOpenSelfCheckModal(topic.topic_id)}
                      className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition-all shadow-soft"
                    >
                      Test
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Section 2: Secondary Priority (Next 48 Hours) */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
            <Clock className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-base font-extrabold text-[#1E1B4B]">
              Secondary Priority: Review Soon (Moderate Risk 35% – 60%)
            </h3>
            <p className="text-xs text-slate-500 font-medium">
              Memory retention is declining; schedule a short revision session before retention drops below 50%.
            </p>
          </div>
        </div>

        {modRisk.length === 0 ? (
          <div className="p-6 rounded-2xl bg-white border border-[#EDE9FE] text-center text-xs text-slate-500 font-medium">
            No moderate risk topics.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {modRisk.map((topic) => (
              <div
                key={topic.topic_id}
                className="p-5 rounded-2xl bg-white border border-amber-100 shadow-card hover:shadow-hover transition-all flex flex-col justify-between gap-4"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[11px] font-bold px-2 py-0.5 rounded-md bg-amber-50 text-amber-700 border border-amber-200">
                      {Math.round(topic.forgetting_probability * 100)}% Risk
                    </span>
                    <span className="text-xs text-slate-400 font-medium truncate max-w-[150px]">
                      {topic.module_name}
                    </span>
                  </div>
                  <h4 className="text-sm font-extrabold text-[#1E1B4B] leading-snug">
                    {topic.topic_name}
                  </h4>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                  <button
                    onClick={() => onOpenExplanation(topic)}
                    className="text-xs font-bold text-violet-600 hover:text-violet-800 flex items-center gap-1"
                  >
                    <HelpCircle className="w-3.5 h-3.5" />
                    Why?
                  </button>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => onOpenStudyModal(topic.topic_id)}
                      className="px-3 py-1.5 bg-violet-600 hover:bg-violet-700 text-white rounded-xl text-xs font-bold transition-all shadow-soft"
                    >
                      Study (15m)
                    </button>
                    <button
                      onClick={() => onOpenSelfCheckModal(topic.topic_id)}
                      className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition-all shadow-soft"
                    >
                      Test
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
