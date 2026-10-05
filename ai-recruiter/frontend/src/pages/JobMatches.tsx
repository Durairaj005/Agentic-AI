import React, { useState, useEffect, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Sparkles, 
  RefreshCw, 
  Sliders, 
  Search, 
  Filter, 
  ChevronRight, 
  Award, 
  CheckCircle2, 
  XCircle, 
  AlertCircle,
  Briefcase, 
  GraduationCap, 
  MapPin, 
  TrendingUp,
  Clock,
  ShieldCheck,
  Eye,
  SlidersHorizontal,
  Info
} from 'lucide-react';
import { jobService } from '../services/jobService';
import { matchService, MatchWeightPayload } from '../services/matchService';
import { Job, CandidateMatchResult, RankedMatchesResponse } from '../types';
import { ScoreBreakdownModal } from '../components/candidates/ScoreBreakdownModal';

export const JobMatches: React.FC = () => {
  const { id: jobId } = useParams<{ id: string }>();
  
  const [job, setJob] = useState<Job | null>(null);
  const [matchData, setMatchData] = useState<RankedMatchesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [matchingInProgress, setMatchingInProgress] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Filters & Sorting
  const [searchQuery, setSearchQuery] = useState('');
  const [minScore, setMinScore] = useState<number>(0);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [sortBy, setSortBy] = useState<'score' | 'experience'>('score');

  // Modal & Weight Customizer states
  const [selectedMatch, setSelectedMatch] = useState<CandidateMatchResult | null>(null);
  const [showWeightPanel, setShowWeightPanel] = useState(false);
  const [weights, setWeights] = useState<MatchWeightPayload>({
    weight_required_skills: 0.40,
    weight_preferred_skills: 0.20,
    weight_experience: 0.20,
    weight_education: 0.10,
    weight_semantic: 0.10,
  });

  const fetchData = async () => {
    if (!jobId) return;
    try {
      setLoading(true);
      setError(null);
      const [jobRes, matchesRes] = await Promise.all([
        jobService.getJob(jobId),
        matchService.getRankedMatches(jobId, { sort_by: sortBy })
      ]);
      setJob(jobRes);
      setMatchData(matchesRes);
      if (matchesRes.weight_config) {
        setWeights(matchesRes.weight_config);
      }
    } catch (err: any) {
      console.error('Failed to load job matches:', err);
      setError(err?.response?.data?.detail || 'Failed to load matching candidates');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [jobId, sortBy]);

  const handleRunMatching = async () => {
    if (!jobId) return;
    try {
      setMatchingInProgress(true);
      setError(null);
      setSuccessMessage(null);
      const res = await matchService.runMatching(jobId, weights);
      setSuccessMessage(res.message || `Matched ${res.evaluated_count} candidates successfully.`);
      const matchesRes = await matchService.getRankedMatches(jobId, { sort_by: sortBy });
      setMatchData(matchesRes);
    } catch (err: any) {
      console.error('Failed running match engine:', err);
      setError(err?.response?.data?.detail || 'Failed to execute matching algorithm');
    } finally {
      setMatchingInProgress(false);
    }
  };

  // Filtered candidate matches
  const filteredMatches = useMemo(() => {
    if (!matchData?.matches) return [];

    return matchData.matches.filter(m => {
      // Score filter
      if (m.overall_score < minScore) return false;

      // Status filter
      if (statusFilter !== 'ALL' && m.status !== statusFilter) return false;

      // Search query filter (name, location, or skills)
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const nameMatch = m.candidate.name.toLowerCase().includes(q);
        const locMatch = m.candidate.location?.toLowerCase().includes(q);
        const skillMatch = m.candidate.skills?.some(s => s.skill.toLowerCase().includes(q));
        if (!nameMatch && !locMatch && !skillMatch) return false;
      }

      return true;
    });
  }, [matchData, minScore, statusFilter, searchQuery]);

  const stats = useMemo(() => {
    const list = matchData?.matches || [];
    const high = list.filter(m => m.overall_score >= 80).length;
    const mid = list.filter(m => m.overall_score >= 60 && m.overall_score < 80).length;
    const topScore = list.length > 0 ? Math.max(...list.map(m => m.overall_score)) : 0;
    return {
      total: list.length,
      high,
      mid,
      topScore
    };
  }, [matchData]);

  const getScoreColor = (score: number) => {
    if (score >= 85) return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
    if (score >= 70) return 'text-brand-400 bg-brand-500/10 border-brand-500/30';
    if (score >= 50) return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
  };

  const getProgressColor = (score: number) => {
    if (score >= 85) return 'bg-emerald-500';
    if (score >= 70) return 'bg-brand-500';
    if (score >= 50) return 'bg-amber-500';
    return 'bg-rose-500';
  };

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <Link
            to={`/jobs/${jobId}`}
            className="inline-flex items-center text-xs font-medium text-slate-400 hover:text-brand-400 mb-2 transition"
          >
            <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back to Requisition Details
          </Link>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-bold text-white tracking-tight">
              AI Candidate Matches: {job?.title || 'Loading...'}
            </h1>
            <span className="px-2.5 py-1 rounded-md text-xs font-semibold bg-brand-500/20 text-brand-300 border border-brand-500/30">
              {job?.company}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 flex items-center gap-2">
            <MapPin className="w-3.5 h-3.5 text-slate-500" /> {job?.location} &bull; 
            <Briefcase className="w-3.5 h-3.5 text-slate-500 ml-1" /> {job?.experience_min}-{job?.experience_max} yrs experience required
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowWeightPanel(!showWeightPanel)}
            className={`btn-secondary text-xs flex items-center space-x-1.5 ${showWeightPanel ? 'border-brand-500/50 bg-brand-500/10 text-brand-300' : ''}`}
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>Customize Weights</span>
          </button>

          <button
            onClick={handleRunMatching}
            disabled={matchingInProgress}
            className="btn-primary text-xs flex items-center space-x-2 shadow-lg shadow-brand-500/20"
          >
            <Sparkles className={`w-3.5 h-3.5 ${matchingInProgress ? 'animate-spin' : ''}`} />
            <span>{matchingInProgress ? 'Calculating Scores...' : 'Re-Run AI Matching'}</span>
          </button>
        </div>
      </div>

      {/* Responsible AI Disclaimer Banner */}
      <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-start space-x-3 text-xs text-slate-400">
        <ShieldCheck className="w-4 h-4 text-brand-400 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-200">Explainable Decision Support:</span> Match scores are computed deterministically across 5 transparent factors: Required Skills (40%), Preferred Skills (20%), Experience Alignment (20%), Education Match (10%), and Semantic Context (10%). AI suggestions assist recruiter judgment and should never replace human evaluation.
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMessage && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Weight Configuration Panel (Collapsible) */}
      {showWeightPanel && (
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl space-y-4 animate-fade-in">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-brand-400" />
              <h3 className="text-sm font-semibold text-white">Adjust Matching Algorithm Weights</h3>
            </div>
            <span className="text-xs text-slate-400">
              Total Weight: <strong className="text-brand-400">{Math.round((
                (weights.weight_required_skills || 0) +
                (weights.weight_preferred_skills || 0) +
                (weights.weight_experience || 0) +
                (weights.weight_education || 0) +
                (weights.weight_semantic || 0)
              ) * 100)}%</strong>
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 text-xs">
            <div>
              <label className="text-slate-300 font-medium block mb-1">
                Required Skills: {Math.round((weights.weight_required_skills || 0) * 100)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weights.weight_required_skills}
                onChange={(e) => setWeights({ ...weights, weight_required_skills: parseFloat(e.target.value) })}
                className="w-full accent-brand-500"
              />
            </div>
            <div>
              <label className="text-slate-300 font-medium block mb-1">
                Preferred Skills: {Math.round((weights.weight_preferred_skills || 0) * 100)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weights.weight_preferred_skills}
                onChange={(e) => setWeights({ ...weights, weight_preferred_skills: parseFloat(e.target.value) })}
                className="w-full accent-brand-500"
              />
            </div>
            <div>
              <label className="text-slate-300 font-medium block mb-1">
                Experience: {Math.round((weights.weight_experience || 0) * 100)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weights.weight_experience}
                onChange={(e) => setWeights({ ...weights, weight_experience: parseFloat(e.target.value) })}
                className="w-full accent-brand-500"
              />
            </div>
            <div>
              <label className="text-slate-300 font-medium block mb-1">
                Education: {Math.round((weights.weight_education || 0) * 100)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weights.weight_education}
                onChange={(e) => setWeights({ ...weights, weight_education: parseFloat(e.target.value) })}
                className="w-full accent-brand-500"
              />
            </div>
            <div>
              <label className="text-slate-300 font-medium block mb-1">
                Semantic Fit: {Math.round((weights.weight_semantic || 0) * 100)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weights.weight_semantic}
                onChange={(e) => setWeights({ ...weights, weight_semantic: parseFloat(e.target.value) })}
                className="w-full accent-brand-500"
              />
            </div>
          </div>

          <div className="flex justify-end space-x-2 pt-2">
            <button
              onClick={() => setWeights({
                weight_required_skills: 0.40,
                weight_preferred_skills: 0.20,
                weight_experience: 0.20,
                weight_education: 0.10,
                weight_semantic: 0.10,
              })}
              className="px-3 py-1.5 rounded-lg border border-slate-700 text-slate-400 hover:text-white text-xs"
            >
              Reset Defaults
            </button>
            <button
              onClick={handleRunMatching}
              disabled={matchingInProgress}
              className="btn-primary text-xs py-1.5"
            >
              Apply Weights & Recalculate
            </button>
          </div>
        </div>
      )}

      {/* KPI Stats Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card p-4">
          <span className="text-slate-400 text-xs font-medium">Evaluated Candidates</span>
          <div className="text-2xl font-bold text-white mt-1">{stats.total}</div>
          <span className="text-2xs text-slate-500 mt-1 block">In talent database</span>
        </div>
        <div className="card p-4">
          <span className="text-slate-400 text-xs font-medium">Strong Fits (&ge; 80%)</span>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{stats.high}</div>
          <span className="text-2xs text-slate-500 mt-1 block">High interview potential</span>
        </div>
        <div className="card p-4">
          <span className="text-slate-400 text-xs font-medium">Moderate Fits (60-79%)</span>
          <div className="text-2xl font-bold text-brand-400 mt-1">{stats.mid}</div>
          <span className="text-2xs text-slate-500 mt-1 block">Review for partial match</span>
        </div>
        <div className="card p-4">
          <span className="text-slate-400 text-xs font-medium">Highest Fit Score</span>
          <div className="text-2xl font-bold text-white mt-1">
            {stats.topScore > 0 ? `${stats.topScore.toFixed(1)}%` : 'N/A'}
          </div>
          <span className="text-2xs text-slate-500 mt-1 block">Optimal candidate match</span>
        </div>
      </div>

      {/* Search, Filter & Sort Controls */}
      <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search candidate name, location, or skill..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input pl-9 text-xs"
          />
        </div>

        <div className="flex items-center space-x-2">
          {/* Min Score Filter */}
          <select
            value={minScore}
            onChange={(e) => setMinScore(Number(e.target.value))}
            className="input text-xs w-36"
          >
            <option value="0">All Scores</option>
            <option value="80">&ge; 80% Match</option>
            <option value="70">&ge; 70% Match</option>
            <option value="50">&ge; 50% Match</option>
          </select>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input text-xs w-36"
          >
            <option value="ALL">All Stages</option>
            <option value="NEW">New</option>
            <option value="SCREENING">Screening</option>
            <option value="SHORTLISTED">Shortlisted</option>
            <option value="INTERVIEW">Interview</option>
          </select>

          {/* Sort By */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'score' | 'experience')}
            className="input text-xs w-36"
          >
            <option value="score">Sort by Score</option>
            <option value="experience">Sort by Experience</option>
          </select>
        </div>
      </div>

      {/* Ranked Candidate Results */}
      {loading ? (
        <div className="p-12 text-center text-slate-400">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-brand-400 mb-2" />
          <p className="text-xs">Evaluating matching algorithms and scoring candidates...</p>
        </div>
      ) : filteredMatches.length === 0 ? (
        <div className="card p-12 text-center space-y-4">
          <div className="w-12 h-12 rounded-xl bg-slate-800 text-slate-400 flex items-center justify-center mx-auto">
            <Filter className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-white">No Matching Candidates Found</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            {stats.total === 0 
              ? 'No candidates have been evaluated for this requisition yet. Click "Re-Run AI Matching" to match all candidates.'
              : 'No candidates matched your search and filter criteria. Try lowering the minimum score or clearing filters.'}
          </p>
          {stats.total === 0 && (
            <button
              onClick={handleRunMatching}
              disabled={matchingInProgress}
              className="btn-primary text-xs mx-auto flex items-center space-x-2"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Evaluate Candidates Now</span>
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {filteredMatches.map((match, index) => {
            const { candidate, overall_score, explanation } = match;
            const rank = index + 1;

            return (
              <div
                key={candidate.id}
                className="card p-5 hover:border-slate-700 transition duration-200 relative overflow-hidden group"
              >
                {/* Score bar on left border */}
                <div 
                  className={`absolute left-0 top-0 bottom-0 w-1.5 ${getProgressColor(overall_score)}`} 
                />

                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  {/* Left: Rank, Name, Details */}
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-xl bg-slate-800/80 border border-slate-700 font-bold text-sm text-slate-300">
                      #{rank}
                    </div>

                    <div>
                      <div className="flex items-center space-x-2">
                        <Link
                          to={`/candidates/${candidate.id}`}
                          className="text-base font-bold text-white hover:text-brand-400 transition"
                        >
                          {candidate.name}
                        </Link>
                        <span className={`px-2 py-0.5 rounded text-2xs font-semibold uppercase tracking-wider ${
                          match.status === 'SHORTLISTED' 
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                            : 'bg-slate-800 text-slate-400'
                        }`}>
                          {match.status}
                        </span>
                      </div>

                      <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 mt-1">
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3 h-3 text-slate-500" />
                          {candidate.location}
                        </span>
                        <span>&bull;</span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-slate-500" />
                          {candidate.total_experience} Years Exp
                        </span>
                        <span>&bull;</span>
                        <span className="flex items-center gap-1">
                          <GraduationCap className="w-3 h-3 text-slate-500" />
                          {candidate.education_level}
                        </span>
                      </div>

                      {/* Natural Language Explanation Snippet */}
                      {explanation?.natural_language_explanation && (
                        <p className="text-xs text-slate-300 mt-2 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/80 line-clamp-2">
                          <span className="text-brand-400 font-medium">AI Rationale:</span> {explanation.natural_language_explanation}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Right: Big Score Pill & Factor Breakdown Bars */}
                  <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6 lg:justify-end">
                    {/* 5-Factor Mini Gauges */}
                    <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-2xs w-full sm:w-60">
                      <div>
                        <div className="flex justify-between text-slate-400">
                          <span>Req. Skills</span>
                          <span className="font-semibold text-slate-300">{Math.round(match.required_skills_score)}%</span>
                        </div>
                        <div className="w-full bg-slate-800 rounded-full h-1 mt-0.5">
                          <div className="bg-brand-500 h-1 rounded-full" style={{ width: `${match.required_skills_score}%` }} />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-slate-400">
                          <span>Pref. Skills</span>
                          <span className="font-semibold text-slate-300">{Math.round(match.preferred_skills_score)}%</span>
                        </div>
                        <div className="w-full bg-slate-800 rounded-full h-1 mt-0.5">
                          <div className="bg-indigo-500 h-1 rounded-full" style={{ width: `${match.preferred_skills_score}%` }} />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-slate-400">
                          <span>Experience</span>
                          <span className="font-semibold text-slate-300">{Math.round(match.experience_score)}%</span>
                        </div>
                        <div className="w-full bg-slate-800 rounded-full h-1 mt-0.5">
                          <div className="bg-emerald-500 h-1 rounded-full" style={{ width: `${match.experience_score}%` }} />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-slate-400">
                          <span>Semantic</span>
                          <span className="font-semibold text-slate-300">{Math.round(match.semantic_score)}%</span>
                        </div>
                        <div className="w-full bg-slate-800 rounded-full h-1 mt-0.5">
                          <div className="bg-cyan-500 h-1 rounded-full" style={{ width: `${match.semantic_score}%` }} />
                        </div>
                      </div>
                    </div>

                    {/* Overall Score Badge */}
                    <div className="flex flex-col items-center justify-center flex-shrink-0">
                      <div className={`px-4 py-2.5 rounded-xl border text-center font-bold text-xl ${getScoreColor(overall_score)}`}>
                        {overall_score.toFixed(1)}%
                        <span className="text-2xs block uppercase tracking-wider font-semibold opacity-80">Match</span>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex sm:flex-col gap-2 w-full sm:w-auto">
                      <button
                        onClick={() => setSelectedMatch(match)}
                        className="btn-secondary text-xs py-1.5 px-3 flex items-center justify-center space-x-1.5 flex-1"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Breakdown</span>
                      </button>
                      <Link
                        to={`/candidates/${candidate.id}`}
                        className="btn-secondary text-xs py-1.5 px-3 flex items-center justify-center space-x-1.5 flex-1 text-slate-300 hover:text-white"
                      >
                        <span>Profile</span>
                        <ChevronRight className="w-3 h-3" />
                      </Link>
                    </div>
                  </div>
                </div>

                {/* Bottom Skill Pills (Matched vs Missing) */}
                <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-wrap items-center gap-2">
                  <span className="text-2xs font-semibold text-slate-400 uppercase tracking-wider mr-1">Matched:</span>
                  {explanation?.matched_required_skills?.length > 0 ? (
                    explanation.matched_required_skills.map(s => (
                      <span key={s} className="px-2 py-0.5 rounded text-2xs font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 flex items-center gap-1">
                        <CheckCircle2 className="w-2.5 h-2.5" /> {s}
                      </span>
                    ))
                  ) : (
                    <span className="text-2xs text-slate-500">None</span>
                  )}

                  {explanation?.missing_required_skills?.length > 0 && (
                    <>
                      <span className="text-2xs font-semibold text-slate-400 uppercase tracking-wider ml-2 mr-1">Missing:</span>
                      {explanation.missing_required_skills.slice(0, 4).map(s => (
                        <span key={s} className="px-2 py-0.5 rounded text-2xs font-medium bg-rose-500/10 text-rose-300 border border-rose-500/20 flex items-center gap-1">
                          <XCircle className="w-2.5 h-2.5" /> {s}
                        </span>
                      ))}
                      {explanation.missing_required_skills.length > 4 && (
                        <span className="text-2xs text-slate-500">+{explanation.missing_required_skills.length - 4} more</span>
                      )}
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Detailed Score Breakdown Modal */}
      <ScoreBreakdownModal
        isOpen={!!selectedMatch}
        onClose={() => setSelectedMatch(null)}
        match={selectedMatch}
        jobTitle={job?.title}
      />
    </div>
  );
};

export default JobMatches;
