import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import DashboardScreen from './screens/DashboardScreen';
import CoursesScreen from './screens/CoursesScreen';
import PlannerScreen from './screens/PlannerScreen';
import ProgressScreen from './screens/ProgressScreen';
import ExplanationModal from './components/ExplanationModal';
import LogStudyModal from './components/LogStudyModal';
import SelfCheckModal from './components/SelfCheckModal';
import NewStudentModal from './components/NewStudentModal';
import { api } from './api';
import { UserPlus, Brain, Sparkles, BookOpen } from 'lucide-react';

export default function App() {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [courses, setCourses] = useState([]);
  const [allTopics, setAllTopics] = useState([]);
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Quick initial student creation form state (if 0 users exist)
  const [initName, setInitName] = useState('');
  const [initEmail, setInitEmail] = useState('');
  const [initSubmitting, setInitSubmitting] = useState(false);

  // Modals state
  const [studyModalOpen, setStudyModalOpen] = useState(false);
  const [studyTopicId, setStudyTopicId] = useState(null);
  const [selfCheckModalOpen, setSelfCheckModalOpen] = useState(false);
  const [selfCheckTopicId, setSelfCheckTopicId] = useState(null);
  const [explanationData, setExplanationData] = useState(null);
  const [newUserModalOpen, setNewUserModalOpen] = useState(false);

  // 1. Initial Load: Users & Courses
  useEffect(() => {
    async function initApp() {
      try {
        setLoading(true);
        const [usersList, coursesList] = await Promise.all([
          api.getUsers(),
          api.getCourses(),
        ]);
        setUsers(usersList);
        setCourses(coursesList);

        if (usersList.length > 0) {
          setSelectedUser(usersList[0]);
        }

        // Fetch flat list of all topics across courses for modals
        const topicsAccum = [];
        for (const c of coursesList) {
          try {
            const mods = await api.getCourseModules(c.id);
            for (const m of mods) {
              const tops = await api.getModuleTopics(m.id);
              tops.forEach((t) => {
                topicsAccum.push({ ...t, module_name: m.name, course_name: c.name });
              });
            }
          } catch (_) {}
        }
        setAllTopics(topicsAccum);
      } catch (err) {
        console.error('Initialization error:', err);
        setError(err.message || 'Failed to connect to backend.');
      } finally {
        setLoading(false);
      }
    }
    initApp();
  }, []);

  // 2. Fetch Dashboard whenever selectedUser changes
  const fetchDashboard = useCallback(async () => {
    if (!selectedUser) {
      setDashboardData(null);
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const data = await api.getUserDashboard(selectedUser.id);
      setDashboardData(data);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
      setError(err.message || 'Failed to load student dashboard.');
    } finally {
      setLoading(false);
    }
  }, [selectedUser]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const [lastActiveTopicId, setLastActiveTopicId] = useState(null);

  // Modal Handlers
  const handleOpenStudy = (topicId = null) => {
    const targetId = topicId || lastActiveTopicId;
    setStudyTopicId(targetId);
    if (topicId) setLastActiveTopicId(topicId);
    setStudyModalOpen(true);
  };

  const handleOpenSelfCheck = (topicId = null) => {
    const targetId = topicId || lastActiveTopicId;
    setSelfCheckTopicId(targetId);
    if (topicId) setLastActiveTopicId(topicId);
    setSelfCheckModalOpen(true);
  };

  const handleOpenExplanation = (topicRisk) => {
    setExplanationData(topicRisk);
  };

  const handleNewUserCreated = (newUser) => {
    setUsers((prev) => [newUser, ...prev]);
    setSelectedUser(newUser);
  };

  // Quick initial student creation (onboarding)
  const handleInitialStudentSubmit = async (e) => {
    e.preventDefault();
    if (!initName.trim() || !initEmail.trim()) return;
    setInitSubmitting(true);
    try {
      const created = await api.createUser(initName.trim(), initEmail.trim());
      handleNewUserCreated(created);
    } catch (err) {
      setError(err.message || 'Failed to create student profile.');
    } finally {
      setInitSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8F9FE] flex">
      {/* Fixed Left Sidebar */}
      <Sidebar 
        currentTab={currentTab} 
        setCurrentTab={setCurrentTab} 
        user={selectedUser} 
      />

      {/* Main Content Area */}
      <div className="flex-1 ml-64 flex flex-col min-h-screen">
        {/* Sticky Top Navbar */}
        <Navbar
          users={users}
          selectedUser={selectedUser}
          onSelectUser={setSelectedUser}
          onOpenNewUser={() => setNewUserModalOpen(true)}
          onOpenStudyModal={() => handleOpenStudy()}
          onOpenSelfCheckModal={() => handleOpenSelfCheck()}
          onRefresh={fetchDashboard}
          loading={loading}
        />

        {/* Page Content */}
        <main className="flex-1 p-8 max-w-7xl w-full mx-auto">
          {error && (
            <div className="mb-6 p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold flex items-center justify-between">
              <span>{error}</span>
              <button 
                onClick={fetchDashboard}
                className="px-3 py-1 bg-white border border-rose-300 rounded-lg text-rose-800 font-bold hover:bg-rose-100"
              >
                Retry
              </button>
            </div>
          )}

          {/* Onboarding View: If 0 students exist in database */}
          {!loading && users.length === 0 ? (
            <div className="max-w-md mx-auto my-12 p-8 rounded-3xl bg-white border border-[#EDE9FE] shadow-card text-center space-y-6 animate-in fade-in">
              <div className="w-16 h-16 rounded-3xl bg-gradient-to-tr from-violet-600 to-indigo-500 text-white flex items-center justify-center mx-auto shadow-soft">
                <Brain className="w-8 h-8" />
              </div>
              <div className="space-y-2">
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-violet-50 text-violet-700 text-xs font-bold">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Welcome to The Forgetting Engine</span>
                </div>
                <h2 className="text-xl font-extrabold text-[#1E1B4B]">
                  Create Your Student Profile
                </h2>
                <p className="text-xs text-slate-500 leading-relaxed font-medium">
                  Add your student profile to start studying curriculum topics, testing your recall, and receiving personalized review schedules.
                </p>
              </div>

              <form onSubmit={handleInitialStudentSubmit} className="space-y-4 text-left">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5 uppercase tracking-wider">
                    Full Name
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Maya Patel"
                    value={initName}
                    onChange={(e) => setInitName(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-[#F8F9FE] border border-slate-200 rounded-xl text-xs font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-violet-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5 uppercase tracking-wider">
                    Email Address
                  </label>
                  <input
                    type="email"
                    placeholder="e.g. maya@university.edu"
                    value={initEmail}
                    onChange={(e) => setInitEmail(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-[#F8F9FE] border border-slate-200 rounded-xl text-xs font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-violet-500"
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={initSubmitting}
                  className="w-full py-3 bg-violet-600 hover:bg-violet-700 text-white font-extrabold text-xs rounded-xl shadow-soft transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  <UserPlus className="w-4 h-4" />
                  <span>{initSubmitting ? 'Creating Profile...' : 'Start Learning'}</span>
                </button>
              </form>
            </div>
          ) : (
            <>
              {currentTab === 'dashboard' && (
                <DashboardScreen
                  dashboardData={dashboardData}
                  courses={courses}
                  loading={loading}
                  user={selectedUser}
                  onOpenStudyModal={handleOpenStudy}
                  onOpenSelfCheckModal={handleOpenSelfCheck}
                  onOpenExplanation={handleOpenExplanation}
                  onNavigateCourses={() => setCurrentTab('courses')}
                />
              )}

              {currentTab === 'courses' && (
                <CoursesScreen
                  courses={courses}
                  dashboardData={dashboardData}
                  onOpenStudyModal={handleOpenStudy}
                  onOpenSelfCheckModal={handleOpenSelfCheck}
                  onOpenExplanation={handleOpenExplanation}
                />
              )}

              {currentTab === 'planner' && (
                <PlannerScreen
                  dashboardData={dashboardData}
                  onOpenStudyModal={handleOpenStudy}
                  onOpenSelfCheckModal={handleOpenSelfCheck}
                  onOpenExplanation={handleOpenExplanation}
                />
              )}

              {currentTab === 'progress' && (
                <ProgressScreen
                  dashboardData={dashboardData}
                  courses={courses}
                  user={selectedUser}
                />
              )}
            </>
          )}
        </main>
      </div>

      {/* Modals */}
      {explanationData && (
        <ExplanationModal
          topicRisk={explanationData}
          onClose={() => setExplanationData(null)}
        />
      )}

      {studyModalOpen && (
        <LogStudyModal
          user={selectedUser}
          topics={allTopics}
          preselectedTopicId={studyTopicId}
          dashboardData={dashboardData}
          onClose={() => setStudyModalOpen(false)}
          onSuccess={fetchDashboard}
        />
      )}

      {selfCheckModalOpen && (
        <SelfCheckModal
          user={selectedUser}
          topics={allTopics}
          preselectedTopicId={selfCheckTopicId}
          onClose={() => setSelfCheckModalOpen(false)}
          onSuccess={fetchDashboard}
        />
      )}

      {newUserModalOpen && (
        <NewStudentModal
          onClose={() => setNewUserModalOpen(false)}
          onCreated={handleNewUserCreated}
        />
      )}
    </div>
  );
}
