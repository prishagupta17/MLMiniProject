import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  ChevronRight, 
  ChevronDown, 
  HelpCircle, 
  Clock, 
  CheckCircle2, 
  Search,
  Sparkles,
  Layers,
  GraduationCap,
  Info
} from 'lucide-react';
import { api } from '../api';

export default function CoursesScreen({ 
  courses, 
  dashboardData, 
  onOpenStudyModal, 
  onOpenSelfCheckModal,
  onOpenExplanation 
}) {
  const [selectedCourseId, setSelectedCourseId] = useState(courses[0]?.id || 1);
  const [modules, setModules] = useState([]);
  const [topicsByModule, setTopicsByModule] = useState({});
  const [loadingModules, setLoadingModules] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterMode, setFilterMode] = useState('all'); // 'all' | 'due' | 'retained'
  const [expandedModules, setExpandedModules] = useState({});

  const studiedMap = React.useMemo(() => {
    const map = {};
    if (dashboardData?.topics) {
      dashboardData.topics.forEach((t) => {
        map[t.topic_id] = t;
      });
    }
    return map;
  }, [dashboardData]);

  useEffect(() => {
    let isMounted = true;
    async function loadCourseData() {
      if (!selectedCourseId) return;
      setLoadingModules(true);
      try {
        const mods = await api.getCourseModules(selectedCourseId);
        if (!isMounted) return;
        setModules(mods);

        // Keep current expanded state or expand all if first load
        setExpandedModules((prev) => {
          const exp = { ...prev };
          mods.forEach((m) => {
            if (exp[m.id] === undefined) exp[m.id] = true;
          });
          return exp;
        });

        const topicsPromises = mods.map(async (m) => {
          const tList = await api.getModuleTopics(m.id);
          return { moduleId: m.id, topics: tList };
        });
        const results = await Promise.all(topicsPromises);
        if (!isMounted) return;

        const tMap = {};
        results.forEach(({ moduleId, topics }) => {
          tMap[moduleId] = topics;
        });
        setTopicsByModule(tMap);
      } catch (err) {
        console.error('Failed to load course modules/topics:', err);
      } finally {
        if (isMounted) setLoadingModules(false);
      }
    }
    loadCourseData();
    return () => { isMounted = false; };
  }, [selectedCourseId]);

  const toggleModule = (modId) => {
    setExpandedModules((prev) => ({ ...prev, [modId]: !prev[modId] }));
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto animate-in fade-in duration-200">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-[#1E1B4B] tracking-tight">
            Curriculum & Topics
          </h2>
          <p className="text-xs text-slate-500 font-medium">
            Browse through your course topics and track retention progress
          </p>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Find a topic..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3.5 py-2 bg-white border border-[#EDE9FE] rounded-xl text-xs font-semibold text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500 shadow-card"
          />
        </div>
      </div>

      {/* Retention Criteria Explainer Banner */}
      <div className="p-4 rounded-2xl bg-[#FAF9FF] border border-[#EDE9FE] flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 text-slate-700 font-medium">
          <Info className="w-4 h-4 text-violet-600 shrink-0" />
          <span><strong>Retention Status Guide:</strong> How the model evaluates your recall:</span>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold text-[11px]" title="Forgetting probability under 35%">
            Remembered: &lt; 35% risk
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-amber-50 text-amber-800 border border-amber-200 font-bold text-[11px]" title="Forgetting probability between 35% and 60%">
            Review Soon: 35% – 60%
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-violet-100 text-violet-800 font-bold text-[11px]" title="Forgetting probability 60% or higher">
            Needs Refresher: ≥ 60%
          </span>
        </div>
      </div>

      {/* Course Tabs */}
      <div className="flex gap-2.5 overflow-x-auto pb-1 scrollbar-none">
        {courses.map((course) => {
          const isSelected = course.id === selectedCourseId;
          return (
            <button
              key={course.id}
              onClick={() => setSelectedCourseId(course.id)}
              className={`px-4 py-2.5 rounded-2xl text-xs font-bold transition-all shrink-0 flex items-center gap-2 ${
                isSelected
                  ? 'bg-violet-600 text-white shadow-soft font-extrabold'
                  : 'bg-white text-slate-600 border border-[#EDE9FE] hover:bg-slate-50'
              }`}
            >
              <BookOpen className={`w-3.5 h-3.5 ${isSelected ? 'text-white' : 'text-slate-400'}`} />
              <span className="truncate max-w-[200px]">{course.name}</span>
            </button>
          );
        })}
      </div>

      {/* Filter Mode Pills (All / Due for Review / Retained) */}
      <div className="flex items-center gap-2 text-xs font-bold">
        <span className="text-slate-400 mr-1 text-[11px] uppercase tracking-wider">Show:</span>
        {[
          { id: 'all', label: 'All Topics' },
          { id: 'due', label: 'Due for Review' },
          { id: 'retained', label: 'Remembered' }
        ].map((f) => (
          <button
            key={f.id}
            onClick={() => setFilterMode(f.id)}
            className={`px-3 py-1.5 rounded-xl transition-all ${
              filterMode === f.id
                ? 'bg-violet-100 text-violet-800 font-extrabold'
                : 'text-slate-500 hover:bg-white'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Modules List */}
      {loadingModules ? (
        <div className="p-12 text-center bg-white rounded-3xl border border-[#EDE9FE] shadow-card space-y-2">
          <div className="w-8 h-8 border-3 border-violet-200 border-t-violet-600 rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400 font-medium">Loading topics...</p>
        </div>
      ) : (
        <div className="space-y-4">
          {modules.map((mod) => {
            const allTopics = topicsByModule[mod.id] || [];
            
            const filteredTopics = allTopics.filter((t) => {
              if (searchQuery && !t.name.toLowerCase().includes(searchQuery.toLowerCase())) {
                return false;
              }
              const risk = studiedMap[t.id];
              if (filterMode === 'due') {
                return risk && (risk.retention_status === 'high_risk' || risk.retention_status === 'moderate_risk');
              }
              if (filterMode === 'retained') {
                return risk && risk.retention_status === 'retained';
              }
              return true;
            });

            if (filteredTopics.length === 0 && (searchQuery || filterMode !== 'all')) return null;

            const isExpanded = !!expandedModules[mod.id];

            return (
              <div
                key={mod.id}
                className="bg-white rounded-3xl border border-[#EDE9FE] shadow-card overflow-hidden"
              >
                {/* Module Bar */}
                <button
                  onClick={() => toggleModule(mod.id)}
                  className="w-full p-4 bg-[#FAF9FF] border-b border-[#EDE9FE] flex items-center justify-between text-left hover:bg-violet-50/40 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-7 h-7 rounded-xl bg-violet-100 text-violet-700 flex items-center justify-center font-bold text-xs">
                      {mod.order_index || mod.id}
                    </div>
                    <div>
                      <h3 className="text-sm font-extrabold text-[#1E1B4B]">
                        {mod.name}
                      </h3>
                      <p className="text-[11px] text-slate-400 font-medium">
                        {allTopics.length} topics
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-slate-400 font-bold">
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4" />
                    ) : (
                      <ChevronRight className="w-4 h-4" />
                    )}
                  </div>
                </button>

                {/* Topics in Module */}
                {isExpanded && (
                  <div className="p-3 divide-y divide-slate-100">
                    {filteredTopics.length === 0 ? (
                      <div className="p-4 text-center text-xs text-slate-400">
                        No topics match the current filter.
                      </div>
                    ) : (
                      filteredTopics.map((topic) => {
                        const riskInfo = studiedMap[topic.id];
                        const isStudied = !!riskInfo;
                        const riskPct = isStudied ? Math.round(riskInfo.forgetting_probability * 100) : null;

                        return (
                          <div
                            key={topic.id}
                            className="py-3 px-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-[#FAF9FF] rounded-xl transition-colors"
                          >
                            <div className="space-y-1 flex-1">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="font-extrabold text-xs text-[#1E1B4B]">
                                  {topic.name}
                                </span>
                                {isStudied ? (
                                  <span className={
                                    riskInfo.retention_status === 'high_risk'
                                      ? 'text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-violet-100 text-violet-800'
                                      : riskInfo.retention_status === 'moderate_risk'
                                      ? 'text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200'
                                      : 'text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200'
                                  }>
                                    {riskInfo.retention_status === 'high_risk' ? `Needs Refresher (${riskPct}%)` :
                                     riskInfo.retention_status === 'moderate_risk' ? `Review Soon (${riskPct}%)` : 
                                     `Remembered (${riskPct}%)`}
                                  </span>
                                ) : (
                                  <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-500">
                                    Not studied yet
                                  </span>
                                )}
                              </div>
                            </div>

                            {/* Actions */}
                            <div className="flex items-center gap-2 shrink-0">
                              <button
                                onClick={() => onOpenStudyModal(topic.id)}
                                className="px-3 py-1 bg-violet-50 hover:bg-violet-100 text-violet-700 rounded-lg text-xs font-bold transition-all"
                              >
                                Study
                              </button>

                              <button
                                onClick={() => onOpenSelfCheckModal(topic.id)}
                                className="px-3 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 rounded-lg text-xs font-bold transition-all"
                              >
                                Quiz
                              </button>
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
