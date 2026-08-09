import { useEffect, useRef, useState } from 'react';
import { Clock, AlertTriangle } from 'lucide-react';
import './SessionTimer.css';

const SESSION_DURATION_MS = 4 * 60 * 60 * 1000; // 4 hours
const WARN_AT_MS = 30 * 60 * 1000; // 30 minutes

function pad(n) {
  return String(n).padStart(2, '0');
}

function formatTime(ms) {
  if (ms <= 0) return '00:00:00';
  const totalSecs = Math.floor(ms / 1000);
  const h = Math.floor(totalSecs / 3600);
  const m = Math.floor((totalSecs % 3600) / 60);
  const s = totalSecs % 60;
  return `${pad(h)}:${pad(m)}:${pad(s)}`;
}

export default function SessionTimer({ uploadTime }) {
  const [remaining, setRemaining] = useState(0);
  const [phase, setPhase] = useState('safe'); // safe | warn | critical | expired
  const intervalRef = useRef(null);

  useEffect(() => {
    if (!uploadTime) return;

    const expiresAt = new Date(uploadTime).getTime() + SESSION_DURATION_MS;

    const tick = () => {
      const now = Date.now();
      const rem = expiresAt - now;

      if (rem <= 0) {
        setRemaining(0);
        setPhase('expired');
        clearInterval(intervalRef.current);
        return;
      }

      setRemaining(rem);

      if (rem <= 5 * 60 * 1000) {
        setPhase('critical');
      } else if (rem <= WARN_AT_MS) {
        setPhase('warn');
      } else {
        setPhase('safe');
      }
    };

    tick();
    intervalRef.current = setInterval(tick, 1000);
    return () => clearInterval(intervalRef.current);
  }, [uploadTime]);

  const pct = Math.max(0, Math.min(100, (remaining / SESSION_DURATION_MS) * 100));

  return (
    <div className={`session-timer session-timer--${phase}`}>
      <div className="session-timer__header">
        {phase === 'warn' || phase === 'critical'
          ? <AlertTriangle size={13} />
          : <Clock size={13} />
        }
        <span className="session-timer__label">Session expires in</span>
      </div>

      <div className="session-timer__time">
        {phase === 'expired' ? 'Expired' : formatTime(remaining)}
      </div>

      {/* Arc progress */}
      <div className="session-timer__bar">
        <div
          className="session-timer__fill"
          style={{ width: `${pct}%` }}
        />
      </div>

      {phase === 'warn' && (
        <p className="session-timer__hint">Data deletes in &lt;30 min</p>
      )}
      {phase === 'critical' && (
        <p className="session-timer__hint">⚠ Data deletes in &lt;5 min!</p>
      )}
    </div>
  );
}
