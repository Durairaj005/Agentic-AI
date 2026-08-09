import { useState, useEffect } from 'react';
import { ImageOff, Download, RefreshCw } from 'lucide-react';
import './ChartViewer.css';

export default function ChartViewer({ chartUrl, onRefresh }) {
  const [imgError, setImgError] = useState(false);
  const [loaded, setLoaded]     = useState(false);

  // Reset states whenever a new chart URL arrives
  useEffect(() => {
    setImgError(false);
    setLoaded(false);
  }, [chartUrl]);

  const handleDownload = () => {
    if (!chartUrl) return;
    const a = document.createElement('a');
    a.href = chartUrl;
    a.download = 'chart.png';
    a.click();
  };

  const isEmpty = !chartUrl;

  return (
    <div className="chart-viewer glass-card">
      {/* Header */}
      <div className="chart-viewer__header">
        <span className="chart-viewer__title">
          <span className="chart-viewer__dot" />
          Chart Output
        </span>
        <div className="chart-viewer__actions">
          {onRefresh && (
            <button className="btn btn-ghost btn-sm btn-icon" onClick={onRefresh} title="Refresh">
              <RefreshCw size={13} />
            </button>
          )}
          {chartUrl && !imgError && (
            <button
              id="download-chart-btn"
              className="btn btn-secondary btn-sm"
              onClick={handleDownload}
            >
              <Download size={13} />
              Save PNG
            </button>
          )}
        </div>
      </div>

      {/* Chart display */}
      <div className="chart-viewer__body">
        {isEmpty || imgError ? (
          <div className="chart-viewer__empty">
            <div className="chart-viewer__empty-icon animate-float">
              <ImageOff size={28} style={{ color: 'var(--text-muted)' }} />
            </div>
            <p className="chart-viewer__empty-title">
              {imgError ? 'Chart failed to load' : 'No chart yet'}
            </p>
            <p className="chart-viewer__empty-sub">
              {imgError
                ? 'The chart image could not be fetched from the server.'
                : 'Ask a question that produces a visual result — e.g. "Monthly sales trend" or "Top 5 categories".'}
            </p>
          </div>
        ) : (
          <div className="chart-viewer__img-wrapper">
            {!loaded && (
              <div className="shimmer chart-viewer__skeleton" />
            )}
            <img
              src={chartUrl}
              alt="Analysis chart"
              className={`chart-viewer__img ${loaded ? 'chart-viewer__img--visible' : ''}`}
              onLoad={() => setLoaded(true)}
              onError={() => { setImgError(true); setLoaded(true); }}
            />
          </div>
        )}
      </div>
    </div>
  );
}
