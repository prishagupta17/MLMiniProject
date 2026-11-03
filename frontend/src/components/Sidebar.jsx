import React from 'react';
import { 
  LayoutDashboard, 
  BookOpen, 
  Calendar, 
  TrendingUp, 
  Brain,
  ShieldCheck,
  Sparkles
} from 'lucide-react';

export default function Sidebar({ currentTab, setCurrentTab, user }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'courses', label: 'My Courses', icon: BookOpen },
    { id: 'planner', label: 'Study Planner', icon: Calendar },
    { id: 'progress', label: 'Progress', icon: TrendingUp },
  ];

  return (
    <aside className="w-64 bg-white border-r border-[#EDE9FE] flex flex-col fixed inset-y-0 left-0 z-30 transition-all">
      {/* Brand Logo */}
      <div className="h-20 flex items-center px-6 border-b border-[#F3F2FD] gap-3">
        <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center text-white shadow-soft">
          <Brain className="w-6 h-6" />
        </div>
        <div>
          <div className="font-extrabold text-base tracking-tight text-[#1E1B4B] flex items-center gap-1.5">
            Forgetting Engine
            <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded-full bg-violet-100 text-violet-700">
              v1
            </span>
          </div>
          <p className="text-xs text-slate-500 font-medium">Memory Retention AI</p>
        </div>
      </div>

      {/* Navigation */}
      <div className="p-4 flex-1">
        <p className="px-3 text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3">
          Main Menu
        </p>
        <nav className="space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentTab(item.id)}
                className={`w-full flex items-center gap-3.5 px-4 py-3 rounded-xl font-semibold text-sm transition-all text-left ${
                  isActive
                    ? 'bg-[#6C5CE7] text-white shadow-soft font-bold'
                    : 'text-slate-600 hover:bg-[#F8F9FE] hover:text-violet-700'
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                {item.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Info Card */}
      <div className="p-4 border-t border-[#F3F2FD]">
        <div className="p-3.5 rounded-2xl bg-[#FAF9FF] border border-[#EDE9FE]">
          <div className="flex items-center gap-2 mb-1.5">
            <ShieldCheck className="w-4 h-4 text-violet-600" />
            <span className="text-xs font-bold text-violet-900">Model Status</span>
          </div>
          <p className="text-[11px] text-slate-600 leading-relaxed">
            Active: <span className="font-semibold text-slate-800">Production v1</span> (13 Features, Balanced Logistic Regression)
          </p>
        </div>
      </div>
    </aside>
  );
}
