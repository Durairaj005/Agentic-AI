import React, { useState, useEffect } from 'react';
import { X, Plus, Trash2, Check, Star, AlertCircle, Sparkles, Wand2 } from 'lucide-react';
import { Job } from '../../types';
import { JobPayload } from '../../services/jobService';
import aiService from '../../services/aiService';

interface JobFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: JobPayload) => Promise<void>;
  initialJob?: Job | null;
}

export const JobFormModal: React.FC<JobFormModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  initialJob
}) => {
  const [title, setTitle] = useState('');
  const [company, setCompany] = useState('');
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('Remote');
  const [employmentType, setEmploymentType] = useState<'FULL_TIME' | 'PART_TIME' | 'CONTRACT' | 'REMOTE'>('FULL_TIME');
  const [experienceMin, setExperienceMin] = useState(2.0);
  const [experienceMax, setExperienceMax] = useState(6.0);
  const [status, setStatus] = useState<'ACTIVE' | 'DRAFT' | 'CLOSED'>('ACTIVE');
  
  // Dynamic skills
  const [skills, setSkills] = useState<{ skill: string; importance: 'HIGH' | 'MEDIUM' | 'LOW'; required: boolean }[]>([]);
  const [newSkillName, setNewSkillName] = useState('');
  const [newSkillRequired, setNewSkillRequired] = useState(true);
  const [newSkillImportance, setNewSkillImportance] = useState<'HIGH' | 'MEDIUM' | 'LOW'>('HIGH');

  // AI JD Auto-Parse Drawer / Panel
  const [showAIPaste, setShowAIPaste] = useState(false);
  const [rawJDPaste, setRawJDPaste] = useState('');
  const [aiParsing, setAiParsing] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialJob) {
      setTitle(initialJob.title);
      setCompany(initialJob.company);
      setDescription(initialJob.description);
      setLocation(initialJob.location);
      setEmploymentType(initialJob.employment_type);
      setExperienceMin(initialJob.experience_min);
      setExperienceMax(initialJob.experience_max);
      setStatus(initialJob.status);
      setSkills(
        initialJob.skills.map((s) => ({
          skill: s.skill,
          importance: s.importance,
          required: s.required
        }))
      );
    } else {
      // Defaults for new job
      setTitle('');
      setCompany('');
      setDescription('');
      setLocation('Remote');
      setEmploymentType('FULL_TIME');
      setExperienceMin(2.0);
      setExperienceMax(6.0);
      setStatus('ACTIVE');
      setSkills([
        { skill: 'Python', importance: 'HIGH', required: true },
        { skill: 'SQL', importance: 'HIGH', required: true },
        { skill: 'Docker', importance: 'MEDIUM', required: false },
      ]);
    }
    setShowAIPaste(false);
    setRawJDPaste('');
    setError(null);
  }, [initialJob, isOpen]);

  if (!isOpen) return null;

  const handleAddSkill = () => {
    if (!newSkillName.trim()) return;
    if (skills.some((s) => s.skill.toLowerCase() === newSkillName.trim().toLowerCase())) {
      setError(`Skill "${newSkillName.trim()}" is already added.`);
      return;
    }
    setSkills([
      ...skills,
      {
        skill: newSkillName.trim(),
        importance: newSkillImportance,
        required: newSkillRequired
      }
    ]);
    setNewSkillName('');
    setError(null);
  };

  const handleRemoveSkill = (index: number) => {
    setSkills(skills.filter((_, i) => i !== index));
  };

  const handleAIParseJD = async () => {
    if (!rawJDPaste.trim()) {
      setError('Please paste the job description text to parse.');
      return;
    }

    setAiParsing(true);
    setError(null);

    try {
      const parsed = await aiService.parseJD(rawJDPaste);
      setTitle(parsed.title);
      setDescription(parsed.description);
      setLocation(parsed.location);
      setEmploymentType(parsed.employment_type);
      setExperienceMin(parsed.experience_min);
      setExperienceMax(parsed.experience_max);
      setSkills(
        parsed.skills.map((s) => ({
          skill: s.skill,
          importance: s.importance,
          required: s.required
        }))
      );
      setShowAIPaste(false);
      setRawJDPaste('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to auto-parse job description.');
    } finally {
      setAiParsing(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !company || !description) {
      setError('Please provide title, company name, and full job description.');
      return;
    }
    if (experienceMin > experienceMax) {
      setError('Minimum experience cannot exceed maximum experience.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await onSubmit({
        title,
        company,
        description,
        location,
        employment_type: employmentType,
        experience_min: experienceMin,
        experience_max: experienceMax,
        status,
        skills
      });
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save job requisition.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden animate-fade-in my-8">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/60">
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-bold text-white">
                {initialJob ? 'Edit Requisition' : 'Create Job Requisition'}
              </h2>
              <button
                type="button"
                onClick={() => setShowAIPaste(!showAIPaste)}
                className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-brand-500/20 border border-brand-500/30 text-brand-300 text-xs font-semibold hover:bg-brand-500/30 transition"
              >
                <Wand2 className="w-3 h-3 text-brand-400" />
                <span>AI Auto-Parse JD</span>
              </button>
            </div>
            <p className="text-xs text-slate-400">
              Define role parameters and classify required vs. preferred technical skills
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* AI Parse Drawer / Dropdown */}
        {showAIPaste && (
          <div className="m-6 p-4 rounded-xl bg-brand-950/30 border border-brand-500/30 space-y-3 animate-fade-in">
            <div className="flex items-center justify-between text-xs font-bold text-brand-300">
              <span className="flex items-center space-x-1.5">
                <Sparkles className="w-4 h-4 text-brand-400" />
                <span>Paste Raw Job Description to Auto-Extract Parameters & Skills</span>
              </span>
              <button
                type="button"
                onClick={() => setShowAIPaste(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <textarea
              rows={4}
              value={rawJDPaste}
              onChange={(e) => setRawJDPaste(e.target.value)}
              placeholder="Paste raw job description text here... The AI parser will automatically extract role title, experience bounds, location, and classify required vs preferred technical skills."
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />

            <div className="flex justify-end">
              <button
                type="button"
                disabled={aiParsing}
                onClick={handleAIParseJD}
                className="px-4 py-1.5 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-xs font-semibold flex items-center space-x-1.5 shadow-md shadow-brand-600/30 disabled:opacity-50"
              >
                {aiParsing ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Extracting Structured Fields...</span>
                  </>
                ) : (
                  <>
                    <Wand2 className="w-3.5 h-3.5" />
                    <span>Extract & Fill Form</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {error && (
          <div className="m-6 mb-0 p-3 bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs rounded-xl flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Job Title *
              </label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Senior Python Developer"
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Company Name *
              </label>
              <input
                type="text"
                required
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                placeholder="e.g. Acme Cloud Corp"
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Location
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. Remote / New York"
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Employment Type
              </label>
              <select
                value={employmentType}
                onChange={(e) => setEmploymentType(e.target.value as any)}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="FULL_TIME">Full Time</option>
                <option value="REMOTE">Remote</option>
                <option value="CONTRACT">Contract</option>
                <option value="PART_TIME">Part Time</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Requisition Status
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as any)}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="ACTIVE">Active</option>
                <option value="DRAFT">Draft</option>
                <option value="CLOSED">Closed</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Min Experience (Years)
              </label>
              <input
                type="number"
                step="0.5"
                min="0"
                max="30"
                value={experienceMin}
                onChange={(e) => setExperienceMin(parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Max Experience (Years)
              </label>
              <input
                type="number"
                step="0.5"
                min="0"
                max="30"
                value={experienceMax}
                onChange={(e) => setExperienceMax(parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Job Description *
            </label>
            <textarea
              required
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Outline responsibilities, team structure, technical scope, and project expectations..."
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500 leading-relaxed"
            />
          </div>

          {/* Classified Technical Skills Section */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-white uppercase tracking-wider">
                Classified Skills Matrix
              </span>
              <span className="text-[11px] text-slate-400">
                {skills.filter((s) => s.required).length} Required &bull; {skills.filter((s) => !s.required).length} Preferred
              </span>
            </div>

            {/* Add Skill Row */}
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <input
                type="text"
                value={newSkillName}
                onChange={(e) => setNewSkillName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddSkill();
                  }
                }}
                placeholder="Add skill (e.g. AWS, Django, Spark)..."
                className="flex-1 min-w-[140px] px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />

              <div className="flex items-center space-x-1 bg-slate-900 p-0.5 rounded-lg border border-slate-700">
                <button
                  type="button"
                  onClick={() => setNewSkillRequired(true)}
                  className={`px-2 py-1 rounded text-[11px] font-semibold flex items-center space-x-1 ${
                    newSkillRequired ? 'bg-brand-600 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <Check className="w-3 h-3" />
                  <span>Required</span>
                </button>
                <button
                  type="button"
                  onClick={() => setNewSkillRequired(false)}
                  className={`px-2 py-1 rounded text-[11px] font-semibold flex items-center space-x-1 ${
                    !newSkillRequired ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <Star className="w-3 h-3" />
                  <span>Preferred</span>
                </button>
              </div>

              <select
                value={newSkillImportance}
                onChange={(e) => setNewSkillImportance(e.target.value as any)}
                className="px-2 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-300 focus:outline-none"
              >
                <option value="HIGH">High</option>
                <option value="MEDIUM">Med</option>
                <option value="LOW">Low</option>
              </select>

              <button
                type="button"
                onClick={handleAddSkill}
                className="p-1.5 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>

            {/* Added Skills Tags */}
            <div className="flex flex-wrap gap-2 pt-2 min-h-[40px]">
              {skills.length === 0 ? (
                <span className="text-xs text-slate-500 italic">No skills added yet.</span>
              ) : (
                skills.map((s, index) => (
                  <span
                    key={index}
                    className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border ${
                      s.required
                        ? 'bg-brand-500/10 border-brand-500/30 text-brand-300'
                        : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                    }`}
                  >
                    {s.required ? (
                      <Check className="w-3 h-3 text-brand-400" />
                    ) : (
                      <Star className="w-3 h-3 text-emerald-400" />
                    )}
                    <span>{s.skill}</span>
                    <span className="text-[9px] uppercase px-1 rounded bg-slate-800 text-slate-400">
                      {s.importance}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleRemoveSkill(index)}
                      className="ml-1 text-slate-400 hover:text-rose-400"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))
              )}
            </div>
          </div>

          {/* Footer Controls */}
          <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-800 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 rounded-xl text-xs font-semibold text-white bg-brand-600 hover:bg-brand-500 transition shadow-lg shadow-brand-600/30 disabled:opacity-50 flex items-center space-x-2"
            >
              {loading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <span>{initialJob ? 'Update Requisition' : 'Create Requisition'}</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default JobFormModal;
