import { useEffect, useRef, useState } from 'react';
import { Database, Hash, Type, Calendar, BarChart2, ChevronDown, ChevronUp } from 'lucide-react';
import SessionTimer from './SessionTimer';
import './ProfileSidebar.css';

const TYPE_META = {
  numeric:  { icon: Hash,     badge: 'badge-cyan',    label: 'Numeric' },
  text:     { icon: Type,     badge: 'badge-indigo',  label: 'Text' },
  datetime: { icon: Calendar, badge: 'badge-violet',  label: 'DateTime' },
  boolean:  { icon: BarChart2,badge: 'badge-amber',   label: 'Boolean' },
};
const DEFAULT_META = { icon: Hash, badge: 'badge-indigo', label: 'Mixed' };

function AnimatedNumber({ value }) {
  const [display, setDisplay] = useState(0);
  const animRef = useRef(null);

  useEffect(() => {
    const target = Number(value) || 0;
    let start = 0;
    const duration = 900;
    const startTime = performance.now();

    const step = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.floor(eased * target));
      if (progress < 1) animRef.current = requestAnimationFrame(step);
    };

    animRef.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(animRef.current);
  }, [value]);

  return <>{display.toLocaleString()}</>;
}

function ColumnRow({ col }) {
  const meta = TYPE_META[col.type?.toLowerCase?.()] || DEFAULT_META;
  const Icon = meta.icon;

  return (
    <div className="sidebar-col-row">
      <Icon size={12} className="sidebar-col-row__icon" />
      <span className="sidebar-col-row__name" title={col.name}>{col.name}</span>
      <span className={`badge ${meta.badge} sidebar-col-row__badge`}>{meta.label}</span>
    </div>
  );
}

export default function ProfileSidebar({ filename, profile, uploadTime }) {
  const [colsExpanded, setColsExpanded] = useState(false);

  if (!profile) {
    return (
      <aside className="profile-sidebar profile-sidebar--loading">
        <div className="shimmer sidebar-skeleton" style={{ height: 80, borderRadius: 10 }} />
        <div className="shimmer sidebar-skeleton" style={{ height: 50, borderRadius: 10 }} />
        <div className="shimmer sidebar-skeleton" style={{ height: 200, borderRadius: 10 }} />
      </aside>
    );
  }

  const columns = profile.columns || [];
  const displayCols = colsExpanded ? columns : columns.slice(0, 8);

  return (
    <aside className="profile-sidebar animate-slide-left">
      {/* Header */}
      <div className="sidebar-header glass-card">
        <Database size={16} style={{ color: 'var(--accent-indigo)', flexShrink: 0 }} />
        <div className="sidebar-header__text">
          <h3 className="sidebar-header__filename" title={filename}>{filename}</h3>
          <p className="sidebar-header__sub">Dataset profile</p>
        </div>
      </div>

      {/* Stats row */}
      <div className="sidebar-stats">
        <div className="sidebar-stat glass-card">
          <span className="sidebar-stat__value">
            <AnimatedNumber value={profile.total_rows} />
          </span>
          <span className="sidebar-stat__label">Rows</span>
        </div>
        <div className="sidebar-stat glass-card">
          <span className="sidebar-stat__value">
            <AnimatedNumber value={profile.total_columns} />
          </span>
          <span className="sidebar-stat__label">Columns</span>
        </div>
      </div>

      {/* Memory / size */}
      {profile.memory_usage_mb != null && (
        <div className="sidebar-meta glass-card">
          <span className="sidebar-meta__label">Memory</span>
          <span className="sidebar-meta__value">{profile.memory_usage_mb.toFixed(2)} MB</span>
        </div>
      )}
      {profile.missing_cells != null && (
        <div className="sidebar-meta glass-card">
          <span className="sidebar-meta__label">Missing cells</span>
          <span className="sidebar-meta__value">{profile.missing_cells.toLocaleString()}</span>
        </div>
      )}

      {/* Columns list */}
      <div className="sidebar-cols glass-card">
        <p className="sidebar-cols__title">Columns</p>
        <div className="sidebar-cols__list">
          {displayCols.map((col) => (
            <ColumnRow key={col.name} col={col} />
          ))}
        </div>
        {columns.length > 8 && (
          <button
            className="btn btn-ghost btn-sm sidebar-cols__expand"
            onClick={() => setColsExpanded((x) => !x)}
          >
            {colsExpanded
              ? <><ChevronUp size={12} /> Show less</>
              : <><ChevronDown size={12} /> +{columns.length - 8} more</>
            }
          </button>
        )}
      </div>

      {/* Session Timer */}
      <SessionTimer uploadTime={uploadTime} />
    </aside>
  );
}
