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

export default function App() {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [courses, setCourses] = useState([]);
  const [allTopics, setAllTopics] = useState([]);
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

        // Default to first user (e.g. Student #1)
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
    if (!selectedUser) return;
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

  // Modal Triggers
  const handleOpenStudy = (topicId = null) => {
    setStudyTopicId(topicId);
    setStudyModalOpen(true);
  };

  const handleOpenSelfCheck = (topicId = null) => {
    setSelfCheckTopicId(topicId);
    setSelfCheckModalOpen(true);
  };

  const handleOpenExplanation = (topicRisk) => {
    setExplanationData(topicRisk);
  };

  const handleNewUserCreated = (newUser) => {
    setUsers((prev) => [newUser, ...prev]);
    setSelectedUser(newUser);
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

          {currentTab === 'dashboard' && (
            <DashboardScreen
              dashboardData={dashboardData}
              courses={courses}
              loading={loading}
              user={selectedUser}
              onOpenStudyModal={handleOpenStudy}
              onOpenSelfCheckModal={handleOpenSelfCheck}
              onOpenExplanation={handleOpenExplanation}
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
