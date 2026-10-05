import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  GitCompare, 
  Sparkles, 
  Briefcase, 
  Users, 
  Check, 
  Minus, 
  AlertCircle, 
  RefreshCw, 
  Plus, 
  X, 
  ChevronRight, 
  Award,
  Layers,
  MapPin,
  Clock,
  GraduationCap
} from 'lucide-react';
import { comparisonService } from '../services/comparisonService';
import { candidateService } from '../services/candidateService';
import { jobService } from '../services/jobService';
import { ComparisonMatrixResponse, Candidate, Job } from '../types';

export const CandidateComparison: React.FC = () => {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>('');

  const [matrixData, setMatrixData] = useState<ComparisonMatrixResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [skillFilter, setSkillFilter] = useState<'ALL' | 'COMMON' | 'UNIQUE'>('ALL');

  useEffect(() => {
    Promise.all([
      candidateService.getCandidates(),
      jobService.getJobs()
    ]).then(([cList, jList]) => {
      setCandidates(cList);
      setJobs(jList);
      // Auto-select first 2 candidates for instant comparison
      if (cList.length >= 2) {
        setSelectedCandidateIds([cList[0].id, cList[1].id]);
      }
      if (jList.length > 0) {
        setSelectedJobId(jList[0].id);
      }
    }).catch(err => {
      console.error('Failed to initialize comparison data:', err);
    });
  }, []);

  const handleRunComparison = async () => {
    if (selectedCandidateIds.length < 2) {
      setError('Please select at least 2 candidates to compare.');
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const res = await comparisonService.compareCandidates(selectedCandidateIds, selectedJobId || undefined);
      setMatrixData(res);
    } catch (err: any) {
      console.error('Comparison error:', err);
      setError(err?.response?.data?.detail || 'Failed to compare candidates');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedCandidateIds.length >= 2) {
      handleRunComparison();
    }
  }, [selectedCandidateIds, selectedJobId]);

  const handleAddCandidate = (id: string) => {
    if (selectedCandidateIds.includes(id)) return;
    if (selectedCandidateIds.length >= 4) {
      alert('You can compare a maximum of 4 candidates simultaneously.');
      return;
    }
    setSelectedCandidateIds([...selectedCandidateIds, id]);
  };

  const handleRemoveCandidate = (id: string) => {
    if (selectedCandidateIds.length <= 2) {
      alert('Comparison requires at least 2 candidates.');
      return;
    }
    setSelectedCandidateIds(selectedCandidateIds.filter(cid => cid !== id));
  };

  const getScoreColor = (score?: number) => {
    if (score === undefined) return 'text-slate-400 border-slate-700 bg-slate-800';
    if (score >= 85) return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
    if (score >= 70) return 'text-brand-400 bg-brand-500/10 border-brand-500/30';
    if (score >= 50) return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
  };

  return (
    <div className="space-y-6 pb-16 animate-fade-in">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <GitCompare className="w-6 h-6 text-brand-400" />
            <h1 className="text-2xl font-bold text-white tracking-tight">
              Multi-Candidate Comparison Matrix
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Side-by-side evaluation of competencies, fit scores, skill overlaps, and AI comparative hiring verdicts.
          </p>
        </div>

        <button
          onClick={handleRunComparison}
          disabled={loading || selectedCandidateIds.length < 2}
          className="btn-primary text-xs flex items-center space-x-1.5 self-start md:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Matrix</span>
        </button>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Target Requisition & Candidate Selection Tray */}
      <div className="card p-5 space-y-4">
        <div className="flex flex-col md:flex-row gap-4 items-stretch md:items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-2">
            <Briefcase className="w-4 h-4 text-brand-400" />
            <span className="text-xs font-semibold text-slate-300">Target Role:</span>
            <select
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              className="input text-xs py-1.5 w-64"
            >
              <option value="">General Talent Comparison (No Job Target)</option>
              {jobs.map(j => (
                <option key={j.id} value={j.id}>{j.title} ({j.company})</option>
              ))}
            </select>
          </div>

          {/* Add candidate dropdown */}
          <div className="flex items-center space-x-2">
            <Plus className="w-4 h-4 text-slate-400" />
            <select
              onChange={(e) => {
                if (e.target.value) {
                  handleAddCandidate(e.target.value);
                  e.target.value = '';
                }
              }}
              className="input text-xs py-1.5 w-60"
              defaultValue=""
            >
              <option value="" disabled>Add Candidate to Matrix...</option>
              {candidates
                .filter(c => !selectedCandidateIds.includes(c.id))
                .map(c => (
                  <option key={c.id} value={c.id}>{c.name} ({c.total_experience}y exp)</option>
                ))}
            </select>
          </div>
        </div>

        {/* Selected Candidate Chips */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-2xs uppercase tracking-wider font-semibold text-slate-500 mr-1">
            Comparing ({selectedCandidateIds.length}/4):
          </span>
          {selectedCandidateIds.map(cid => {
            const cand = candidates.find(c => c.id === cid);
            return (
              <span
                key={cid}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-medium bg-slate-800 border border-slate-700 text-slate-200"
              >
                <span>{cand?.name || 'Candidate'}</span>
                <button
                  onClick={() => handleRemoveCandidate(cid)}
                  className="p-0.5 rounded-full hover:bg-slate-700 text-slate-400 hover:text-white"
                  title="Remove"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            );
          })}
        </div>
      </div>

      {loading && !matrixData ? (
        <div className="p-16 text-center text-slate-400 space-y-3">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto text-brand-400" />
          <p className="text-xs">Computing multi-candidate skill matrix and 5-factor alignment...</p>
        </div>
      ) : matrixData ? (
        <div className="space-y-6">
          {/* Side-by-Side Candidate Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {matrixData.candidates.map((item, idx) => {
              const { candidate, overall_match_score, unique_skills } = item;

              return (
                <div
                  key={candidate.id}
                  className="card p-5 flex flex-col justify-between space-y-4 hover:border-slate-700 transition"
                >
                  <div className="space-y-3">
                    {/* Header: Name and Rank */}
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="text-2xs font-bold text-slate-500 uppercase tracking-wider block">
                          Candidate #{idx + 1}
                        </span>
                        <Link
                          to={`/candidates/${candidate.id}`}
                          className="text-base font-bold text-white hover:text-brand-300 transition line-clamp-1"
                        >
                          {candidate.name}
                        </Link>
                      </div>

                      {overall_match_score !== undefined && (
                        <div className={`px-2.5 py-1 rounded-xl text-xs font-bold border ${getScoreColor(overall_match_score)}`}>
                          {overall_match_score.toFixed(1)}%
                        </div>
                      )}
                    </div>

                    {/* Metadata */}
                    <div className="space-y-1 text-xs text-slate-400">
                      <div className="flex items-center space-x-1.5">
                        <Clock className="w-3.5 h-3.5 text-slate-500" />
                        <span>{candidate.total_experience} Years Experience</span>
                      </div>
                      <div className="flex items-center space-x-1.5">
                        <MapPin className="w-3.5 h-3.5 text-slate-500" />
                        <span>{candidate.location}</span>
                      </div>
                      <div className="flex items-center space-x-1.5">
                        <GraduationCap className="w-3.5 h-3.5 text-slate-500" />
                        <span>{candidate.education_level}</span>
                      </div>
                    </div>

                    {/* 5-Factor Score Bars (if role matched) */}
                    {item.required_skills_score !== undefined && (
                      <div className="space-y-1.5 pt-2 border-t border-slate-800 text-2xs">
                        <div>
                          <div className="flex justify-between text-slate-400">
                            <span>Required Skills</span>
                            <span className="font-semibold text-slate-300">{Math.round(item.required_skills_score)}%</span>
                          </div>
                          <div className="w-full bg-slate-800 rounded-full h-1 mt-0.5">
                            <div className="bg-brand-500 h-1 rounded-full" style={{ width: `${item.required_skills_score}%` }} />
                          </div>
                        </div>

                        <div>
                          <div className="flex justify-between text-slate-400">
                            <span>Experience</span>
                            <span className="font-semibold text-slate-300">{Math.round(item.experience_score || 0)}%</span>
                          </div>
                          <div className="w-full bg-slate-800 rounded-full h-1 mt-0.5">
                            <div className="bg-emerald-500 h-1 rounded-full" style={{ width: `${item.experience_score || 0}%` }} />
                          </div>
                        </div>

                        <div>
                          <div className="flex justify-between text-slate-400">
                            <span>Semantic Fit</span>
                            <span className="font-semibold text-slate-300">{Math.round(item.semantic_score || 0)}%</span>
                          </div>
                          <div className="w-full bg-slate-800 rounded-full h-1 mt-0.5">
                            <div className="bg-cyan-500 h-1 rounded-full" style={{ width: `${item.semantic_score || 0}%` }} />
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Unique Skills Provided */}
                    {unique_skills.length > 0 && (
                      <div className="pt-2 border-t border-slate-800/80">
                        <span className="text-2xs uppercase tracking-wider font-semibold text-brand-400 block mb-1">
                          Unique Strengths:
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {unique_skills.slice(0, 4).map(s => (
                            <span key={s} className="px-1.5 py-0.5 rounded text-[10px] bg-brand-500/10 text-brand-300 border border-brand-500/20">
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="pt-3 border-t border-slate-800">
                    <Link
                      to={`/candidates/${candidate.id}`}
                      className="btn-secondary text-xs w-full py-1.5 flex items-center justify-center space-x-1"
                    >
                      <span>View Dossier</span>
                      <ChevronRight className="w-3 h-3" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>

          {/* AI Comparative Synthesis Box */}
          <div className="card p-6 bg-gradient-to-r from-slate-900 via-indigo-950/20 to-slate-900 border border-indigo-500/30 space-y-3">
            <div className="flex items-center space-x-2 text-sm font-bold text-white">
              <Sparkles className="w-4 h-4 text-brand-400" />
              <span>AI Comparative Decision Synthesis</span>
            </div>

            <div className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
              {matrixData.ai_comparative_synthesis}
            </div>
          </div>

          {/* Comprehensive Skills Overlap Matrix */}
          <div className="card p-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                  <Layers className="w-4 h-4 text-brand-400" />
                  <span>Technical Competency Overlap Matrix</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Side-by-side comparison across {matrixData.all_compared_skills.length} identified technical competencies
                </p>
              </div>

              {/* Filter Tabs */}
              <div className="flex items-center space-x-1.5">
                <button
                  onClick={() => setSkillFilter('ALL')}
                  className={`px-3 py-1 rounded-lg text-2xs font-semibold ${skillFilter === 'ALL' ? 'bg-brand-600 text-white' : 'bg-slate-800 text-slate-400'}`}
                >
                  All ({matrixData.all_compared_skills.length})
                </button>
                <button
                  onClick={() => setSkillFilter('COMMON')}
                  className={`px-3 py-1 rounded-lg text-2xs font-semibold ${skillFilter === 'COMMON' ? 'bg-brand-600 text-white' : 'bg-slate-800 text-slate-400'}`}
                >
                  Shared ({matrixData.common_skills.length})
                </button>
                <button
                  onClick={() => setSkillFilter('UNIQUE')}
                  className={`px-3 py-1 rounded-lg text-2xs font-semibold ${skillFilter === 'UNIQUE' ? 'bg-brand-600 text-white' : 'bg-slate-800 text-slate-400'}`}
                >
                  Differentiators
                </button>
              </div>
            </div>

            {/* Matrix Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="py-2.5 px-3 font-semibold">Technical Skill</th>
                    {matrixData.candidates.map(item => (
                      <th key={item.candidate.id} className="py-2.5 px-3 font-semibold text-center">
                        {item.candidate.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {matrixData.all_compared_skills
                    .filter(skill => {
                      if (skillFilter === 'COMMON') return matrixData.common_skills.includes(skill);
                      if (skillFilter === 'UNIQUE') return !matrixData.common_skills.includes(skill);
                      return true;
                    })
                    .map(skill => {
                      const isCommon = matrixData.common_skills.includes(skill);

                      return (
                        <tr key={skill} className="hover:bg-slate-850/50 transition">
                          <td className="py-2.5 px-3 font-medium text-slate-200 flex items-center space-x-2">
                            <span>{skill}</span>
                            {isCommon && (
                              <span className="text-[9px] bg-emerald-500/10 text-emerald-300 px-1.5 py-0.2 rounded border border-emerald-500/20 font-bold">
                                SHARED
                              </span>
                            )}
                          </td>
                          {matrixData.candidates.map(item => {
                            const hasSkill = matrixData.skill_matrix[skill]?.[item.candidate.id];

                            return (
                              <td key={item.candidate.id} className="py-2.5 px-3 text-center">
                                {hasSkill ? (
                                  <div className="w-6 h-6 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mx-auto">
                                    <Check className="w-3.5 h-3.5" />
                                  </div>
                                ) : (
                                  <div className="w-6 h-6 rounded-md bg-slate-800/40 text-slate-600 flex items-center justify-center mx-auto">
                                    <Minus className="w-3.5 h-3.5" />
                                  </div>
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default CandidateComparison;
