import React from 'react';
import { 
  X, 
  CheckCircle2, 
  AlertCircle, 
  Star, 
  Sparkles, 
  ShieldCheck, 
  Clock, 
  GraduationCap, 
  Cpu, 
  Layers 
} from 'lucide-react';
import { CandidateMatchResult } from '../../types';

interface ScoreBreakdownModalProps {
  isOpen: boolean;
  onClose: () => void;
  match: CandidateMatchResult | null;
  jobTitle?: string;
}

export const ScoreBreakdownModal: React.FC<ScoreBreakdownModalProps> = ({
  isOpen,
  onClose,
  match,
  jobTitle
}) => {
  if (!isOpen || !match) return null;

  const { candidate, explanation } = match;

  const getScoreColor = (score: number) => {
    if (score >= 85) return 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10';
    if (score >= 70) return 'text-brand-400 border-brand-500/40 bg-brand-500/10';
    if (score >= 50) return 'text-amber-400 border-amber-500/40 bg-amber-500/10';
    return 'text-rose-400 border-rose-500/40 bg-rose-500/10';
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden animate-fade-in my-8">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/60">
          <div>
            <div className="flex items-center space-x-2">
              <Sparkles className="w-5 h-5 text-brand-400" />
              <h2 className="text-lg font-bold text-white">AI Match Score Breakdown</h2>
            </div>
            <p className="text-xs text-slate-400">
              Candidate: <span className="text-slate-200 font-semibold">{candidate.name}</span> &bull; Role: <span className="text-brand-300 font-medium">{jobTitle || 'Target Requisition'}</span>
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-6 max-h-[80vh] overflow-y-auto">
          {/* Overall Score Banner */}
          <div className="flex items-center justify-between p-5 rounded-2xl bg-gradient-to-r from-slate-950 to-slate-900 border border-slate-800 shadow-inner">
            <div className="space-y-1">
              <div className="text-xs uppercase font-bold tracking-wider text-slate-400">
                Transparent Compatibility Score
              </div>
              <div className="text-xs text-slate-400">
                Calculated via 5-factor deterministic & semantic weighted model
              </div>
            </div>
            <div className={`px-5 py-2.5 rounded-2xl border-2 font-extrabold text-3xl tracking-tight ${getScoreColor(match.overall_score)}`}>
              {match.overall_score}%
            </div>
          </div>

          {/* 5-Factor Progress Bars */}
          <div className="space-y-3.5 bg-slate-950/60 p-5 rounded-2xl border border-slate-800">
            <div className="text-xs font-bold text-white uppercase tracking-wider flex items-center justify-between">
              <span>Scoring Factors Breakdown</span>
              <span className="text-slate-500 font-normal">Weights Normalized to 100%</span>
            </div>

            {/* Factor 1: Required Skills */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-300 flex items-center space-x-1.5 font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5 text-brand-400" />
                  <span>Required Skills (40% Weight)</span>
                </span>
                <span className="font-bold text-white">{match.required_skills_score}%</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-brand-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${match.required_skills_score}%` }}
                />
              </div>
            </div>

            {/* Factor 2: Preferred Skills */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-300 flex items-center space-x-1.5 font-medium">
                  <Star className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Preferred Skills (20% Weight)</span>
                </span>
                <span className="font-bold text-white">{match.preferred_skills_score}%</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-emerald-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${match.preferred_skills_score}%` }}
                />
              </div>
            </div>

            {/* Factor 3: Experience */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-300 flex items-center space-x-1.5 font-medium">
                  <Clock className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Experience Alignment (20% Weight)</span>
                </span>
                <span className="font-bold text-white">{match.experience_score}%</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-indigo-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${match.experience_score}%` }}
                />
              </div>
            </div>

            {/* Factor 4: Education */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-300 flex items-center space-x-1.5 font-medium">
                  <GraduationCap className="w-3.5 h-3.5 text-amber-400" />
                  <span>Education Tier (10% Weight)</span>
                </span>
                <span className="font-bold text-white">{match.education_score}%</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-amber-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${match.education_score}%` }}
                />
              </div>
            </div>

            {/* Factor 5: Semantic Vectors */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-300 flex items-center space-x-1.5 font-medium">
                  <Cpu className="w-3.5 h-3.5 text-sky-400" />
                  <span>Semantic Vector Alignment (10% Weight)</span>
                </span>
                <span className="font-bold text-white">{match.semantic_score}%</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-sky-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${match.semantic_score}%` }}
                />
              </div>
            </div>
          </div>

          {/* Matched vs Missing Skills Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Matched Required Skills */}
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
              <div className="text-xs font-bold text-emerald-300 flex items-center space-x-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Matched Required ({explanation.matched_required_skills.length})</span>
              </div>
              <div className="flex flex-wrap gap-1.5 min-h-[32px]">
                {explanation.matched_required_skills.length === 0 ? (
                  <span className="text-xs text-slate-500 italic">None matched</span>
                ) : (
                  explanation.matched_required_skills.map((s, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-medium"
                    >
                      {s}
                    </span>
                  ))
                )}
              </div>
            </div>

            {/* Missing Required Skills */}
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
              <div className="text-xs font-bold text-rose-300 flex items-center space-x-1.5">
                <AlertCircle className="w-4 h-4 text-rose-400" />
                <span>Missing Required ({explanation.missing_required_skills.length})</span>
              </div>
              <div className="flex flex-wrap gap-1.5 min-h-[32px]">
                {explanation.missing_required_skills.length === 0 ? (
                  <span className="text-xs text-emerald-400 font-medium">✓ None missing!</span>
                ) : (
                  explanation.missing_required_skills.map((s, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded-md bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-medium"
                    >
                      {s}
                    </span>
                  ))
                )}
              </div>
            </div>

            {/* Matched Preferred Skills */}
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
              <div className="text-xs font-bold text-brand-300 flex items-center space-x-1.5">
                <Star className="w-4 h-4 text-brand-400" />
                <span>Matched Preferred ({explanation.matched_preferred_skills.length})</span>
              </div>
              <div className="flex flex-wrap gap-1.5 min-h-[32px]">
                {explanation.matched_preferred_skills.length === 0 ? (
                  <span className="text-xs text-slate-500 italic">None matched</span>
                ) : (
                  explanation.matched_preferred_skills.map((s, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded-md bg-brand-500/10 border border-brand-500/30 text-brand-300 text-xs font-medium"
                    >
                      {s}
                    </span>
                  ))
                )}
              </div>
            </div>

            {/* Missing Preferred Skills */}
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
              <div className="text-xs font-bold text-slate-400 flex items-center space-x-1.5">
                <AlertCircle className="w-4 h-4 text-slate-500" />
                <span>Missing Preferred ({explanation.missing_preferred_skills.length})</span>
              </div>
              <div className="flex flex-wrap gap-1.5 min-h-[32px]">
                {explanation.missing_preferred_skills.length === 0 ? (
                  <span className="text-xs text-slate-400 font-medium">All preferred skills present</span>
                ) : (
                  explanation.missing_preferred_skills.map((s, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded-md bg-slate-800 border border-slate-700 text-slate-400 text-xs font-medium"
                    >
                      {s}
                    </span>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Natural Language Explanation Box */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
            <div className="text-xs font-bold text-brand-300 flex items-center space-x-1.5">
              <Sparkles className="w-4 h-4 text-brand-400" />
              <span>Why This Candidate Matches</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed italic">
              "{explanation.natural_language_explanation}"
            </p>
          </div>

          {/* Human-in-the-Loop Governance Notice */}
          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 flex items-start space-x-2.5 text-[11px] text-slate-400">
            <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
            <span>
              <strong>Responsible AI Notice:</strong> AI recommendations are decision-support suggestions and should be reviewed by a human recruiter before taking hiring actions.
            </span>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-slate-800 bg-slate-950/60 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-slate-800 hover:bg-slate-750 text-white rounded-xl text-xs font-semibold transition"
          >
            Close Breakdown
          </button>
        </div>
      </div>
    </div>
  );
};

export default ScoreBreakdownModal;
