import React, { useState, useEffect } from 'react';
import { 
  Briefcase, 
  Plus, 
  Search, 
  Filter, 
  Sparkles, 
  CheckCircle2, 
  AlertCircle,
  Database
} from 'lucide-react';
import jobService, { JobPayload } from '../services/jobService';
import { Job } from '../types';
import JobCard from '../components/jobs/JobCard';
import JobFormModal from '../components/jobs/JobFormModal';

export const Jobs: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [employmentFilter, setEmploymentFilter] = useState<string>('ALL');

  const [modalOpen, setModalOpen] = useState<boolean>(false);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);

  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const showNotification = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 3500);
  };

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const data = await jobService.getJobs({
        status: statusFilter !== 'ALL' ? statusFilter : undefined,
        search: search.trim() || undefined,
        employment_type: employmentFilter !== 'ALL' ? employmentFilter : undefined,
      });
      setJobs(data);
    } catch (err: any) {
      showNotification('error', err.response?.data?.detail || 'Failed to fetch job requisitions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [statusFilter, employmentFilter]);

  // Debounced search trigger
  useEffect(() => {
    const handler = setTimeout(() => {
      fetchJobs();
    }, 300);
    return () => clearTimeout(handler);
  }, [search]);

  const handleCreateOrUpdate = async (payload: JobPayload) => {
    if (selectedJob) {
      await jobService.updateJob(selectedJob.id, payload);
      showNotification('success', `Requisition "${payload.title}" updated successfully.`);
    } else {
      await jobService.createJob(payload);
      showNotification('success', `Requisition "${payload.title}" created successfully.`);
    }
    fetchJobs();
  };

  const handleToggleStatus = async (id: string) => {
    try {
      const updated = await jobService.toggleStatus(id);
      showNotification('success', `Requisition marked as ${updated.status}.`);
      fetchJobs();
    } catch (err: any) {
      showNotification('error', err.response?.data?.detail || 'Could not update status');
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this job requisition?')) return;
    try {
      await jobService.deleteJob(id);
      showNotification('success', 'Job requisition deleted.');
      fetchJobs();
    } catch (err: any) {
      showNotification('error', err.response?.data?.detail || 'Could not delete job');
    }
  };

  const handleSeedJobs = async () => {
    try {
      setLoading(true);
      const seeded = await jobService.seedJobs();
      showNotification('success', `Populated ${seeded.length} realistic technical requisitions.`);
      fetchJobs();
    } catch (err: any) {
      showNotification('error', err.response?.data?.detail || 'Failed to seed sample jobs');
      setLoading(false);
    }
  };

  const activeCount = jobs.filter((j) => j.status === 'ACTIVE').length;
  const closedCount = jobs.filter((j) => j.status === 'CLOSED').length;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Banner and Summary */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center space-x-2.5">
            <Briefcase className="w-6 h-6 text-brand-400" />
            <span>Job Requisitions</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Manage technical job descriptions, skill requirements, and candidate matching pipelines.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleSeedJobs}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-750 border border-slate-700 text-xs font-semibold text-slate-200 hover:text-white transition"
          >
            <Database className="w-3.5 h-3.5 text-indigo-400" />
            <span>Seed 5 Demo Roles</span>
          </button>

          <button
            onClick={() => {
              setSelectedJob(null);
              setModalOpen(true);
            }}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-xs font-semibold text-white transition shadow-lg shadow-brand-600/30"
          >
            <Plus className="w-4 h-4" />
            <span>Create Requisition</span>
          </button>
        </div>
      </div>

      {/* Toast Notification Banner */}
      {notification && (
        <div
          className={`p-3.5 rounded-xl border text-xs flex items-center space-x-2.5 transition animate-fade-in ${
            notification.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
              : 'bg-rose-500/10 border-rose-500/20 text-rose-300'
          }`}
        >
          {notification.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-400" />
          )}
          <span>{notification.message}</span>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-2xl flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Search */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search roles, skills, or companies..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-800/80 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        {/* Status Filters */}
        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800">
            {['ALL', 'ACTIVE', 'CLOSED'].map((tab) => (
              <button
                key={tab}
                onClick={() => setStatusFilter(tab)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                  statusFilter === tab
                    ? 'bg-brand-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {tab.charAt(0) + tab.slice(1).toLowerCase()}
              </button>
            ))}
          </div>

          <select
            value={employmentFilter}
            onChange={(e) => setEmploymentFilter(e.target.value)}
            className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-xl text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-brand-500"
          >
            <option value="ALL">All Types</option>
            <option value="FULL_TIME">Full Time</option>
            <option value="REMOTE">Remote</option>
            <option value="CONTRACT">Contract</option>
          </select>
        </div>
      </div>

      {/* Jobs Grid */}
      {loading ? (
        <div className="py-16 text-center space-y-3">
          <div className="w-8 h-8 border-4 border-brand-500/20 border-t-brand-500 rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Loading requisitions...</p>
        </div>
      ) : jobs.length === 0 ? (
        <div className="bg-slate-900/40 border border-dashed border-slate-800 rounded-2xl p-12 text-center space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-slate-800 flex items-center justify-center text-slate-400 mx-auto">
            <Briefcase className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-white">No job requisitions found</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Get started by creating your first technical job description or seed 5 sample roles instantly.
            </p>
          </div>
          <div className="flex items-center justify-center space-x-3 pt-2">
            <button
              onClick={handleSeedJobs}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-750 text-slate-200 border border-slate-700 rounded-xl text-xs font-semibold transition"
            >
              Seed 5 Sample Roles
            </button>
            <button
              onClick={() => {
                setSelectedJob(null);
                setModalOpen(true);
              }}
              className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-xl text-xs font-semibold transition"
            >
              Create Requisition
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {jobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              onEdit={(j) => {
                setSelectedJob(j);
                setModalOpen(true);
              }}
              onDelete={handleDelete}
              onToggleStatus={handleToggleStatus}
            />
          ))}
        </div>
      )}

      {/* Modal Dialog */}
      <JobFormModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSubmit={handleCreateOrUpdate}
        initialJob={selectedJob}
      />
    </div>
  );
};

export default Jobs;
