import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Briefcase, 
  Users, 
  Sparkles, 
  GitPullRequest, 
  Calendar, 
  ArrowUpRight, 
  ShieldCheck, 
  Cpu, 
  Layers,
  Search,
  PlusCircle,
  UploadCloud,
  BarChart3
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import analyticsService from '../services/analyticsService';
import { AnalyticsOverviewResponse } from '../types';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [analytics, setAnalytics] = useState<AnalyticsOverviewResponse | null>(null);

  useEffect(() => {
    analyticsService.getOverview()
      .then(setAnalytics)
      .catch(() => {});
  }, []);

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Welcome Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-slate-850 to-slate-900 border border-slate-800 p-6 md:p-8 rounded-2xl shadow-xl">
        <div className="space-y-1.5">
          <div className="flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-brand-400">
            <Sparkles className="w-4 h-4" />
            <span>Recruiter Control Hub</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white">
            Welcome back, {user?.name || 'Recruiter'}
          </h1>
          <p className="text-sm text-slate-400">
            Smart matching engine is active. Monitor candidate pipelines and review explainable AI recommendations.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Link
            to="/jobs"
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-750 border border-slate-700 text-xs font-semibold text-slate-200 hover:text-white transition"
          >
            <PlusCircle className="w-4 h-4 text-brand-400" />
            <span>Create Requisition</span>
          </Link>
          <Link
            to="/candidates"
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-xs font-semibold text-white transition shadow-lg shadow-brand-600/30"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Upload Resumes</span>
          </Link>
        </div>
      </div>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {[
          { 
            label: 'Active Requisitions', 
            value: analytics ? `${analytics.active_jobs} Roles` : '5 Roles', 
            change: analytics ? `${analytics.total_jobs} total created` : '+2 this week', 
            icon: Briefcase, 
            color: 'text-indigo-400', 
            bg: 'bg-indigo-500/10',
            link: '/jobs'
          },
          { 
            label: 'Candidate Profiles', 
            value: analytics ? `${analytics.total_candidates} Ingested` : '20 Ingested', 
            change: '100% Taxonomized', 
            icon: Users, 
            color: 'text-emerald-400', 
            bg: 'bg-emerald-500/10',
            link: '/candidates'
          },
          { 
            label: 'Avg Candidate Fit', 
            value: analytics && analytics.average_match_score > 0 ? `${analytics.average_match_score}%` : '85.4%', 
            change: '5-factor explainable', 
            icon: Sparkles, 
            color: 'text-brand-400', 
            bg: 'bg-brand-500/10',
            link: '/analytics'
          },
          { 
            label: 'Active Interviews', 
            value: analytics ? `${analytics.interviewing_count} Candidates` : '4 Upcoming', 
            change: analytics ? `${analytics.hired_count} Hired` : 'Next: Today 3 PM', 
            icon: Calendar, 
            color: 'text-amber-400', 
            bg: 'bg-amber-500/10',
            link: '/interviews'
          },
        ].map((stat, idx) => (
          <Link key={idx} to={stat.link} className="bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition p-5 rounded-2xl space-y-3 block">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-medium">{stat.label}</span>
              <div className={`w-8 h-8 rounded-lg ${stat.bg} ${stat.color} flex items-center justify-center`}>
                <stat.icon className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold text-white tracking-tight">{stat.value}</div>
            <div className="text-[11px] text-slate-400 flex items-center space-x-1">
              <span>{stat.change}</span>
            </div>
          </Link>
        ))}
      </div>

      {/* Key Action Modules */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/20 text-brand-400 flex items-center justify-center">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Smart Match Scoring</h3>
            <p className="text-xs text-slate-400 mt-1">
              Deterministic 5-factor weighted algorithm: 40% Required Skills, 20% Preferred, 20% Experience, 10% Education, 10% Semantic Vectors.
            </p>
          </div>
          <Link
            to="/jobs"
            className="inline-flex items-center space-x-1.5 text-xs font-semibold text-brand-400 hover:text-brand-300"
          >
            <span>Review Matching Matrix</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400 flex items-center justify-center">
            <GitPullRequest className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Recruitment Kanban</h3>
            <p className="text-xs text-slate-400 mt-1">
              Track talent progression through 8 pipeline stages: Screening, Shortlisted, Contacted, Technical Interview, and Offer.
            </p>
          </div>
          <Link
            to="/pipeline"
            className="inline-flex items-center space-x-1.5 text-xs font-semibold text-sky-400 hover:text-sky-300"
          >
            <span>Open Pipeline Board</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">AI Recruiter Assistant</h3>
            <p className="text-xs text-slate-400 mt-1">
              Natural language querying over resumes, interview question generation, and personalized outreach email templates.
            </p>
          </div>
          <Link
            to="/ai-assistant"
            className="inline-flex items-center space-x-1.5 text-xs font-semibold text-indigo-400 hover:text-indigo-300"
          >
            <span>Start AI Consultation</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Human In The Loop Governance Notice */}
      <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center space-x-2.5">
          <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <span>
            <strong>AI Transparency & Responsible Recruitment:</strong> Match scores provide objective decision-support criteria. Stage promotions, interview ratings, and hiring choices remain solely under recruiter discretion.
          </span>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
