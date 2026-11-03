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
  GraduationCap
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
  const [expandedModules, setExpandedModules] = useState({});

  // Map studied topic risk from dashboardData for quick O(1) lookup
  const studiedMap = React.useMemo(() => {
    const map = {};
    if (dashboardData?.topics) {
      dashboardData.topics.forEach((t) => {
        map[t.topic_id] = t;
      });
    }
    return map;
  }, [dashboardData]);

  // Load modules & topics when course tab changes
  useEffect(() => {
    let isMounted = true;
    async function loadCourseData() {
      if (!selectedCourseId) return;
      setLoadingModules(true);
      try {
        const mods = await api.getCourseModules(selectedCourseId);
        if (!isMounted) return;
        setModules(mods);

        // Auto-expand all modules initially
        const expMap = {};
        mods.forEach((m) => { expMap[m.id] = true; });
        setExpandedModules(expMap);

        // Load topics for each module in parallel
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

  const selectedCourse = courses.find((c) => c.id === selectedCourseId);

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-[#1E1B4B] tracking-tight">
            Curriculum & Forgetting Risk
          </h2>
          <p className="text-xs text-slate-500 font-medium">
            Explore syllabus modules and inspect personalized retention status for every concept
          </p>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search topic or concept..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-white border border-[#EDE9FE] rounded-xl text-xs font-semibold text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500 shadow-card"
          />
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
              className={`px-5 py-3 rounded-2xl text-xs font-bold transition-all shrink-0 flex items-center gap-2.5 ${
                isSelected
                  ? 'bg-violet-600 text-white shadow-soft font-extrabold'
                  : 'bg-white text-slate-600 border border-[#EDE9FE] hover:bg-slate-50 hover:text-violet-700'
              }`}
            >
              <BookOpen className={`w-4 h-4 ${isSelected ? 'text-white' : 'text-slate-400'}`} />
              <span className="truncate max-w-[220px]">{course.name}</span>
            </button>
          );
        })}
      </div>

      {/* Modules and Topics List */}
      {loadingModules ? (
        <div className="p-12 text-center bg-white rounded-3xl border border-[#EDE9FE] shadow-card space-y-3">
          <div className="w-8 h-8 border-4 border-violet-200 border-t-violet-600 rounded-full animate-spin mx-auto" />
          <p className="text-xs font-semibold text-slate-500">Loading module syllabus and risk estimates...</p>
        </div>
      ) : (
        <div className="space-y-4">
          {modules.map((mod) => {
            const allTopics = topicsByModule[mod.id] || [];
            const filteredTopics = searchQuery
              ? allTopics.filter((t) => t.name.toLowerCase().includes(searchQuery.toLowerCase()))
              : allTopics;

            if (searchQuery && filteredTopics.length === 0) return null;

            const isExpanded = !!expandedModules[mod.id];

            return (
              <div
                key={mod.id}
                className="bg-white rounded-3xl border border-[#EDE9FE] shadow-card overflow-hidden transition-all"
              >
                {/* Module Bar */}
                <button
                  onClick={() => toggleModule(mod.id)}
                  className="w-full p-5 bg-[#FAF9FF] border-b border-[#EDE9FE] flex items-center justify-between text-left hover:bg-violet-50/50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-xl bg-violet-100 text-violet-700 flex items-center justify-center font-black text-xs">
                      M{mod.order_index || mod.id}
                    </div>
                    <div>
                      <h3 className="text-sm font-extrabold text-[#1E1B4B]">
                        {mod.name}
                      </h3>
                      <p className="text-[11px] text-slate-500 font-medium">
                        {allTopics.length} topics in this module
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400 font-bold hidden sm:inline">
                      {isExpanded ? 'Collapse' : 'Expand'}
                    </span>
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-slate-400" />
                    )}
                  </div>
                </button>

                {/* Topics in Module */}
                {isExpanded && (
                  <div className="p-4 divide-y divide-slate-100">
                    {filteredTopics.length === 0 ? (
                      <div className="p-4 text-center text-xs text-slate-400">
                        No topics match your search query.
                      </div>
                    ) : (
                      filteredTopics.map((topic) => {
                        const riskInfo = studiedMap[topic.id];
                        const isStudied = !!riskInfo;
                        const probPct = isStudied 
                          ? (riskInfo.forgetting_probability * 100).toFixed(1) 
                          : null;

                        return (
                          <div
                            key={topic.id}
                            className="py-3.5 px-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-[#FAF9FF] rounded-2xl transition-colors"
                          >
                            <div className="space-y-1 flex-1">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="font-extrabold text-xs text-[#1E1B4B]">
                                  {topic.name}
                                </span>
                                {isStudied ? (
                                  <span className={
                                    riskInfo.retention_status === 'high_risk'
                                      ? 'text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200'
                                      : riskInfo.retention_status === 'moderate_risk'
                                      ? 'text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200'
                                      : 'text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200'
                                  }>
                                    {riskInfo.retention_status === 'high_risk' ? 'High Risk' :
                                     riskInfo.retention_status === 'moderate_risk' ? 'Moderate Risk' : 'Retained'}
                                  </span>
                                ) : (
                                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-500">
                                    Not studied yet
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center gap-3 text-[11px] text-slate-500 font-medium">
                                <span>Difficulty: {Math.round(topic.difficulty * 100)}%</span>
                                <span>•</span>
                                <span>Importance: {Math.round(topic.importance * 100)}%</span>
                                {topic.confusable_note && (
                                  <>
                                    <span>•</span>
                                    <span className="text-violet-600 truncate max-w-xs" title={topic.confusable_note}>
                                      Note: {topic.confusable_note}
                                    </span>
                                  </>
                                )}
                              </div>
                            </div>

                            {/* Risk badge & Action buttons */}
                            <div className="flex items-center gap-3 shrink-0">
                              {isStudied && (
                                <div className="text-right mr-1">
                                  <div className="text-sm font-black text-[#1E1B4B]">
                                    {probPct}%
                                  </div>
                                  <div className="text-[9px] uppercase font-bold text-slate-400">
                                    Risk
                                  </div>
                                </div>
                              )}

                              {isStudied && (
                                <button
                                  onClick={() => onOpenExplanation(riskInfo)}
                                  className="p-2 text-violet-600 hover:text-violet-800 bg-violet-50 hover:bg-violet-100 rounded-xl text-xs font-bold transition-all flex items-center gap-1"
                                  title="View model explainability"
                                >
                                  <HelpCircle className="w-4 h-4" />
                                  <span className="hidden sm:inline">Why?</span>
                                </button>
                              )}

                              <button
                                onClick={() => onOpenStudyModal(topic.id)}
                                className="px-3 py-1.5 bg-violet-600 hover:bg-violet-700 text-white rounded-xl text-xs font-bold transition-all shadow-soft"
                              >
                                Study
                              </button>

                              <button
                                onClick={() => onOpenSelfCheckModal(topic.id)}
                                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition-all shadow-soft"
                              >
                                Test
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
