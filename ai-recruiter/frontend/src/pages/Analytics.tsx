import React, { useState, useEffect } from 'react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  PieChart, 
  Pie, 
  Cell, 
  Legend 
} from 'recharts';
import { 
  BarChart3, 
  TrendingUp, 
  Users, 
  Briefcase, 
  Award, 
  Sparkles, 
  RefreshCw, 
  AlertCircle,
  GraduationCap,
  Layers,
  ArrowUpRight
} from 'lucide-react';
import { analyticsService } from '../services/analyticsService';
import { pipelineService } from '../services/pipelineService';
import { AnalyticsOverviewResponse } from '../types';

const COLORS = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'];

export const Analytics: React.FC = () => {
  const [data, setData] = useState<AnalyticsOverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await analyticsService.getOverview();
      setData(res);
    } catch (err: any) {
      console.error('Failed to load analytics:', err);
      setError(err?.response?.data?.detail || 'Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const handleSeedDemo = async () => {
    try {
      setSeeding(true);
      await pipelineService.seedPipeline();
      await fetchAnalytics();
    } catch (err: any) {
      setError('Failed to seed demo metrics');
    } finally {
      setSeeding(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <BarChart3 className="w-6 h-6 text-brand-400" />
            <h1 className="text-2xl font-bold text-white tracking-tight">
              Recruitment Funnel & Talent Analytics
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time pipeline velocity, conversion ratios, candidate score distributions, and skill demand-supply gap.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleSeedDemo}
            disabled={seeding}
            className="btn-secondary text-xs flex items-center space-x-1.5"
            title="Populate test data across all stages"
          >
            <Sparkles className={`w-3.5 h-3.5 ${seeding ? 'animate-spin text-brand-400' : 'text-brand-400'}`} />
            <span>{seeding ? 'Seeding...' : 'Populate Sample Data'}</span>
          </button>

          <button
            onClick={fetchAnalytics}
            disabled={loading}
            className="btn-primary text-xs flex items-center space-x-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Analytics</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading && !data ? (
        <div className="p-20 text-center text-slate-400 space-y-3">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto text-brand-400" />
          <p className="text-xs">Aggregating recruitment metrics and candidate distributions...</p>
        </div>
      ) : data ? (
        <div className="space-y-6">
          {/* KPI Cards Row */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="card p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400">Active Roles</span>
                <Briefcase className="w-4 h-4 text-brand-400" />
              </div>
              <div className="text-3xl font-extrabold text-white mt-2">
                {data.active_jobs}
                <span className="text-xs font-normal text-slate-500 ml-1.5">/ {data.total_jobs} total</span>
              </div>
              <span className="text-2xs text-emerald-400 flex items-center mt-1">
                <ArrowUpRight className="w-3 h-3 mr-0.5" /> Requisitions actively hiring
              </span>
            </div>

            <div className="card p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400">Total Talent Pool</span>
                <Users className="w-4 h-4 text-cyan-400" />
              </div>
              <div className="text-3xl font-extrabold text-white mt-2">
                {data.total_candidates}
              </div>
              <span className="text-2xs text-slate-400 mt-1 block">
                {data.total_applications} evaluations processed
              </span>
            </div>

            <div className="card p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400">Avg Candidate Fit</span>
                <Award className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="text-3xl font-extrabold text-brand-400 mt-2">
                {data.average_match_score}%
              </div>
              <span className="text-2xs text-slate-400 mt-1 block">
                5-factor weighted algorithm
              </span>
            </div>

            <div className="card p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400">Candidates Hired</span>
                <TrendingUp className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-3xl font-extrabold text-emerald-400 mt-2">
                {data.hired_count}
              </div>
              <span className="text-2xs text-slate-400 mt-1 block">
                {data.interviewing_count} currently in active interviews
              </span>
            </div>
          </div>

          {/* Chart 1: Recruitment Pipeline Funnel Progression */}
          <div className="card p-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                  <Layers className="w-4 h-4 text-brand-400" />
                  <span>Recruitment Pipeline Stage Progression</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Volume of candidates flowing across all 8 pipeline phases
                </p>
              </div>
            </div>

            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.funnel} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="funnelGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="stage" stroke="#64748b" textAnchor="end" tick={{ fontSize: 10 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px' }}
                    labelStyle={{ color: '#fff', fontWeight: 'bold' }}
                  />
                  <Area
                    type="monotone"
                    dataKey="count"
                    name="Candidates"
                    stroke="#6366f1"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#funnelGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Two-Column Grid: Match Score Distribution & Skills Supply vs Demand */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Score Distribution */}
            <div className="card p-6 space-y-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                <Award className="w-4 h-4 text-amber-400" />
                <span>Candidate Match Score Distribution</span>
              </h3>
              <p className="text-xs text-slate-400">
                Frequency histogram of computed fit percentages
              </p>

              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.score_distribution} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="bucket" stroke="#64748b" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px' }}
                    />
                    <Bar dataKey="count" name="Candidates" fill="#3b82f6" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Skills Demand vs Supply */}
            <div className="card p-6 space-y-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                <TrendingUp className="w-4 h-4 text-cyan-400" />
                <span>Skills Demand vs Talent Supply</span>
              </h3>
              <p className="text-xs text-slate-400">
                Jobs Requiring Skill (Indigo) vs Candidates With Skill (Cyan)
              </p>

              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.skills_gap} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="skill" stroke="#64748b" tick={{ fontSize: 10 }} />
                    <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px' }}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                    <Bar dataKey="job_demand_count" name="Roles Demanding" fill="#6366f1" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="talent_supply_count" name="Talent Supply" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Bottom Grid: Education Level Distribution & Recent Activity Feed */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Education Pie Chart */}
            <div className="card p-6 space-y-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                <GraduationCap className="w-4 h-4 text-emerald-400" />
                <span>Education Background</span>
              </h3>
              <p className="text-xs text-slate-400">
                Highest degree attained across talent pool
              </p>

              <div className="h-56 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={data.education_breakdown}
                      dataKey="count"
                      nameKey="level"
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={75}
                      paddingAngle={4}
                    >
                      {data.education_breakdown.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div className="flex flex-wrap gap-2 justify-center text-2xs text-slate-300">
                {data.education_breakdown.map((item, idx) => (
                  <span key={item.level} className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[idx % COLORS.length] }} />
                    <span>{item.level} ({item.percentage}%)</span>
                  </span>
                ))}
              </div>
            </div>

            {/* Recent Activity Feed */}
            <div className="lg:col-span-2 card p-6 space-y-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-brand-400" />
                <span>Recent Platform Activity</span>
              </h3>
              <p className="text-xs text-slate-400">
                Audit trail of recent stage shifts, candidate evaluations, and recruiter notes
              </p>

              <div className="space-y-3 pt-1">
                {data.recent_activity.map((act) => (
                  <div
                    key={act.id}
                    className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-start justify-between gap-3 text-xs"
                  >
                    <div>
                      <div className="font-semibold text-white">{act.title}</div>
                      <div className="text-slate-400 text-xs mt-0.5">{act.description}</div>
                    </div>
                    <span className="text-2xs text-slate-500 flex-shrink-0">
                      {new Date(act.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default Analytics;
