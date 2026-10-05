import React from 'react';
import { Link } from 'react-router-dom';
import { 
  User, 
  MapPin, 
  Clock, 
  GraduationCap, 
  FileText, 
  ChevronRight, 
  Trash2,
  Mail,
  Phone
} from 'lucide-react';
import { Candidate } from '../../types';

interface CandidateCardProps {
  candidate: Candidate;
  onDelete: (id: string) => void;
}

export const CandidateCard: React.FC<CandidateCardProps> = ({ candidate, onDelete }) => {
  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 hover:border-slate-700/80 transition-all duration-200 shadow-lg hover:shadow-indigo-500/5 flex flex-col justify-between space-y-4">
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center text-white font-bold text-sm shadow-md">
              {candidate.name.charAt(0).toUpperCase()}
            </div>
            <div>
              <Link
                to={`/candidates/${candidate.id}`}
                className="text-base font-bold text-white hover:text-brand-300 transition line-clamp-1"
              >
                {candidate.name}
              </Link>
              <div className="flex items-center space-x-1 text-xs text-slate-400">
                <Mail className="w-3 h-3 text-slate-500" />
                <span className="truncate max-w-[170px]">{candidate.email}</span>
              </div>
            </div>
          </div>

          <button
            onClick={() => onDelete(candidate.id)}
            title="Delete Candidate Profile"
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>

        {/* Experience & Education Badges */}
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 font-semibold">
            <Clock className="w-3 h-3" />
            <span>{candidate.total_experience} yrs exp</span>
          </span>

          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 font-semibold">
            <GraduationCap className="w-3 h-3" />
            <span>{candidate.education_level}</span>
          </span>

          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-400">
            <MapPin className="w-3 h-3" />
            <span className="truncate max-w-[120px]">{candidate.location}</span>
          </span>
        </div>

        {/* Summary Snippet */}
        {candidate.summary && (
          <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
            {candidate.summary}
          </p>
        )}

        {/* Skills Chips */}
        {candidate.skills && candidate.skills.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {candidate.skills.slice(0, 5).map((s, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 rounded-md bg-slate-800/80 border border-slate-700/80 text-[11px] font-medium text-slate-300"
              >
                {s.skill}
              </span>
            ))}
            {candidate.skills.length > 5 && (
              <span className="text-[10px] text-slate-500 self-center">
                +{candidate.skills.length - 5} more
              </span>
            )}
          </div>
        )}
      </div>

      {/* Card Footer */}
      <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
        <span className="text-[11px] text-slate-500 flex items-center space-x-1">
          <FileText className="w-3.5 h-3.5 text-slate-500" />
          <span className="truncate max-w-[120px]">
            {candidate.resume_filename || 'Parsed Dossier'}
          </span>
        </span>

        <Link
          to={`/candidates/${candidate.id}`}
          className="inline-flex items-center space-x-1 text-brand-400 hover:text-brand-300 font-semibold transition"
        >
          <span>View Dossier</span>
          <ChevronRight className="w-4 h-4" />
        </Link>
      </div>
    </div>
  );
};

export default CandidateCard;
