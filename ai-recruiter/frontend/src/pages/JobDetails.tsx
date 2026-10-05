import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  Briefcase, 
  MapPin, 
  Clock, 
  Users, 
  ArrowLeft, 
  Edit3, 
  Power, 
  Trash2, 
  Sparkles, 
  CheckCircle2, 
  Star, 
  AlertCircle,
  FileText
} from 'lucide-react';
import jobService, { JobPayload } from '../services/jobService';
import { Job } from '../types';
import JobFormModal from '../components/jobs/JobFormModal';

export const JobDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState<boolean>(false);

  const fetchJob = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const data = await jobService.getJob(id);
      setJob(data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Job requisition not found');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJob();
  }, [id]);

  const handleUpdate = async (payload: JobPayload) => {
    if (!id) return;
    await jobService.updateJob(id, payload);
    fetchJob();
  };

  const handleToggleStatus = async () => {
    if (!id) return;
    const updated = await jobService.toggleStatus(id);
    setJob(updated);
  };

  const handleDelete = async () => {
    if (!id) return;
    if (!window.confirm('Are you sure you want to delete this job requisition?')) return;
    await jobService.deleteJob(id);
    navigate('/jobs');
  };

  if (loading) {
    return (
      <div className="py-20 text-center space-y-3">
        <div className="w-8 h-8 border-4 border-brand-500/20 border-t-brand-500 rounded-full animate-spin mx-auto" />
        <p className="text-xs text-slate-400">Loading requisition details...</p>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center space-y-4">
        <AlertCircle className="w-8 h-8 text-rose-400 mx-auto" />
        <h2 className="text-lg font-bold text-white">Requisition Not Found</h2>
        <p className="text-xs text-slate-400">{error || 'The requested job requisition does not exist.'}</p>
        <Link
          to="/jobs"
          className="inline-block px-4 py-2 bg-brand-600 text-white rounded-xl text-xs font-semibold"
        >
          Return to Jobs
        </Link>
      </div>
    );
  }

  const requiredSkills = job.skills.filter((s) => s.required);
  const preferredSkills = job.skills.filter((s) => !s.required);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Back Button */}
      <Link
        to="/jobs"
        className="inline-flex items-center space-x-1.5 text-xs font-semibold text-slate-400 hover:text-white transition"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Requisitions</span>
      </Link>

      {/* Main Header Card */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 md:p-8 shadow-xl space-y-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center space-x-2">
              <span
                className={`text-[10px] uppercase font-bold tracking-wider px-2.5 py-0.5 rounded-full border ${
                  job.status === 'ACTIVE'
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                    : 'bg-slate-800 border-slate-700 text-slate-400'
                }`}
              >
                {job.status}
              </span>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                {job.employment_type.replace('_', ' ')}
              </span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              {job.title}
            </h1>
            <div className="text-sm font-medium text-slate-300">{job.company}</div>
          </div>

          {/* Action buttons */}
          <div className="flex flex-wrap items-center gap-2.5">
            <Link
              to={`/jobs/${job.id}/matches`}
              className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-xs font-semibold text-white transition shadow-lg shadow-brand-500/25"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>AI Candidate Matches</span>
            </Link>

            <button
              onClick={handleToggleStatus}
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-750 border border-slate-700 text-xs font-semibold text-slate-200 transition"
            >
              <Power className={`w-3.5 h-3.5 ${job.status === 'ACTIVE' ? 'text-emerald-400' : 'text-slate-500'}`} />
              <span>{job.status === 'ACTIVE' ? 'Close Requisition' : 'Activate'}</span>
            </button>

            <button
              onClick={() => setModalOpen(true)}
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-750 border border-slate-700 text-xs font-semibold text-slate-200 transition"
            >
              <Edit3 className="w-3.5 h-3.5 text-brand-400" />
              <span>Edit</span>
            </button>

            <button
              onClick={handleDelete}
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-xs font-semibold text-rose-300 transition"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Delete</span>
            </button>
          </div>
        </div>

        {/* Quick Meta Row */}
        <div className="flex flex-wrap gap-y-2 gap-x-6 pt-4 border-t border-slate-800 text-xs text-slate-300">
          <div className="flex items-center space-x-1.5">
            <MapPin className="w-4 h-4 text-slate-500" />
            <span>{job.location}</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <Clock className="w-4 h-4 text-slate-500" />
            <span>Experience: {job.experience_min} to {job.experience_max} Years</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <Users className="w-4 h-4 text-indigo-400" />
            <span>{job.applicant_count || 0} Ingested Applicants</span>
          </div>
        </div>
      </div>

      {/* Grid Layout: Description & Skills Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Job Description */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center space-x-2 text-sm font-bold text-white uppercase tracking-wider">
              <FileText className="w-4 h-4 text-brand-400" />
              <span>Role Overview & Responsibilities</span>
            </div>
            <div className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">
              {job.description}
            </div>
          </div>
        </div>

        {/* Right Column: Classified Skills Matrix */}
        <div className="space-y-6">
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 space-y-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-sm font-bold text-white uppercase tracking-wider">
                <Sparkles className="w-4 h-4 text-brand-400" />
                <span>Skills Matrix</span>
              </div>
              <span className="text-[11px] text-slate-500 font-medium">
                {job.skills.length} Technical Skills
              </span>
            </div>

            {/* Required Skills */}
            <div className="space-y-2">
              <div className="flex items-center space-x-1.5 text-xs font-semibold text-brand-300">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Required Skills ({requiredSkills.length})</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {requiredSkills.map((s, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-brand-500/10 border border-brand-500/30 text-brand-200"
                  >
                    <span>{s.skill}</span>
                    <span className="text-[9px] uppercase px-1 rounded bg-brand-500/20 text-brand-300 font-bold">
                      {s.importance}
                    </span>
                  </span>
                ))}
              </div>
            </div>

            {/* Preferred Skills */}
            <div className="space-y-2 pt-2 border-t border-slate-800">
              <div className="flex items-center space-x-1.5 text-xs font-semibold text-emerald-300">
                <Star className="w-3.5 h-3.5" />
                <span>Preferred Skills ({preferredSkills.length})</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {preferredSkills.length === 0 ? (
                  <span className="text-xs text-slate-500 italic">No preferred skills defined.</span>
                ) : (
                  preferredSkills.map((s, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-emerald-500/10 border border-emerald-500/30 text-emerald-200"
                    >
                      <span>{s.skill}</span>
                      <span className="text-[9px] uppercase px-1 rounded bg-emerald-500/20 text-emerald-300 font-bold">
                        {s.importance}
                      </span>
                    </span>
                  ))
                )}
              </div>
            </div>

            {/* Matching Engine Callout */}
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <div className="text-xs font-semibold text-slate-200 flex items-center space-x-1.5">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                <span>Matching Engine Weights</span>
              </div>
              <p className="text-[11px] text-slate-400 leading-snug">
                Required skills contribute 40% to candidate scores, preferred skills 20%, experience 20%, education 10%, and vector semantics 10%.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Edit Modal */}
      <JobFormModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSubmit={handleUpdate}
        initialJob={job}
      />
    </div>
  );
};

export default JobDetails;
