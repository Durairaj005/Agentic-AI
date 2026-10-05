import React from 'react';
import { Check, Star } from 'lucide-react';
import { JobSkill } from '../../types';

interface SkillBadgeListProps {
  skills: JobSkill[];
  maxDisplay?: number;
}

export const SkillBadgeList: React.FC<SkillBadgeListProps> = ({ skills, maxDisplay }) => {
  const required = skills.filter((s) => s.required);
  const preferred = skills.filter((s) => !s.required);

  const displayList = maxDisplay ? skills.slice(0, maxDisplay) : skills;
  const remainingCount = maxDisplay && skills.length > maxDisplay ? skills.length - maxDisplay : 0;

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1.5 items-center">
        {displayList.map((item, idx) => (
          <span
            key={idx}
            className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-lg text-[11px] font-medium border transition ${
              item.required
                ? 'bg-brand-500/10 border-brand-500/30 text-brand-300'
                : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
            }`}
          >
            {item.required ? (
              <Check className="w-3 h-3 text-brand-400" />
            ) : (
              <Star className="w-3 h-3 text-emerald-400" />
            )}
            <span>{item.skill}</span>
            <span
              className={`text-[9px] px-1 rounded uppercase tracking-wider font-semibold opacity-70 ${
                item.importance === 'HIGH'
                  ? 'bg-rose-500/20 text-rose-300'
                  : item.importance === 'MEDIUM'
                  ? 'bg-amber-500/20 text-amber-300'
                  : 'bg-slate-500/20 text-slate-400'
              }`}
            >
              {item.importance}
            </span>
          </span>
        ))}

        {remainingCount > 0 && (
          <span className="text-[11px] text-slate-400 font-medium px-2 py-0.5 rounded-md bg-slate-800 border border-slate-700">
            +{remainingCount} more
          </span>
        )}
      </div>
    </div>
  );
};

export default SkillBadgeList;
