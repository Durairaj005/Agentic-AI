import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { 
  Calendar, 
  Clock, 
  User, 
  Briefcase, 
  Star, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  Plus, 
  RefreshCw,
  Search,
  MessageSquare,
  ChevronRight
} from 'lucide-react';
import { pipelineService, InterviewPayload } from '../services/pipelineService';
import { Interview, Application } from '../types';

export const Interviews: React.FC = () => {
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Schedule Modal
  const [scheduleModalOpen, setScheduleModalOpen] = useState(false);
  const [newInterview, setNewInterview] = useState<InterviewPayload>({
    application_id: '',
    interview_date: '',
    interview_type: 'TECHNICAL',
    interviewer: 'Technical Hiring Team',
    feedback: '',
    rating: undefined
  });
  const [scheduling, setScheduling] = useState(false);

  // Feedback Modal
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);
  const [selectedInterview, setSelectedInterview] = useState<Interview | null>(null);
  const [feedbackRating, setFeedbackRating] = useState<number>(4);
  const [feedbackNotes, setFeedbackNotes] = useState<string>('');
  const [submittingFeedback, setSubmittingFeedback] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [intList, appList] = await Promise.all([
        pipelineService.getInterviews(),
        pipelineService.getApplications()
      ]);
      setInterviews(intList);
      setApplications(appList);
      if (appList.length > 0 && !newInterview.application_id) {
        setNewInterview(prev => ({ ...prev, application_id: appList[0].id }));
      }
    } catch (err: any) {
      console.error('Failed to load interviews:', err);
      setError(err?.response?.data?.detail || 'Failed to load interviews');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newInterview.application_id || !newInterview.interview_date) {
      setError('Please select an applicant and date/time.');
      return;
    }

    try {
      setScheduling(true);
      setError(null);
      await pipelineService.scheduleInterview(newInterview);
      setSuccessMessage('Interview scheduled successfully!');
      setScheduleModalOpen(false);
      fetchData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to schedule interview');
    } finally {
      setScheduling(false);
    }
  };

  const handleOpenFeedback = (interview: Interview) => {
    setSelectedInterview(interview);
    setFeedbackRating(interview.rating || 4);
    setFeedbackNotes(interview.feedback || '');
    setFeedbackModalOpen(true);
  };

  const handleSubmitFeedback = async () => {
    if (!selectedInterview) return;
    try {
      setSubmittingFeedback(true);
      await pipelineService.updateInterview(selectedInterview.id, {
        status: 'COMPLETED',
        rating: feedbackRating,
        feedback: feedbackNotes
      });
      setSuccessMessage('Interview feedback recorded successfully.');
      setFeedbackModalOpen(false);
      fetchData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to submit feedback');
    } finally {
      setSubmittingFeedback(false);
    }
  };

  const handleCancelInterview = async (id: string) => {
    if (!window.confirm('Are you sure you want to cancel this interview?')) return;
    try {
      await pipelineService.updateInterview(id, { status: 'CANCELLED' });
      fetchData();
    } catch (err: any) {
      setError('Failed to cancel interview');
    }
  };

  const filteredInterviews = useMemo(() => {
    return interviews.filter(i => {
      if (statusFilter !== 'ALL' && i.status !== statusFilter) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const cand = i.candidate_name?.toLowerCase() || '';
        const role = i.job_title?.toLowerCase() || '';
        const interviewer = i.interviewer?.toLowerCase() || '';
        if (!cand.includes(q) && !role.includes(q) && !interviewer.includes(q)) return false;
      }
      return true;
    });
  }, [interviews, statusFilter, searchQuery]);

  const stats = useMemo(() => {
    return {
      total: interviews.length,
      scheduled: interviews.filter(i => i.status === 'SCHEDULED').length,
      completed: interviews.filter(i => i.status === 'COMPLETED').length,
      cancelled: interviews.filter(i => i.status === 'CANCELLED').length,
    };
  }, [interviews]);

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Calendar className="w-6 h-6 text-brand-400" />
            <h1 className="text-2xl font-bold text-white tracking-tight">
              Interview Scheduling & Feedback
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Coordinate technical and behavioral screening rounds, log interviewer ratings, and submit evaluations.
          </p>
        </div>

        <button
          onClick={() => setScheduleModalOpen(true)}
          className="btn-primary text-xs flex items-center space-x-1.5 shadow-lg shadow-brand-500/20"
        >
          <Plus className="w-4 h-4" />
          <span>Schedule New Interview</span>
        </button>
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

      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card p-4">
          <span className="text-slate-400 text-xs font-medium">Total Interviews</span>
          <div className="text-2xl font-bold text-white mt-1">{stats.total}</div>
        </div>
        <div className="card p-4">
          <span className="text-slate-400 text-xs font-medium">Upcoming / Scheduled</span>
          <div className="text-2xl font-bold text-amber-400 mt-1">{stats.scheduled}</div>
        </div>
        <div className="card p-4">
          <span className="text-slate-400 text-xs font-medium">Completed Evaluations</span>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{stats.completed}</div>
        </div>
        <div className="card p-4">
          <span className="text-slate-400 text-xs font-medium">Cancelled / No-Show</span>
          <div className="text-2xl font-bold text-slate-500 mt-1">{stats.cancelled}</div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
        <div className="flex items-center space-x-2">
          {['ALL', 'SCHEDULED', 'COMPLETED', 'CANCELLED'].map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition ${
                statusFilter === s
                  ? 'bg-brand-600 text-white shadow-md shadow-brand-500/20'
                  : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        <div className="relative sm:w-72">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search candidate, role, interviewer..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input pl-9 text-xs w-full"
          />
        </div>
      </div>

      {/* Interview Cards List */}
      {loading ? (
        <div className="p-12 text-center text-slate-400">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-brand-400 mb-2" />
          <p className="text-xs">Loading scheduled interviews...</p>
        </div>
      ) : filteredInterviews.length === 0 ? (
        <div className="card p-12 text-center space-y-3">
          <Calendar className="w-8 h-8 text-slate-600 mx-auto" />
          <h3 className="text-sm font-semibold text-white">No Interviews Found</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            {statusFilter !== 'ALL'
              ? `There are no interviews with status "${statusFilter}".`
              : 'No interviews have been scheduled yet. Click "Schedule New Interview" to arrange one.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredInterviews.map((item) => (
            <div
              key={item.id}
              className="card p-5 hover:border-slate-700 transition flex flex-col justify-between space-y-4"
            >
              <div>
                {/* Top Badge and Date */}
                <div className="flex items-center justify-between gap-2">
                  <span className={`px-2 py-0.5 rounded text-2xs font-bold uppercase tracking-wider ${
                    item.status === 'COMPLETED'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      : item.status === 'SCHEDULED'
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      : 'bg-slate-800 text-slate-400'
                  }`}>
                    {item.status}
                  </span>

                  <div className="flex items-center space-x-1 text-2xs text-slate-400">
                    <Clock className="w-3 h-3 text-slate-500" />
                    <span>{new Date(item.interview_date).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}</span>
                  </div>
                </div>

                {/* Candidate & Role */}
                <div className="mt-3">
                  <div className="text-base font-bold text-white">
                    {item.candidate_name || 'Candidate'}
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5">
                    Role: <span className="text-slate-200 font-medium">{item.job_title}</span>
                  </div>
                </div>

                {/* Interviewer & Type */}
                <div className="mt-3 pt-3 border-t border-slate-800/80 flex flex-wrap gap-2 text-2xs text-slate-400">
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-brand-300 font-medium">
                    {item.interview_type} ROUND
                  </span>
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    Panel: {item.interviewer}
                  </span>
                </div>

                {/* Completed Rating & Feedback */}
                {item.status === 'COMPLETED' && (
                  <div className="mt-3 bg-slate-950/60 p-3 rounded-xl border border-slate-800/80 space-y-1.5">
                    <div className="flex items-center space-x-1">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <Star
                          key={star}
                          className={`w-3.5 h-3.5 ${
                            (item.rating || 0) >= star
                              ? 'text-amber-400 fill-amber-400'
                              : 'text-slate-600'
                          }`}
                        />
                      ))}
                      <span className="text-2xs font-bold text-slate-300 ml-1.5">
                        {item.rating}/5 Rating
                      </span>
                    </div>
                    {item.feedback && (
                      <p className="text-2xs text-slate-300 italic">
                        "{item.feedback}"
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
                {item.candidate_id ? (
                  <Link
                    to={`/candidates/${item.candidate_id}`}
                    className="text-brand-400 hover:text-brand-300 font-medium flex items-center space-x-1"
                  >
                    <span>View Dossier</span>
                    <ChevronRight className="w-3 h-3" />
                  </Link>
                ) : <span />}

                <div className="flex items-center space-x-2">
                  {item.status === 'SCHEDULED' && (
                    <>
                      <button
                        onClick={() => handleOpenFeedback(item)}
                        className="btn-primary text-2xs py-1 px-2.5 flex items-center space-x-1"
                      >
                        <CheckCircle2 className="w-3 h-3" />
                        <span>Log Feedback</span>
                      </button>
                      <button
                        onClick={() => handleCancelInterview(item.id)}
                        className="px-2 py-1 rounded-lg text-2xs text-rose-400 hover:bg-rose-500/10 border border-rose-500/20"
                      >
                        Cancel
                      </button>
                    </>
                  )}
                  {item.status === 'COMPLETED' && (
                    <button
                      onClick={() => handleOpenFeedback(item)}
                      className="btn-secondary text-2xs py-1 px-2.5"
                    >
                      Update Evaluation
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Schedule Modal */}
      {scheduleModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <form
            onSubmit={handleSchedule}
            className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl animate-fade-in"
          >
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <Calendar className="w-5 h-5 text-brand-400" />
              <span>Schedule Candidate Interview</span>
            </h3>

            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">Select Applicant & Role</label>
              <select
                value={newInterview.application_id}
                onChange={(e) => setNewInterview({ ...newInterview, application_id: e.target.value })}
                className="input text-xs w-full"
                required
              >
                {applications.map((app) => (
                  <option key={app.id} value={app.id}>
                    {app.candidate?.name} &bull; {app.job?.title} ({app.match_score.toFixed(0)}% fit)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">Interview Round Type</label>
              <select
                value={newInterview.interview_type}
                onChange={(e) => setNewInterview({ ...newInterview, interview_type: e.target.value })}
                className="input text-xs w-full"
              >
                <option value="SCREENING">Initial Screening</option>
                <option value="TECHNICAL">Technical Deep-Dive</option>
                <option value="BEHAVIORAL">Behavioral & Culture Fit</option>
                <option value="FINAL">Executive / Final Round</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">Date & Time</label>
              <input
                type="datetime-local"
                value={newInterview.interview_date}
                onChange={(e) => setNewInterview({ ...newInterview, interview_date: e.target.value })}
                className="input text-xs w-full"
                required
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">Interviewer Panel</label>
              <input
                type="text"
                value={newInterview.interviewer}
                onChange={(e) => setNewInterview({ ...newInterview, interviewer: e.target.value })}
                placeholder="e.g. Sarah Jenkins (Tech Lead) & David Wu"
                className="input text-xs w-full"
                required
              />
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setScheduleModalOpen(false)}
                disabled={scheduling}
                className="btn-secondary text-xs"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={scheduling}
                className="btn-primary text-xs flex items-center space-x-1.5"
              >
                {scheduling ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Calendar className="w-3.5 h-3.5" />}
                <span>Confirm & Schedule</span>
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Log Feedback Modal */}
      {feedbackModalOpen && selectedInterview && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl animate-fade-in">
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <Star className="w-5 h-5 text-amber-400" />
              <span>Interview Feedback & Rating</span>
            </h3>

            <p className="text-xs text-slate-300">
              Candidate: <strong className="text-white">{selectedInterview.candidate_name}</strong> &bull; {selectedInterview.job_title}
            </p>

            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-2">Overall Candidate Rating</label>
              <div className="flex items-center space-x-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setFeedbackRating(star)}
                    className="p-1 hover:scale-110 transition"
                  >
                    <Star
                      className={`w-6 h-6 ${
                        feedbackRating >= star
                          ? 'text-amber-400 fill-amber-400'
                          : 'text-slate-600'
                      }`}
                    />
                  </button>
                ))}
                <span className="text-xs font-bold text-slate-200 ml-2">
                  {feedbackRating} of 5 Stars
                </span>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">Interviewer Notes & Synthesis</label>
              <textarea
                value={feedbackNotes}
                onChange={(e) => setFeedbackNotes(e.target.value)}
                placeholder="Enter feedback on coding proficiency, communication, algorithmic problem solving, and architecture..."
                rows={4}
                className="input text-xs w-full resize-none"
              />
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setFeedbackModalOpen(false)}
                disabled={submittingFeedback}
                className="btn-secondary text-xs"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSubmitFeedback}
                disabled={submittingFeedback}
                className="btn-primary text-xs flex items-center space-x-1.5"
              >
                {submittingFeedback ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
                <span>Save Evaluation</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Interviews;
