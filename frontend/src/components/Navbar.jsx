import React, { useState } from 'react';
import { 
  User, 
  UserPlus, 
  RefreshCw, 
  BookOpen, 
  CheckCircle2, 
  ChevronDown,
  Clock,
  Sparkles
} from 'lucide-react';

export default function Navbar({ 
  users = [], 
  selectedUser, 
  onSelectUser, 
  onOpenNewUser,
  onOpenStudyModal,
  onOpenSelfCheckModal,
  onRefresh,
  loading,
}) {
  const [dropdownOpen, setDropdownOpen] = useState(false);

  return (
    <header className="h-20 bg-white border-b border-[#EDE9FE] px-8 flex items-center justify-between sticky top-0 z-20 shadow-card">
      {/* Left: Active student welcome */}
      <div className="flex items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold text-[#1E1B4B]">
              Hello, {selectedUser ? selectedUser.name.split(' ')[0] : 'Learner'}! 👋
            </h1>
            {selectedUser && (
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-violet-100 text-violet-700">
                Student #{selectedUser.id}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500">
            {selectedUser 
              ? `${selectedUser.email} • Track your memory and study sessions`
              : 'Add or select a student profile to begin'}
          </p>
        </div>
      </div>

      {/* Right: Actions & Student Selector */}
      <div className="flex items-center gap-3">
        {selectedUser && (
          <>
            {/* Quick Action: Log Study Session */}
            <button
              onClick={onOpenStudyModal}
              className="flex items-center gap-2 px-3.5 py-2 text-xs font-bold text-violet-700 bg-violet-50 hover:bg-violet-100 border border-violet-200 rounded-xl transition-all shadow-sm"
              title="Log a study session for a topic"
            >
              <Clock className="w-3.5 h-3.5 text-violet-600" />
              <span>Log Study</span>
            </button>

            {/* Quick Action: Quick Self-Check */}
            <button
              onClick={onOpenSelfCheckModal}
              className="flex items-center gap-2 px-3.5 py-2 text-xs font-bold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-xl transition-all shadow-sm"
              title="Log a recall quiz / self-check attempt"
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>Self-Check</span>
            </button>

            {/* Refresh */}
            <button
              onClick={onRefresh}
              disabled={loading}
              className="p-2 text-slate-500 hover:text-violet-600 hover:bg-[#F8F9FE] border border-slate-200 rounded-xl transition-all"
              title="Refresh Dashboard Data"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-violet-600' : ''}`} />
            </button>
          </>
        )}

        {/* Add Student Button */}
        <button
          onClick={onOpenNewUser}
          className="flex items-center gap-1.5 px-3.5 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-xl text-xs font-bold shadow-soft transition-all"
        >
          <UserPlus className="w-3.5 h-3.5" />
          <span>+ Add Student</span>
        </button>

        {/* Student Selector Dropdown (if students exist) */}
        {users.length > 0 && (
          <div className="relative">
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-2.5 px-3.5 py-2 bg-[#F8F9FE] hover:bg-[#F3F2FD] border border-[#EDE9FE] rounded-xl text-xs font-bold text-[#1E1B4B] transition-all"
            >
              <div className="w-6 h-6 rounded-full bg-violet-600 text-white flex items-center justify-center text-[10px] font-black">
                {selectedUser ? selectedUser.name.charAt(0).toUpperCase() : 'U'}
              </div>
              <span className="max-w-[130px] truncate">
                {selectedUser ? selectedUser.name : 'Select Student'}
              </span>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </button>

            {dropdownOpen && (
              <div className="absolute right-0 mt-2 w-72 bg-white rounded-2xl shadow-hover border border-[#EDE9FE] py-2 z-50 max-h-96 overflow-y-auto">
                <div className="px-3 py-1.5 border-b border-slate-100 flex items-center justify-between">
                  <span className="text-[11px] font-bold uppercase text-slate-400 tracking-wider">
                    Student Profiles ({users.length})
                  </span>
                  <button
                    onClick={() => {
                      setDropdownOpen(false);
                      onOpenNewUser();
                    }}
                    className="text-[11px] text-violet-600 hover:text-violet-800 font-bold flex items-center gap-1"
                  >
                    <UserPlus className="w-3 h-3" />
                    + New
                  </button>
                </div>

                {users.map((u) => (
                  <button
                    key={u.id}
                    onClick={() => {
                      onSelectUser(u);
                      setDropdownOpen(false);
                    }}
                    className={`w-full text-left px-3.5 py-2.5 text-xs flex items-center justify-between transition-colors ${
                      selectedUser?.id === u.id ? 'bg-violet-50 text-violet-700 font-bold' : 'hover:bg-slate-50 text-slate-700'
                    }`}
                  >
                    <div>
                      <div className="font-bold">{u.name}</div>
                      <div className="text-[10px] text-slate-400">{u.email}</div>
                    </div>
                    <span className="text-[10px] text-slate-400 ml-2">#{u.id}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
