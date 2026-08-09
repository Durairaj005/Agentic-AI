import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BrainCircuit, Cpu, ChartBar, Globe, ArrowRight } from 'lucide-react';
import UploadZone from '../components/UploadZone';
import './LandingPage.css';

const FEATURES = [
  { icon: BrainCircuit, title: 'Multi-Agent AI', desc: 'LangGraph orchestrates a team of specialized agents — planner, analyst, validator, reporter.' },
  { icon: ChartBar,     title: 'Visual Insights', desc: 'Plotly-powered charts generated automatically from your queries.' },
  { icon: Cpu,          title: 'Deterministic Tools', desc: 'Pandas & SciPy tools produce reproducible numerical results.' },
  { icon: Globe,        title: 'Tavily Research',  desc: 'Optional web search agent enriches results with real-world context.' },
];

export default function LandingPage() {
  const navigate  = useNavigate();
  const heroRef   = useRef(null);
  const [scrollY, setScrollY] = useState(0);

  // Parallax effect
  useEffect(() => {
    const onScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const handleUploadSuccess = (data) => {
    // Store upload time for session timer
    sessionStorage.setItem(`upload_time_${data.filename}`, new Date().toISOString());
    navigate(`/dashboard/${encodeURIComponent(data.filename)}`);
  };

  return (
    <div className="landing" ref={heroRef}>
      {/* ── Hero ─────────────────────────────────────── */}
      <section className="landing-hero">
        {/* Floating glow orbs */}
        <div
          className="landing-orb landing-orb--indigo"
          style={{ transform: `translateY(${scrollY * 0.2}px)` }}
        />
        <div
          className="landing-orb landing-orb--violet"
          style={{ transform: `translateY(${scrollY * 0.12}px)` }}
        />

        <div className="landing-hero__inner">
          {/* Badge */}
          <div className="landing-badge animate-fade-in-up">
            <span className="landing-badge__dot" />
            <span>AI Data Analyst · Phase 8</span>
          </div>

          {/* Headline */}
          <h1 className="landing-hero__title animate-fade-in-up delay-100">
            Ask questions.<br />
            <span className="gradient-text">Discover answers.</span>
          </h1>

          <p className="landing-hero__sub animate-fade-in-up delay-200">
            Upload a CSV or Excel dataset and let a coordinated team of AI agents
            profile, analyze, visualize and explain your data in plain English.
          </p>

          {/* CTA */}
          <div className="landing-hero__cta animate-fade-in-up delay-300">
            <a href="#upload" className="btn btn-primary btn-lg">
              Start analyzing <ArrowRight size={16} />
            </a>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-ghost btn-lg"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-github"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/></svg>
              View source
            </a>
          </div>

          {/* Data lifecycle notice */}
          <p className="landing-hero__notice animate-fade-in-up delay-400">
            🔒 Files auto-delete after <strong>4 hours</strong> — no account required.
          </p>
        </div>
      </section>

      {/* ── Feature cards ────────────────────────────── */}
      <section className="landing-features">
        {FEATURES.map((f, i) => {
          const Icon = f.icon;
          return (
            <div
              key={f.title}
              className={`landing-feature glass-card animate-fade-in-up delay-${(i + 1) * 100}`}
            >
              <div className="landing-feature__icon">
                <Icon size={20} />
              </div>
              <h3 className="landing-feature__title">{f.title}</h3>
              <p className="landing-feature__desc">{f.desc}</p>
            </div>
          );
        })}
      </section>

      {/* ── Upload zone ──────────────────────────────── */}
      <section className="landing-upload" id="upload">
        <div className="landing-upload__label animate-fade-in-up">
          <span>Upload your dataset</span>
        </div>
        <UploadZone onSuccess={handleUploadSuccess} />
      </section>

      {/* ── Footer ───────────────────────────────────── */}
      <footer className="landing-footer">
        <p>Built with FastAPI · LangGraph · Pandas · React</p>
        <p>MIT License · {new Date().getFullYear()}</p>
      </footer>
    </div>
  );
}
