import React, { useState, useEffect } from 'react';
import { 
  Users, 
  UploadCloud, 
  Search, 
  Filter, 
  Database, 
  CheckCircle2, 
  AlertCircle,
  X
} from 'lucide-react';
import candidateService from '../services/candidateService';
import { Candidate } from '../types';
import CandidateCard from '../components/candidates/CandidateCard';
import ResumeUploader from '../components/candidates/ResumeUploader';

export const Candidates: React.FC = () => {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [educationFilter, setEducationFilter] = useState<string>('ALL');
  const [experienceRange, setExperienceRange] = useState<string>('ALL');
  const [skillFilter, setSkillFilter] = useState<string>('');

  const [uploaderOpen, setUploaderOpen] = useState<boolean>(false);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const showNotification = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 3500);
  };

  const fetchCandidates = async () => {
    try {
      setLoading(true);
      let minExp: number | undefined;
      let maxExp: number | undefined;

      if (experienceRange === 'JUNIOR') {
        minExp = 0;
        maxExp = 2.5;
      } else if (experienceRange === 'MID') {
        minExp = 2.5;
        maxExp = 5.0;
      } else if (experienceRange === 'SENIOR') {
        minExp = 5.0;
      }

      const data = await candidateService.getCandidates({
        search: search.trim() || undefined,
        education_level: educationFilter !== 'ALL' ? educationFilter : undefined,
        min_experience: minExp,
        max_experience: maxExp,
        skill: skillFilter.trim() || undefined,
      });
      setCandidates(data);
    } catch (err: any) {
      showNotification('error', err.response?.data?.detail || 'Failed to fetch candidate directory');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCandidates();
  }, [educationFilter, experienceRange, skillFilter]);

  // Debounced search trigger
  useEffect(() => {
    const handler = setTimeout(() => {
      fetchCandidates();
    }, 300);
    return () => clearTimeout(handler);
  }, [search]);

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this candidate profile?')) return;
    try {
      await candidateService.deleteCandidate(id);
      showNotification('success', 'Candidate profile removed.');
      fetchCandidates();
    } catch (err: any) {
      showNotification('error', err.response?.data?.detail || 'Could not delete candidate');
    }
  };

  const handleSeedCandidates = async () => {
    try {
      setLoading(true);
      const seeded = await candidateService.seedCandidates();
      showNotification('success', `Populated ${seeded.length} realistic technical candidate profiles.`);
      fetchCandidates();
    } catch (err: any) {
      showNotification('error', err.response?.data?.detail || 'Failed to seed sample candidates');
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Banner and Summary */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center space-x-2.5">
            <Users className="w-6 h-6 text-brand-400" />
            <span>Candidate Directory</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Browse parsed technical talent, manage candidate dossiers, and extract skill vectors.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleSeedCandidates}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-750 border border-slate-700 text-xs font-semibold text-slate-200 hover:text-white transition"
          >
            <Database className="w-3.5 h-3.5 text-emerald-400" />
            <span>Seed 20 Sample Talent</span>
          </button>

          <button
            onClick={() => setUploaderOpen(true)}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-xs font-semibold text-white transition shadow-lg shadow-brand-600/30"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Upload Resume</span>
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
            placeholder="Search name, skill, or Boolean (e.g. Python AND Docker NOT Junior)..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-800/80 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          {/* Skill Filter */}
          <input
            type="text"
            placeholder="Skill (e.g. Python)..."
            value={skillFilter}
            onChange={(e) => setSkillFilter(e.target.value)}
            className="w-32 px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />

          {/* Education Filter */}
          <select
            value={educationFilter}
            onChange={(e) => setEducationFilter(e.target.value)}
            className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-xl text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-brand-500"
          >
            <option value="ALL">All Degrees</option>
            <option value="BACHELORS">Bachelors</option>
            <option value="MASTERS">Masters</option>
            <option value="PHD">PhD</option>
            <option value="DIPLOMA">Diploma</option>
          </select>

          {/* Experience Range Filter */}
          <select
            value={experienceRange}
            onChange={(e) => setExperienceRange(e.target.value)}
            className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-xl text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-brand-500"
          >
            <option value="ALL">All Experience</option>
            <option value="JUNIOR">0 - 2.5 Years</option>
            <option value="MID">2.5 - 5.0 Years</option>
            <option value="SENIOR">5.0+ Years</option>
          </select>
        </div>
      </div>

      {/* Candidates Grid */}
      {loading ? (
        <div className="py-16 text-center space-y-3">
          <div className="w-8 h-8 border-4 border-brand-500/20 border-t-brand-500 rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Loading candidate directory...</p>
        </div>
      ) : candidates.length === 0 ? (
        <div className="bg-slate-900/40 border border-dashed border-slate-800 rounded-2xl p-12 text-center space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-slate-800 flex items-center justify-center text-slate-400 mx-auto">
            <Users className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-white">No candidates found</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Upload candidate resumes (PDF, DOCX, TXT) or populate 20 pre-built technical candidates.
            </p>
          </div>
          <div className="flex items-center justify-center space-x-3 pt-2">
            <button
              onClick={handleSeedCandidates}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-750 text-slate-200 border border-slate-700 rounded-xl text-xs font-semibold transition"
            >
              Seed 20 Sample Candidates
            </button>
            <button
              onClick={() => setUploaderOpen(true)}
              className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-xl text-xs font-semibold transition"
            >
              Upload Resume
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {candidates.map((cand) => (
            <CandidateCard
              key={cand.id}
              candidate={cand}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {/* Upload Modal */}
      {uploaderOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="relative w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 space-y-4 animate-fade-in">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-base font-bold text-white flex items-center space-x-2">
                <UploadCloud className="w-5 h-5 text-brand-400" />
                <span>Upload Candidate Resume</span>
              </h2>
              <button
                onClick={() => setUploaderOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <ResumeUploader
              onSuccess={() => {
                fetchCandidates();
              }}
              onClose={() => setUploaderOpen(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default Candidates;
