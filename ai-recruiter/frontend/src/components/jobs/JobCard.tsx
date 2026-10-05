import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Briefcase, 
  MapPin, 
  Clock, 
  Users, 
  ChevronRight, 
  Edit3, 
  Trash2, 
  Power,
  Sparkles
} from 'lucide-react';
import { Job } from '../../types';
import SkillBadgeList from './SkillBadgeList';

interface JobCardProps {
  job: Job;
  onEdit: (job: Job) => void;
  onDelete: (id: string) => void;
  onToggleStatus: (id: string) => void;
}

export const JobCard: React.FC<JobCardProps> = ({
  job,
  onEdit,
  onDelete,
  onToggleStatus
}) => {
  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 hover:border-slate-700/80 transition-all duration-200 shadow-lg hover:shadow-indigo-500/5 flex flex-col justify-between space-y-4">
      <div className="space-y-3">
        {/* Top Header Row */}
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span
                className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full border ${
                  job.status === 'ACTIVE'
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                    : 'bg-slate-800 border-slate-700 text-slate-400'
                }`}
              >
                {job.status}
              </span>
              <span className="text-[10px] uppercase font-semibold text-slate-500">
                {job.employment_type.replace('_', ' ')}
              </span>
            </div>
            <Link
              to={`/jobs/${job.id}`}
              className="text-base font-bold text-white hover:text-brand-300 transition line-clamp-1"
            >
              {job.title}
            </Link>
            <div className="text-xs font-medium text-slate-400">{job.company}</div>
          </div>

          <div className="flex items-center space-x-1">
            <button
              onClick={() => onToggleStatus(job.id)}
              title={job.status === 'ACTIVE' ? 'Close Requisition' : 'Activate Requisition'}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            >
              <Power className={`w-4 h-4 ${job.status === 'ACTIVE' ? 'text-emerald-400' : 'text-slate-500'}`} />
            </button>
            <button
              onClick={() => onEdit(job)}
              title="Edit Requisition"
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            >
              <Edit3 className="w-4 h-4" />
            </button>
            <button
              onClick={() => onDelete(job.id)}
              title="Delete Requisition"
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Location & Experience meta */}
        <div className="flex flex-wrap gap-y-1 gap-x-4 text-xs text-slate-400">
          <div className="flex items-center space-x-1">
            <MapPin className="w-3.5 h-3.5 text-slate-500" />
            <span>{job.location}</span>
          </div>
          <div className="flex items-center space-x-1">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            <span>{job.experience_min} - {job.experience_max} yrs exp</span>
          </div>
          <div className="flex items-center space-x-1">
            <Users className="w-3.5 h-3.5 text-indigo-400" />
            <span className="font-semibold text-slate-300">{job.applicant_count || 0} applicants</span>
          </div>
        </div>

        {/* Description snippet */}
        <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
          {job.description}
        </p>

        {/* Technical Skills Classification */}
        <div className="pt-1">
          <SkillBadgeList skills={job.skills} maxDisplay={4} />
        </div>
      </div>

      {/* Card Footer Actions */}
      <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
        <span className="text-[11px] text-slate-500">
          Posted {new Date(job.created_at).toLocaleDateString()}
        </span>
        <Link
          to={`/jobs/${job.id}`}
          className="inline-flex items-center space-x-1 text-brand-400 hover:text-brand-300 font-semibold transition"
        >
          <span>View Candidates & Match</span>
          <ChevronRight className="w-4 h-4" />
        </Link>
      </div>
    </div>
  );
};

export default JobCard;
