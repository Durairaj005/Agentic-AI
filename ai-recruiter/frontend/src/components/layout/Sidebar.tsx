import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Briefcase,
  Users,
  GitPullRequest,
  Calendar,
  Clock,
  Sparkles,
  BarChart3,
  Scale,
  ShieldCheck,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

export const Sidebar: React.FC = () => {
  const { user } = useAuth();

  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/jobs', label: 'Job Requisitions', icon: Briefcase },
    { to: '/candidates', label: 'Candidates', icon: Users },
    { to: '/pipeline', label: 'Kanban Pipeline', icon: GitPullRequest },
    { to: '/compare', label: 'Candidate Compare', icon: Scale },
    { to: '/interviews', label: 'Interviews', icon: Calendar },
    { to: '/followups', label: 'Follow-ups', icon: Clock },
    { to: '/ai-assistant', label: 'AI Recruiter Chat', icon: Sparkles, highlight: true },
    { to: '/analytics', label: 'Analytics & Funnel', icon: BarChart3 },
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-950/50 flex flex-col justify-between p-4 flex-shrink-0">
      <div className="space-y-1">
        <div className="px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">
          Recruitment Workspace
        </div>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-medium transition ${
                isActive
                  ? 'bg-brand-600 text-white shadow-md shadow-brand-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`
            }
          >
            <item.icon className="w-4 h-4 flex-shrink-0" />
            <span>{item.label}</span>
            {item.highlight && (
              <span className="ml-auto text-[9px] px-1.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-semibold border border-indigo-500/30">
                AI
              </span>
            )}
          </NavLink>
        ))}

        {user?.role === 'ADMIN' && (
          <>
            <div className="pt-4 px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Administration
            </div>
            <NavLink
              to="/users"
              className={({ isActive }) =>
                `flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-medium transition ${
                  isActive
                    ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <ShieldCheck className="w-4 h-4 flex-shrink-0 text-emerald-400" />
              <span>User Management</span>
            </NavLink>
          </>
        )}
      </div>

      {/* Recruiter Footnote */}
      <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 text-[11px] text-slate-400 space-y-1">
        <div className="text-slate-300 font-semibold flex items-center space-x-1.5">
          <Sparkles className="w-3.5 h-3.5 text-brand-400" />
          <span>Local AI Active</span>
        </div>
        <p className="text-[10px] text-slate-400 leading-tight">
          Explainable matching & vector semantic indexing ready.
        </p>
      </div>
    </aside>
  );
};

export default Sidebar;
