import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { 
  Bell, 
  Clock, 
  Phone, 
  Mail, 
  Linkedin, 
  Users, 
  CheckCircle2, 
  AlertCircle, 
  Plus, 
  RefreshCw, 
  Trash2, 
  Search,
  ChevronRight,
  CalendarCheck
} from 'lucide-react';
import { pipelineService, FollowupPayload } from '../services/pipelineService';
import { candidateService } from '../services/candidateService';
import { Followup, Candidate } from '../types';

export const Followups: React.FC = () => {
  const [followups, setFollowups] = useState<Followup[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // New Reminder Modal
  const [modalOpen, setModalOpen] = useState(false);
  const [newFollowup, setNewFollowup] = useState<FollowupPayload>({
    candidate_id: '',
    followup_date: '',
    method: 'CALL',
    notes: ''
  });
  const [saving, setSaving] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [fList, cList] = await Promise.all([
        pipelineService.getFollowups(),
        candidateService.getCandidates()
      ]);
      setFollowups(fList);
      setCandidates(cList);
      if (cList.length > 0 && !newFollowup.candidate_id) {
        setNewFollowup(prev => ({ ...prev, candidate_id: cList[0].id }));
      }
    } catch (err: any) {
      console.error('Failed to load follow-ups:', err);
      setError(err?.response?.data?.detail || 'Failed to load follow-up reminders');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateFollowup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFollowup.candidate_id || !newFollowup.followup_date) {
      setError('Please select a candidate and target follow-up date.');
      return;
    }

    try {
      setSaving(true);
      setError(null);
      await pipelineService.createFollowup(newFollowup);
      setSuccessMessage('Follow-up reminder set successfully!');
      setModalOpen(false);
      setNewFollowup({
        candidate_id: candidates[0]?.id || '',
        followup_date: '',
        method: 'CALL',
        notes: ''
      });
      fetchData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to create follow-up reminder');
    } finally {
      setSaving(false);
    }
  };

  const handleToggleComplete = async (f: Followup) => {
    const nextStatus = f.status === 'COMPLETED' ? 'PENDING' : 'COMPLETED';
    try {
      await pipelineService.updateFollowup(f.id, { status: nextStatus });
      fetchData();
    } catch (err: any) {
      setError('Failed to update follow-up status');
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this reminder?')) return;
    try {
      await pipelineService.deleteFollowup(id);
      fetchData();
    } catch (err: any) {
      setError('Failed to delete reminder');
    }
  };

  const filteredFollowups = useMemo(() => {
    return followups.filter(f => {
      if (statusFilter !== 'ALL' && f.status !== statusFilter) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const cand = f.candidate_name?.toLowerCase() || '';
        const notes = f.notes?.toLowerCase() || '';
        if (!cand.includes(q) && !notes.includes(q)) return false;
      }
      return true;
    });
  }, [followups, statusFilter, searchQuery]);

  const stats = useMemo(() => {
    return {
      total: followups.length,
      overdue: followups.filter(f => f.status === 'OVERDUE').length,
      pending: followups.filter(f => f.status === 'PENDING').length,
      completed: followups.filter(f => f.status === 'COMPLETED').length,
    };
  }, [followups]);

  const getMethodIcon = (method: string) => {
    switch (method.toUpperCase()) {
      case 'CALL':
        return <Phone className="w-3.5 h-3.5 text-emerald-400" />;
      case 'EMAIL':
        return <Mail className="w-3.5 h-3.5 text-cyan-400" />;
      case 'LINKEDIN':
        return <Linkedin className="w-3.5 h-3.5 text-blue-400" />;
      case 'MEETING':
        return <Users className="w-3.5 h-3.5 text-indigo-400" />;
      default:
        return <Clock className="w-3.5 h-3.5 text-slate-400" />;
    }
  };

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Bell className="w-6 h-6 text-brand-400" />
            <h1 className="text-2xl font-bold text-white tracking-tight">
              Recruiter Follow-up Reminders
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Stay on top of candidate outreach, check-ins, offer negotiations, and scheduled touchpoints.
          </p>
        </div>

        <button
          onClick={() => setModalOpen(true)}
          className="btn-primary text-xs flex items-center space-x-1.5 shadow-lg shadow-brand-500/20"
        >
          <Plus className="w-4 h-4" />
          <span>New Follow-up Reminder</span>
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
          <span className="text-slate-400 text-xs font-medium">Total Reminders</span>
          <div className="text-2xl font-bold text-white mt-1">{stats.total}</div>
        </div>
        <div className="card p-4">
          <span className="text-slate-400 text-xs font-medium">Overdue</span>
          <div className="text-2xl font-bold text-rose-400 mt-1">{stats.overdue}</div>
        </div>
        <div className="card p-4">
          <span className="text-slate-400 text-xs font-medium">Due / Pending</span>
          <div className="text-2xl font-bold text-amber-400 mt-1">{stats.pending}</div>
        </div>
        <div className="card p-4">
          <span className="text-slate-400 text-xs font-medium">Completed</span>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{stats.completed}</div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
        <div className="flex items-center space-x-2">
          {['ALL', 'OVERDUE', 'PENDING', 'COMPLETED'].map((s) => (
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
            placeholder="Search candidate or note..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input pl-9 text-xs w-full"
          />
        </div>
      </div>

      {/* Follow-up Cards List */}
      {loading ? (
        <div className="p-12 text-center text-slate-400">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-brand-400 mb-2" />
          <p className="text-xs">Loading follow-up reminders...</p>
        </div>
      ) : filteredFollowups.length === 0 ? (
        <div className="card p-12 text-center space-y-3">
          <CalendarCheck className="w-8 h-8 text-slate-600 mx-auto" />
          <h3 className="text-sm font-semibold text-white">No Reminders Found</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            {statusFilter !== 'ALL'
              ? `There are no follow-ups marked as "${statusFilter}".`
              : 'You have no scheduled follow-ups. Click "New Follow-up Reminder" to create one.'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredFollowups.map((f) => (
            <div
              key={f.id}
              className={`card p-4 hover:border-slate-700 transition flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                f.status === 'COMPLETED' ? 'opacity-60 bg-slate-900/40' : ''
              }`}
            >
              {/* Left: Checkmark toggle, Candidate, Method, Date */}
              <div className="flex items-start space-x-3.5">
                <button
                  onClick={() => handleToggleComplete(f)}
                  className={`mt-0.5 w-5 h-5 rounded-lg border flex items-center justify-center transition flex-shrink-0 ${
                    f.status === 'COMPLETED'
                      ? 'bg-emerald-500 border-emerald-500 text-white'
                      : 'border-slate-700 bg-slate-800 text-transparent hover:border-brand-500'
                  }`}
                  title={f.status === 'COMPLETED' ? 'Mark Pending' : 'Mark Complete'}
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                </button>

                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <Link
                      to={`/candidates/${f.candidate_id}`}
                      className="text-sm font-bold text-white hover:text-brand-300 transition"
                    >
                      {f.candidate_name || 'Candidate'}
                    </Link>

                    {/* Method Tag */}
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-2xs font-semibold bg-slate-800 border border-slate-700 text-slate-300">
                      {getMethodIcon(f.method)}
                      <span>{f.method}</span>
                    </span>

                    {/* Status Badge */}
                    <span className={`px-2 py-0.5 rounded text-2xs font-bold uppercase tracking-wider ${
                      f.status === 'OVERDUE'
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        : f.status === 'PENDING'
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                        : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    }`}>
                      {f.status}
                    </span>
                  </div>

                  {f.notes && (
                    <p className="text-xs text-slate-300 leading-relaxed max-w-2xl">
                      {f.notes}
                    </p>
                  )}

                  <div className="flex items-center space-x-2 text-2xs text-slate-500">
                    <Clock className="w-3 h-3 text-slate-600" />
                    <span>Due: {new Date(f.followup_date).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}</span>
                  </div>
                </div>
              </div>

              {/* Right: Actions */}
              <div className="flex items-center space-x-2 self-end sm:self-center">
                <Link
                  to={`/candidates/${f.candidate_id}`}
                  className="btn-secondary text-2xs py-1 px-2.5 flex items-center space-x-1"
                >
                  <span>Profile</span>
                  <ChevronRight className="w-3 h-3" />
                </Link>
                <button
                  onClick={() => handleDelete(f.id)}
                  className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition"
                  title="Delete Reminder"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal: New Follow-up Reminder */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <form
            onSubmit={handleCreateFollowup}
            className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl animate-fade-in"
          >
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <Bell className="w-5 h-5 text-brand-400" />
              <span>Schedule Follow-up Reminder</span>
            </h3>

            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">Candidate</label>
              <select
                value={newFollowup.candidate_id}
                onChange={(e) => setNewFollowup({ ...newFollowup, candidate_id: e.target.value })}
                className="input text-xs w-full"
                required
              >
                {candidates.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} &bull; {c.location} ({c.total_experience}y exp)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">Outreach Channel / Method</label>
              <select
                value={newFollowup.method}
                onChange={(e) => setNewFollowup({ ...newFollowup, method: e.target.value })}
                className="input text-xs w-full"
              >
                <option value="CALL">Phone Call</option>
                <option value="EMAIL">Email Outreach</option>
                <option value="LINKEDIN">LinkedIn InMail</option>
                <option value="MEETING">Video Sync / Coffee Chat</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">Target Date & Time</label>
              <input
                type="datetime-local"
                value={newFollowup.followup_date}
                onChange={(e) => setNewFollowup({ ...newFollowup, followup_date: e.target.value })}
                className="input text-xs w-full"
                required
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">Follow-up Objective / Note</label>
              <textarea
                value={newFollowup.notes}
                onChange={(e) => setNewFollowup({ ...newFollowup, notes: e.target.value })}
                placeholder="e.g. Inquire about notice period, current compensation and counter-offer status..."
                rows={3}
                className="input text-xs w-full resize-none"
              />
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                disabled={saving}
                className="btn-secondary text-xs"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving}
                className="btn-primary text-xs flex items-center space-x-1.5"
              >
                {saving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Bell className="w-3.5 h-3.5" />}
                <span>Set Reminder</span>
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default Followups;
