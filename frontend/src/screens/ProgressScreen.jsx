import React from 'react';
import { 
  TrendingUp, 
  Award, 
  Clock, 
  BookOpen, 
  CheckCircle2, 
  Flame,
  Brain,
  ShieldCheck
} from 'lucide-react';

export default function ProgressScreen({ dashboardData, courses, user }) {
  const topics = dashboardData?.topics || [];
  const highRisk = topics.filter((t) => t.retention_status === 'high_risk');
  const modRisk = topics.filter((t) => t.retention_status === 'moderate_risk');
  const retained = topics.filter((t) => t.retention_status === 'retained');

  const totalStudied = topics.length;
  const overallScorePct = dashboardData 
    ? Math.round(dashboardData.overall_retention_score * 100) 
    : 100;

  const highPct = totalStudied ? Math.round((highRisk.length / totalStudied) * 100) : 0;
  const modPct = totalStudied ? Math.round((modRisk.length / totalStudied) * 100) : 0;
  const retPct = totalStudied ? Math.round((retained.length / totalStudied) * 100) : 0;

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-black text-[#1E1B4B] tracking-tight">
          Learning Progress & Retention Analytics
        </h2>
        <p className="text-xs text-slate-500 font-medium">
          Comprehensive longitudinal tracking of cognitive memory consolidation across courses
        </p>
      </div>

      {/* Top Banner Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="p-6 rounded-3xl bg-white border border-[#EDE9FE] shadow-card flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-violet-50 text-violet-600 flex items-center justify-center border border-violet-100 shrink-0">
            <Brain className="w-7 h-7" />
          </div>
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Concepts Studied
            </div>
            <div className="text-3xl font-black text-[#1E1B4B]">
              {totalStudied}
            </div>
            <div className="text-[11px] text-slate-500 font-semibold mt-0.5">
              Active in memory model
            </div>
          </div>
        </div>

        <div className="p-6 rounded-3xl bg-white border border-[#EDE9FE] shadow-card flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100 shrink-0">
            <TrendingUp className="w-7 h-7" />
          </div>
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Overall Retention
            </div>
            <div className="text-3xl font-black text-emerald-600">
              {overallScorePct}%
            </div>
            <div className="text-[11px] text-slate-500 font-semibold mt-0.5">
              Average across all studied topics
            </div>
          </div>
        </div>

        <div className="p-6 rounded-3xl bg-white border border-[#EDE9FE] shadow-card flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-purple-50 text-purple-600 flex items-center justify-center border border-purple-100 shrink-0">
            <Award className="w-7 h-7" />
          </div>
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Active Curriculum
            </div>
            <div className="text-3xl font-black text-purple-700">
              {courses.length}
            </div>
            <div className="text-[11px] text-slate-500 font-semibold mt-0.5">
              Accredited courses tracked
            </div>
          </div>
        </div>
      </div>

      {/* Retention Distribution Bar */}
      <div className="p-6 rounded-3xl bg-white border border-[#EDE9FE] shadow-card space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-extrabold text-[#1E1B4B]">
            Portfolio Retention Status Distribution
          </h3>
          <span className="text-xs font-bold text-slate-400">{totalStudied} total concepts</span>
        </div>

        {/* Stacked bar */}
        <div className="w-full h-4 rounded-full bg-slate-100 overflow-hidden flex">
          <div 
            style={{ width: `${retPct}%` }} 
            className="bg-emerald-500 h-full transition-all duration-500" 
            title={`Retained: ${retained.length} (${retPct}%)`}
          />
          <div 
            style={{ width: `${modPct}%` }} 
            className="bg-amber-400 h-full transition-all duration-500" 
            title={`Moderate Risk: ${modRisk.length} (${modPct}%)`}
          />
          <div 
            style={{ width: `${highPct}%` }} 
            className="bg-rose-500 h-full transition-all duration-500" 
            title={`High Risk: ${highRisk.length} (${highPct}%)`}
          />
        </div>

        <div className="grid grid-cols-3 gap-4 pt-2">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-emerald-500 shrink-0" />
            <div>
              <span className="text-xs font-bold text-slate-700">Retained: {retained.length}</span>
              <span className="text-xs text-slate-400 ml-1.5">({retPct}%)</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-amber-400 shrink-0" />
            <div>
              <span className="text-xs font-bold text-slate-700">Moderate Risk: {modRisk.length}</span>
              <span className="text-xs text-slate-400 ml-1.5">({modPct}%)</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-rose-500 shrink-0" />
            <div>
              <span className="text-xs font-bold text-slate-700">High Risk: {highRisk.length}</span>
              <span className="text-xs text-slate-400 ml-1.5">({highPct}%)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Course Breakdown */}
      <div className="space-y-4">
        <h3 className="text-base font-extrabold text-[#1E1B4B]">
          Course-Level Curriculum Health
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {courses.map((course) => (
            <div
              key={course.id}
              className="p-5 rounded-2xl bg-white border border-[#EDE9FE] shadow-card space-y-3"
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-black uppercase text-violet-600 bg-violet-50 px-2.5 py-1 rounded-lg">
                  Course #{course.id}
                </span>
                <span className="text-xs font-bold text-emerald-600 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Monitoring Active
                </span>
              </div>
              <h4 className="text-sm font-extrabold text-[#1E1B4B]">
                {course.name}
              </h4>
              <p className="text-xs text-slate-500 font-medium">
                Cognitive spaced repetition model actively schedules reminders for all topics in this course syllabus.
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
