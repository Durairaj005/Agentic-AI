import { useState, useEffect } from 'react';
import { ImageOff, Download, RefreshCw, Maximize2, X } from 'lucide-react';
import { downloadChartImage } from '../api/client';
import './ChartViewer.css';

export default function ChartViewer({ chartUrl, onRefresh }) {
  const [imgError, setImgError]       = useState(false);
  const [loaded, setLoaded]           = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Reset states whenever a new chart URL arrives
  useEffect(() => {
    setImgError(false);
    setLoaded(false);
    setIsModalOpen(false);
  }, [chartUrl]);

  // Handle ESC key to close modal
  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.key === 'Escape') setIsModalOpen(false);
    };
    if (isModalOpen) {
      window.addEventListener('keydown', onKeyDown);
    }
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [isModalOpen]);

  const handleDownload = (e) => {
    e?.stopPropagation?.();
    if (!chartUrl) return;
    downloadChartImage(chartUrl, 'analysis_chart.png');
  };

  const isEmpty = !chartUrl;

  return (
    <>
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
              <>
                <button
                  className="btn btn-ghost btn-sm btn-icon"
                  onClick={() => setIsModalOpen(true)}
                  title="Enlarge chart preview"
                >
                  <Maximize2 size={13} />
                </button>
                <button
                  id="download-chart-btn"
                  className="btn btn-secondary btn-sm"
                  onClick={handleDownload}
                  title="Download PNG"
                >
                  <Download size={13} />
                  Save PNG
                </button>
              </>
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
            <div
              className="chart-viewer__img-wrapper"
              onClick={() => setIsModalOpen(true)}
              title="Click to enlarge chart"
            >
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
              <div className="chart-viewer__overlay">
                <Maximize2 size={14} />
                <span>Click to enlarge</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── In-App Modal / Lightbox ─────────────────────── */}
      {isModalOpen && chartUrl && (
        <div
          className="chart-modal-backdrop animate-fade-in"
          onClick={() => setIsModalOpen(false)}
        >
          <div
            className="chart-modal glass-card animate-scale-in"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="chart-modal__header">
              <div className="chart-modal__title-group">
                <span className="chart-viewer__dot" />
                <h3 className="chart-modal__title">Data Visualization Preview</h3>
              </div>
              <div className="chart-modal__actions">
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={handleDownload}
                  title="Save PNG to your downloads folder"
                >
                  <Download size={13} />
                  Download PNG
                </button>
                <button
                  className="btn btn-ghost btn-sm btn-icon"
                  onClick={() => setIsModalOpen(false)}
                  title="Close preview (Esc)"
                >
                  <X size={16} />
                </button>
              </div>
            </div>

            <div className="chart-modal__body">
              <img
                src={chartUrl}
                alt="Enlarged visualization"
                className="chart-modal__img"
              />
            </div>

            <div className="chart-modal__footer">
              <span>Press <kbd>Esc</kbd> or click outside to return to dashboard</span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
