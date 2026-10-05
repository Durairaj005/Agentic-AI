import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Mail, 
  Phone, 
  MapPin, 
  Clock, 
  GraduationCap, 
  FileText, 
  Download, 
  Trash2, 
  Sparkles, 
  CheckCircle2, 
  AlertCircle,
  Eye,
  EyeOff,
  Briefcase,
  MessageSquare,
  Send,
  UserCheck
} from 'lucide-react';
import candidateService from '../services/candidateService';
import aiService from '../services/aiService';
import pipelineService from '../services/pipelineService';
import { Candidate, Note } from '../types';

export const CandidateProfile: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [reparsing, setReparsing] = useState<boolean>(false);
  const [notification, setNotification] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showRawText, setShowRawText] = useState<boolean>(false);
  const [notes, setNotes] = useState<Note[]>([]);
  const [newNoteText, setNewNoteText] = useState<string>('');
  const [addingNote, setAddingNote] = useState<boolean>(false);

  const fetchCandidate = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const [candData, notesData] = await Promise.all([
        candidateService.getCandidate(id),
        pipelineService.getCandidateNotes(id).catch(() => [])
      ]);
      setCandidate(candData);
      setNotes(notesData);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Candidate not found');
    } finally {
      setLoading(false);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !newNoteText.trim()) return;
    try {
      setAddingNote(true);
      const created = await pipelineService.addCandidateNote(id, newNoteText.trim());
      setNotes([created, ...notes]);
      setNewNoteText('');
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to add note');
    } finally {
      setAddingNote(false);
    }
  };

  useEffect(() => {
    fetchCandidate();
  }, [id]);

  const handleReparse = async () => {
    if (!id) return;
    setReparsing(true);
    try {
      const updated = await aiService.reparseCandidate(id);
      setCandidate(updated);
      setNotification(`Re-parsed resume text with canonical taxonomy. Identified ${updated.skills?.length || 0} skills.`);
      setTimeout(() => setNotification(null), 3500);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to re-parse candidate');
    } finally {
      setReparsing(false);
    }
  };

  const handleDelete = async () => {
    if (!id) return;
    if (!window.confirm('Are you sure you want to permanently delete this candidate profile?')) return;
    try {
      await candidateService.deleteCandidate(id);
      navigate('/candidates');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete candidate');
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center space-y-3">
        <div className="w-8 h-8 border-4 border-brand-500/20 border-t-brand-500 rounded-full animate-spin mx-auto" />
        <p className="text-xs text-slate-400">Loading candidate dossier...</p>
      </div>
    );
  }

  if (error || !candidate) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center space-y-4">
        <AlertCircle className="w-8 h-8 text-rose-400 mx-auto" />
        <h2 className="text-lg font-bold text-white">Candidate Not Found</h2>
        <p className="text-xs text-slate-400">{error || 'The requested profile does not exist.'}</p>
        <Link
          to="/candidates"
          className="inline-block px-4 py-2 bg-brand-600 text-white rounded-xl text-xs font-semibold"
        >
          Return to Candidates
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Back Link */}
      <Link
        to="/candidates"
        className="inline-flex items-center space-x-1.5 text-xs font-semibold text-slate-400 hover:text-white transition"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Directory</span>
      </Link>

      {/* Notification Banner */}
      {notification && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center space-x-2 animate-fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{notification}</span>
        </div>
      )}

      {/* Hero Dossier Card */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 md:p-8 shadow-xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="flex items-start space-x-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center text-white text-2xl font-bold shadow-lg shadow-brand-500/20 flex-shrink-0">
              {candidate.name.charAt(0).toUpperCase()}
            </div>
            <div className="space-y-1">
              <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
                {candidate.name}
              </h1>
              <div className="flex flex-wrap items-center gap-y-1 gap-x-4 text-xs text-slate-400">
                <div className="flex items-center space-x-1.5">
                  <Mail className="w-3.5 h-3.5 text-slate-500" />
                  <span>{candidate.email}</span>
                </div>
                {candidate.phone && (
                  <div className="flex items-center space-x-1.5">
                    <Phone className="w-3.5 h-3.5 text-slate-500" />
                    <span>{candidate.phone}</span>
                  </div>
                )}
                <div className="flex items-center space-x-1.5">
                  <MapPin className="w-3.5 h-3.5 text-slate-500" />
                  <span>{candidate.location}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-3">
            <button
              onClick={handleReparse}
              disabled={reparsing}
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-brand-600/20 hover:bg-brand-600/30 border border-brand-500/40 text-xs font-semibold text-brand-300 hover:text-white transition disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5 text-brand-400" />
              <span>{reparsing ? 'Re-parsing...' : 'Re-parse Skills'}</span>
            </button>

            {candidate.resume_path && (
              <a
                href={candidateService.getDownloadResumeUrl(candidate.id)}
                target="_blank"
                rel="noreferrer"
                className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-750 border border-slate-700 text-xs font-semibold text-slate-200 hover:text-white transition"
              >
                <Download className="w-3.5 h-3.5 text-indigo-400" />
                <span>Original File</span>
              </a>
            )}

            <button
              onClick={handleDelete}
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-xs font-semibold text-rose-300 transition"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Delete Profile</span>
            </button>
          </div>
        </div>

        {/* Highlight Pills */}
        <div className="flex flex-wrap gap-3 pt-2 border-t border-slate-800 text-xs">
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700 text-slate-200">
            <Clock className="w-4 h-4 text-brand-400" />
            <span className="font-semibold">{candidate.total_experience} Years Experience</span>
          </div>

          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700 text-slate-200">
            <GraduationCap className="w-4 h-4 text-emerald-400" />
            <span className="font-semibold">{candidate.education_level} ({candidate.education_details || 'Degree'})</span>
          </div>

          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700 text-slate-200">
            <FileText className="w-4 h-4 text-amber-400" />
            <span className="truncate max-w-[200px]">{candidate.resume_filename || 'Ingested Profile'}</span>
          </div>
        </div>
      </div>

      {/* Two Column Layout: Skills & Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Summary & Raw Resume */}
        <div className="lg:col-span-2 space-y-6">
          {/* Professional Summary */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 space-y-3">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-brand-400" />
              <span>Professional Summary</span>
            </h2>
            <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">
              {candidate.summary || 'No summary text available.'}
            </p>
          </div>

          {/* Raw Text Viewer */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-sm font-bold text-white uppercase tracking-wider">
                <FileText className="w-4 h-4 text-indigo-400" />
                <span>Extracted Resume Document Text</span>
              </div>
              <button
                onClick={() => setShowRawText(!showRawText)}
                className="flex items-center space-x-1 text-xs text-brand-400 hover:text-brand-300 font-semibold"
              >
                {showRawText ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                <span>{showRawText ? 'Hide Text' : 'View Full Extracted Text'}</span>
              </button>
            </div>

            {showRawText && (
              <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-300 font-mono overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-96">
                {candidate.resume_raw_text || 'No raw text stored.'}
              </pre>
            )}
          </div>

          {/* Recruiter Notes & Evaluation History */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
              <MessageSquare className="w-4 h-4 text-brand-400" />
              <span>Recruiter Notes & Timeline</span>
            </h2>

            {/* Note entry form */}
            <form onSubmit={handleAddNote} className="space-y-2">
              <textarea
                value={newNoteText}
                onChange={(e) => setNewNoteText(e.target.value)}
                placeholder="Log internal candidate evaluation notes, compensation expectations, or interviewer remarks..."
                rows={2}
                className="input text-xs w-full resize-none"
              />
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={addingNote || !newNoteText.trim()}
                  className="btn-primary text-xs py-1.5 px-3 flex items-center space-x-1.5"
                >
                  <Send className="w-3 h-3" />
                  <span>{addingNote ? 'Adding...' : 'Add Note'}</span>
                </button>
              </div>
            </form>

            {/* Notes list */}
            <div className="space-y-2.5 pt-2 border-t border-slate-800">
              {notes.length === 0 ? (
                <p className="text-xs text-slate-500 italic">No notes recorded for this candidate yet.</p>
              ) : (
                notes.map((n) => (
                  <div key={n.id} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
                    <div className="flex items-center justify-between text-2xs">
                      <span className="font-semibold text-brand-400">{n.recruiter_name || 'Recruiter'}</span>
                      <span className="text-slate-500">{new Date(n.created_at).toLocaleString()}</span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">{n.note}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Technical Skills */}
        <div className="space-y-6">
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Extracted Skills</span>
              </h2>
              <span className="text-[11px] text-slate-500 font-medium">
                {candidate.skills?.length || 0} Competencies
              </span>
            </div>

            <div className="space-y-2">
              {candidate.skills && candidate.skills.length > 0 ? (
                candidate.skills.map((s, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between"
                  >
                    <div className="space-y-0.5">
                      <div className="text-xs font-semibold text-slate-200">{s.skill}</div>
                      <div className="text-[10px] text-slate-400">
                        {s.years_experience} yrs &bull; Confidence {Math.round(s.confidence_score * 100)}%
                      </div>
                    </div>
                    <div className="w-16 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-brand-500 h-1.5 rounded-full"
                        style={{ width: `${Math.round(s.confidence_score * 100)}%` }}
                      />
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-500 italic">No skills extracted yet.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CandidateProfile;
