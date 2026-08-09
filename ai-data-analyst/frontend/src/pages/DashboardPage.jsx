import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, AlertTriangle } from 'lucide-react';
import { getProfile } from '../api/client';
import ProfileSidebar from '../components/ProfileSidebar';
import ChatPanel from '../components/ChatPanel';
import ChartViewer from '../components/ChartViewer';
import DownloadBar from '../components/DownloadBar';
import './DashboardPage.css';

export default function DashboardPage() {
  const { filename }   = useParams();
  const navigate       = useNavigate();
  const decodedName    = decodeURIComponent(filename || '');

  const [profile, setProfile]       = useState(null);
  const [profileErr, setProfileErr] = useState(null);
  const [uploadTime, setUploadTime] = useState(null);
  const [chartUrl, setChartUrl]     = useState(null);
  const [messages, setMessages]     = useState([]);

  // Retrieve stored upload time from sessionStorage
  useEffect(() => {
    const t = sessionStorage.getItem(`upload_time_${decodedName}`);
    setUploadTime(t || new Date().toISOString());
  }, [decodedName]);

  // Fetch profile on mount
  useEffect(() => {
    if (!decodedName) return;
    getProfile(decodedName)
      .then(setProfile)
      .catch((e) => {
        const detail = e?.response?.data?.detail || 'Failed to load dataset profile.';
        setProfileErr(detail);
      });
  }, [decodedName]);

  // Called by ChatPanel when a query completes
  const handleQueryComplete = useCallback((result) => {
    // If backend returned a chart URL, display it immediately
    if (result?.chart_url) {
      setChartUrl(result.chart_url);
    }
  }, []);

  // Mirror messages from ChatPanel via callback
  const messagesRef = useRef([]);
  const handleMessagesUpdate = useCallback((msgs) => {
    messagesRef.current = msgs;
    setMessages([...msgs]);
  }, []);

  if (!decodedName) {
    return (
      <div className="dashboard-error">
        <AlertTriangle size={32} />
        <p>No dataset specified.</p>
        <button className="btn btn-primary" onClick={() => navigate('/')}>
          <ArrowLeft size={14} /> Go back
        </button>
      </div>
    );
  }

  return (
    <div className="dashboard">
      {/* ── Top nav bar ─────────────────────────────── */}
      <nav className="dashboard-nav glass-card">
        <button
          id="back-to-upload-btn"
          className="btn btn-ghost btn-sm"
          onClick={() => navigate('/')}
        >
          <ArrowLeft size={14} />
          New upload
        </button>

        <div className="dashboard-nav__center">
          <span className="dashboard-nav__title">AI Data Analyst</span>
          <span className="badge badge-emerald">Live</span>
        </div>

        <div className="dashboard-nav__right">
          <span className="dashboard-nav__file" title={decodedName}>
            {decodedName}
          </span>
        </div>
      </nav>

      {/* ── Three-panel layout ───────────────────────── */}
      <div className="dashboard-layout">
        {/* Left: Profile sidebar */}
        <div className="dashboard-col dashboard-col--left">
          <ProfileSidebar
            filename={decodedName}
            profile={profile}
            uploadTime={uploadTime}
          />
          {profileErr && (
            <div className="dashboard-profile-error glass-card">
              <AlertTriangle size={14} style={{ color: 'var(--accent-rose)' }} />
              <p>{profileErr}</p>
            </div>
          )}
        </div>

        {/* Center: Chat */}
        <div className="dashboard-col dashboard-col--center glass-card">
          <div className="dashboard-col__header">
            <span className="dashboard-col__label">Query Chat</span>
          </div>
          <ChatPanel
            filename={decodedName}
            onQueryComplete={handleQueryComplete}
          />
        </div>

        {/* Right: Chart + Export */}
        <div className="dashboard-col dashboard-col--right">
          <ChartViewer chartUrl={chartUrl} />
          <DownloadBar
            filename={decodedName}
            messages={messages}
            chartUrl={chartUrl}
          />
        </div>
      </div>
    </div>
  );
}
