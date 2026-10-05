import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { 
  Columns, 
  Search, 
  Filter, 
  Sparkles, 
  ArrowRight, 
  MapPin, 
  Clock, 
  Briefcase, 
  AlertCircle, 
  RefreshCw, 
  CheckCircle2, 
  ChevronRight,
  UserCheck,
  Calendar,
  Layers,
  MessageSquare
} from 'lucide-react';
import { pipelineService } from '../services/pipelineService';
import { jobService } from '../services/jobService';
import { Application, Job, ApplicationStatus } from '../types';

interface StageColumnConfig {
  id: ApplicationStatus;
  title: string;
  badgeBg: string;
  badgeText: string;
  borderHover: string;
  dotColor: string;
}

const STAGES: StageColumnConfig[] = [
  { id: 'NEW', title: 'New Applications', badgeBg: 'bg-slate-800', badgeText: 'text-slate-300', borderHover: 'hover:border-slate-600', dotColor: 'bg-slate-400' },
  { id: 'SCREENING', title: 'Screening', badgeBg: 'bg-blue-500/20', badgeText: 'text-blue-300', borderHover: 'hover:border-blue-500/40', dotColor: 'bg-blue-400' },
  { id: 'SHORTLISTED', title: 'Shortlisted', badgeBg: 'bg-indigo-500/20', badgeText: 'text-indigo-300', borderHover: 'hover:border-indigo-500/40', dotColor: 'bg-indigo-400' },
  { id: 'CONTACTED', title: 'Contacted', badgeBg: 'bg-cyan-500/20', badgeText: 'text-cyan-300', borderHover: 'hover:border-cyan-500/40', dotColor: 'bg-cyan-400' },
  { id: 'INTERVIEW', title: 'Interviewing', badgeBg: 'bg-amber-500/20', badgeText: 'text-amber-300', borderHover: 'hover:border-amber-500/40', dotColor: 'bg-amber-400' },
  { id: 'SELECTED', title: 'Selected / Offer', badgeBg: 'bg-emerald-500/20', badgeText: 'text-emerald-300', borderHover: 'hover:border-emerald-500/40', dotColor: 'bg-emerald-400' },
  { id: 'HIRED', title: 'Hired', badgeBg: 'bg-teal-500/20', badgeText: 'text-teal-300', borderHover: 'hover:border-teal-500/40', dotColor: 'bg-teal-400' },
  { id: 'REJECTED', title: 'Archived / Rejected', badgeBg: 'bg-rose-500/20', badgeText: 'text-rose-300', borderHover: 'hover:border-rose-500/40', dotColor: 'bg-rose-400' },
];

export const Pipeline: React.FC = () => {
  const [applications, setApplications] = useState<Application[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Filters
  const [selectedJobId, setSelectedJobId] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [minScore, setMinScore] = useState<number>(0);

  // Modal for changing stage with notes
  const [movingApp, setMovingApp] = useState<Application | null>(null);
  const [targetStage, setTargetStage] = useState<ApplicationStatus>('SHORTLISTED');
  const [stageNotes, setStageNotes] = useState<string>('');
  const [updatingStage, setUpdatingStage] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [appsData, jobsData] = await Promise.all([
        pipelineService.getApplications(),
        jobService.getJobs()
      ]);
      setApplications(appsData);
      setJobs(jobsData);
    } catch (err: any) {
      console.error('Failed to load pipeline:', err);
      setError(err?.response?.data?.detail || 'Failed to load recruitment pipeline');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSeedPipeline = async () => {
    try {
      setSeeding(true);
      setError(null);
      const res = await pipelineService.seedPipeline();
      setSuccessMessage(res.message);
      const updatedApps = await pipelineService.getApplications();
      setApplications(updatedApps);
    } catch (err: any) {
      console.error('Pipeline seed error:', err);
      setError(err?.response?.data?.detail || 'Failed to seed pipeline');
    } finally {
      setSeeding(false);
    }
  };

  const handleOpenMoveModal = (app: Application, nextStage: ApplicationStatus) => {
    setMovingApp(app);
    setTargetStage(nextStage);
    setStageNotes('');
  };

  const handleConfirmMove = async () => {
    if (!movingApp) return;
    try {
      setUpdatingStage(true);
      await pipelineService.updateStage(movingApp.id, targetStage, stageNotes);
      setSuccessMessage(`Moved ${movingApp.candidate?.name || 'candidate'} to ${targetStage}`);
      setMovingApp(null);
      // Refresh
      const updated = await pipelineService.getApplications();
      setApplications(updated);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to update candidate stage');
    } finally {
      setUpdatingStage(false);
    }
  };

  const filteredApps = useMemo(() => {
    return applications.filter(app => {
      if (selectedJobId !== 'ALL' && app.job_id !== selectedJobId) return false;
      if (minScore > 0 && app.match_score < minScore) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const candName = app.candidate?.name?.toLowerCase() || '';
        const jobTitle = app.job?.title?.toLowerCase() || '';
        const skillMatch = app.candidate?.skills?.some(s => s.skill.toLowerCase().includes(q));
        if (!candName.includes(q) && !jobTitle.includes(q) && !skillMatch) return false;
      }
      return true;
    });
  }, [applications, selectedJobId, minScore, searchQuery]);

  const appsByStage = useMemo(() => {
    const map: Record<string, Application[]> = {};
    STAGES.forEach(s => { map[s.id] = []; });
    filteredApps.forEach(app => {
      if (map[app.status]) {
        map[app.status].push(app);
      } else {
        // Fallback into NEW if unknown
        map['NEW'].push(app);
      }
    });
    return map;
  }, [filteredApps]);

  const getScoreColor = (score: number) => {
    if (score >= 85) return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
    if (score >= 70) return 'text-brand-400 bg-brand-500/10 border-brand-500/30';
    if (score >= 50) return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
  };

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      {/* Header and Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Columns className="w-6 h-6 text-brand-400" />
            <h1 className="text-2xl font-bold text-white tracking-tight">
              Recruitment Kanban Pipeline
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Track candidates across 8 recruitment stages, advance candidates, and record decision notes.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleSeedPipeline}
            disabled={seeding}
            className="btn-secondary text-xs flex items-center space-x-1.5"
            title="Populate pipeline stages with sample evaluations"
          >
            <Sparkles className={`w-3.5 h-3.5 ${seeding ? 'animate-spin' : 'text-brand-400'}`} />
            <span>{seeding ? 'Seeding...' : 'Seed Pipeline Demo'}</span>
          </button>

          <button
            onClick={fetchData}
            disabled={loading}
            className="btn-primary text-xs flex items-center space-x-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Messages */}
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
      {successMessage && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Filters Toolbar */}
      <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between bg-slate-900/60 border border-slate-800 p-3.5 rounded-2xl">
        <div className="flex-1 flex flex-col sm:flex-row gap-2">
          {/* Job Filter */}
          <div className="sm:w-64">
            <select
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              className="input text-xs w-full"
            >
              <option value="ALL">All Requisitions ({jobs.length})</option>
              {jobs.map(j => (
                <option key={j.id} value={j.id}>{j.title} ({j.company})</option>
              ))}
            </select>
          </div>

          {/* Search Bar */}
          <div className="relative flex-1">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search candidate name, role, or skill..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input pl-9 text-xs w-full"
            />
          </div>
        </div>

        {/* Min Score Filter */}
        <div className="flex items-center space-x-2">
          <span className="text-2xs text-slate-400 uppercase font-semibold">Min Score:</span>
          <select
            value={minScore}
            onChange={(e) => setMinScore(Number(e.target.value))}
            className="input text-xs w-28"
          >
            <option value="0">All</option>
            <option value="80">&ge; 80%</option>
            <option value="70">&ge; 70%</option>
            <option value="50">&ge; 50%</option>
          </select>
        </div>
      </div>

      {/* Kanban Board Container (Horizontally Scrollable) */}
      <div className="overflow-x-auto pb-4 custom-scrollbar">
        <div className="flex gap-4 min-w-[1750px]">
          {STAGES.map((col) => {
            const apps = appsByStage[col.id] || [];

            return (
              <div
                key={col.id}
                className="w-72 flex-shrink-0 bg-slate-900/70 border border-slate-800 rounded-2xl flex flex-col max-h-[750px]"
              >
                {/* Column Header */}
                <div className="p-3.5 border-b border-slate-800 flex items-center justify-between bg-slate-950/40 rounded-t-2xl">
                  <div className="flex items-center space-x-2">
                    <span className={`w-2.5 h-2.5 rounded-full ${col.dotColor}`} />
                    <h3 className="text-xs font-bold text-slate-200">{col.title}</h3>
                  </div>
                  <span className={`px-2 py-0.5 rounded-md text-2xs font-semibold ${col.badgeBg} ${col.badgeText}`}>
                    {apps.length}
                  </span>
                </div>

                {/* Column Cards Container */}
                <div className="p-2.5 space-y-2.5 overflow-y-auto flex-1 custom-scrollbar">
                  {apps.length === 0 ? (
                    <div className="p-6 text-center text-slate-500 text-2xs">
                      No candidates in this stage
                    </div>
                  ) : (
                    apps.map((app) => (
                      <div
                        key={app.id}
                        className={`bg-slate-950/70 border border-slate-800/80 rounded-xl p-3.5 transition-all shadow-sm ${col.borderHover} hover:shadow-md hover:bg-slate-950 group`}
                      >
                        {/* Top: Candidate Name and Match Score */}
                        <div className="flex items-start justify-between gap-2">
                          <Link
                            to={`/candidates/${app.candidate_id}`}
                            className="font-bold text-xs text-white hover:text-brand-300 transition line-clamp-1"
                          >
                            {app.candidate?.name || 'Candidate'}
                          </Link>
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold border ${getScoreColor(app.match_score)}`}>
                            {app.match_score.toFixed(0)}%
                          </span>
                        </div>

                        {/* Job Requisition */}
                        <div className="text-[11px] font-medium text-slate-400 mt-1 line-clamp-1">
                          {app.job?.title || 'Target Role'}
                        </div>

                        {/* Meta: Exp & Location */}
                        <div className="flex items-center gap-2 text-2xs text-slate-500 mt-1.5">
                          <span>{app.candidate?.total_experience || 0}y exp</span>
                          <span>&bull;</span>
                          <span className="line-clamp-1">{app.candidate?.location || 'Remote'}</span>
                        </div>

                        {/* Key Skills */}
                        {app.candidate?.skills && app.candidate.skills.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {app.candidate.skills.slice(0, 3).map((s) => (
                              <span
                                key={s.skill}
                                className="px-1.5 py-0.5 rounded text-[9px] bg-slate-800/90 text-slate-300 border border-slate-700/50"
                              >
                                {s.skill}
                              </span>
                            ))}
                            {app.candidate.skills.length > 3 && (
                              <span className="text-[9px] text-slate-500">
                                +{app.candidate.skills.length - 3}
                              </span>
                            )}
                          </div>
                        )}

                        {/* Recruiter Notes Snippet */}
                        {app.recruiter_notes && (
                          <div className="mt-2 text-[10px] text-slate-400 italic bg-slate-900/60 p-1.5 rounded border border-slate-800 line-clamp-2">
                            "{app.recruiter_notes}"
                          </div>
                        )}

                        {/* Quick Advance Footer */}
                        <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between text-2xs">
                          <Link
                            to={`/candidates/${app.candidate_id}`}
                            className="text-slate-400 hover:text-white"
                          >
                            Profile
                          </Link>

                          {/* Quick stage selector */}
                          <select
                            value={app.status}
                            onChange={(e) => handleOpenMoveModal(app, e.target.value as ApplicationStatus)}
                            className="bg-slate-900 border border-slate-700 text-slate-300 text-[10px] rounded px-1.5 py-0.5 cursor-pointer focus:outline-none focus:border-brand-500"
                          >
                            {STAGES.map(s => (
                              <option key={s.id} value={s.id}>{s.title}</option>
                            ))}
                          </select>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Stage Transition Modal */}
      {movingApp && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl animate-fade-in">
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <UserCheck className="w-5 h-5 text-brand-400" />
              <span>Update Recruitment Stage</span>
            </h3>

            <p className="text-xs text-slate-300">
              Move candidate <strong className="text-white">{movingApp.candidate?.name}</strong> to:
            </p>

            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">Target Stage</label>
              <select
                value={targetStage}
                onChange={(e) => setTargetStage(e.target.value as ApplicationStatus)}
                className="input text-xs w-full"
              >
                {STAGES.map(s => (
                  <option key={s.id} value={s.id}>{s.title}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">
                Recruiter Decision Notes (Optional)
              </label>
              <textarea
                value={stageNotes}
                onChange={(e) => setStageNotes(e.target.value)}
                placeholder="e.g., Passed technical screening with flying colors. Advancing to round 2 architecture review..."
                rows={3}
                className="input text-xs w-full resize-none"
              />
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setMovingApp(null)}
                disabled={updatingStage}
                className="btn-secondary text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmMove}
                disabled={updatingStage}
                className="btn-primary text-xs flex items-center space-x-1.5"
              >
                {updatingStage ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Updating...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Confirm Stage Move</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Pipeline;
