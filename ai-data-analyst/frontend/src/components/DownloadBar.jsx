import { FileJson, FileText, Image } from 'lucide-react';
import './DownloadBar.css';

export default function DownloadBar({ filename, messages, chartUrl }) {
  const handleExportJSON = () => {
    const data = messages
      .filter((m) => m.role !== 'ai' || !m.isLoading)
      .map((m) => ({
        role: m.role,
        content: m.content,
        result: m.result || null,
        errors: m.errors || [],
      }));
    const blob = new Blob([JSON.stringify({ filename, session: data }, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename.replace(/\.[^.]+$/, '')}_session.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadChart = () => {
    if (!chartUrl) return;
    const a = document.createElement('a');
    a.href = chartUrl;
    a.download = 'chart.png';
    a.click();
  };

  const handleDownloadCSV = () => {
    // Re-link to the original upload endpoint
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    window.open(`${baseUrl}/api/v1/datasets/download/${encodeURIComponent(filename)}`, '_blank');
  };

  return (
    <div className="download-bar glass-card animate-fade-in">
      <span className="download-bar__label">Export</span>

      <div className="download-bar__actions">
        <button
          id="export-json-btn"
          className="btn btn-secondary btn-sm"
          onClick={handleExportJSON}
          disabled={messages.filter((m) => !m.isLoading).length === 0}
          title="Export full session as JSON"
        >
          <FileJson size={13} />
          Session JSON
        </button>

        <button
          id="export-chart-btn"
          className="btn btn-secondary btn-sm"
          onClick={handleDownloadChart}
          disabled={!chartUrl}
          title="Download last chart as PNG"
        >
          <Image size={13} />
          Chart PNG
        </button>

        <button
          id="export-csv-btn"
          className="btn btn-ghost btn-sm"
          onClick={handleDownloadCSV}
          title="Re-download the raw dataset"
        >
          <FileText size={13} />
          Raw CSV
        </button>
      </div>
    </div>
  );
}
