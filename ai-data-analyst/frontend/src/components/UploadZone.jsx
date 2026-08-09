import { useCallback, useState } from 'react';
import { Upload, FileSpreadsheet, AlertCircle, CheckCircle } from 'lucide-react';
import { uploadFile } from '../api/client';
import './UploadZone.css';

const ALLOWED_EXTS = ['.csv', '.xlsx', '.xls'];
const ALLOWED_MIME = [
  'text/csv',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-excel',
];

function getExt(name) {
  return name.slice(name.lastIndexOf('.')).toLowerCase();
}

export default function UploadZone({ onSuccess }) {
  const [dragging, setDragging]   = useState(false);
  const [progress, setProgress]   = useState(0);
  const [status, setStatus]       = useState('idle'); // idle | uploading | success | error
  const [errorMsg, setErrorMsg]   = useState('');
  const [fileName, setFileName]   = useState('');

  const validate = (file) => {
    const ext = getExt(file.name);
    if (!ALLOWED_EXTS.includes(ext)) {
      return `Unsupported file type "${ext}". Please upload CSV, XLSX, or XLS.`;
    }
    if (file.size > 50 * 1024 * 1024) {
      return 'File is too large. Maximum size is 50 MB.';
    }
    return null;
  };

  const handleUpload = useCallback(async (file) => {
    const err = validate(file);
    if (err) { setErrorMsg(err); setStatus('error'); return; }

    setFileName(file.name);
    setStatus('uploading');
    setProgress(0);
    setErrorMsg('');

    try {
      const data = await uploadFile(file, setProgress);
      setStatus('success');
      setProgress(100);
      // Small delay for the success animation
      setTimeout(() => onSuccess(data), 800);
    } catch (e) {
      const detail = e?.response?.data?.detail || e.message || 'Upload failed.';
      setErrorMsg(detail);
      setStatus('error');
    }
  }, [onSuccess]);

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
  }, [handleUpload]);

  const onFileChange = (e) => {
    const file = e.target.files[0];
    if (file) handleUpload(file);
    e.target.value = '';
  };

  const isUploading = status === 'uploading';
  const isSuccess   = status === 'success';
  const isError     = status === 'error';

  return (
    <div className="upload-zone-wrapper animate-fade-in-up">
      <label
        id="upload-drop-zone"
        className={`upload-zone ${dragging ? 'upload-zone--dragging' : ''} ${isSuccess ? 'upload-zone--success' : ''} ${isError ? 'upload-zone--error' : ''} ${isUploading ? 'upload-zone--uploading' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        aria-label="Upload dataset file"
      >
        <input
          id="file-input"
          type="file"
          accept=".csv,.xlsx,.xls"
          className="sr-only"
          onChange={onFileChange}
          disabled={isUploading}
        />

        <div className="upload-zone__inner">
          {/* Icon */}
          <div className={`upload-zone__icon ${isUploading ? 'animate-pulse' : 'animate-float'}`}>
            {isSuccess
              ? <CheckCircle size={48} strokeWidth={1.5} style={{ color: 'var(--accent-emerald)' }} />
              : isError
              ? <AlertCircle size={48} strokeWidth={1.5} style={{ color: 'var(--accent-rose)' }} />
              : <FileSpreadsheet size={48} strokeWidth={1.5} style={{ color: 'var(--accent-indigo)' }} />
            }
          </div>

          {/* Text */}
          {isUploading ? (
            <div className="upload-zone__uploading">
              <p className="upload-zone__title">Uploading <span className="gradient-text">{fileName}</span></p>
              <p className="upload-zone__sub">Profiling dataset…</p>
            </div>
          ) : isSuccess ? (
            <div className="upload-zone__uploading">
              <p className="upload-zone__title" style={{ color: 'var(--accent-emerald)' }}>Upload complete!</p>
              <p className="upload-zone__sub">Redirecting to dashboard…</p>
            </div>
          ) : isError ? (
            <div className="upload-zone__uploading">
              <p className="upload-zone__title" style={{ color: 'var(--accent-rose)' }}>Upload failed</p>
              <p className="upload-zone__sub">{errorMsg}</p>
              <button
                className="btn btn-secondary btn-sm"
                style={{ marginTop: '1rem' }}
                onClick={(e) => { e.preventDefault(); setStatus('idle'); }}
              >
                Try again
              </button>
            </div>
          ) : (
            <>
              <div className="upload-zone__text">
                <p className="upload-zone__title">
                  Drop your dataset here, or{' '}
                  <span className="gradient-text">browse</span>
                </p>
                <p className="upload-zone__sub">Supports CSV, XLSX, XLS — up to 50 MB</p>
              </div>
              <div className="upload-zone__chips">
                {ALLOWED_EXTS.map((ext) => (
                  <span key={ext} className="badge badge-indigo">{ext}</span>
                ))}
              </div>
              <div className="upload-zone__cta">
                <Upload size={14} />
                Click or drag &amp; drop
              </div>
            </>
          )}
        </div>

        {/* Progress bar */}
        {(isUploading || isSuccess) && (
          <div className="upload-zone__progress-bar">
            <div
              className="upload-zone__progress-fill"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
      </label>

      {/* Privacy notice */}
      <p className="upload-zone__notice">
        🔒 Files are processed in-memory and auto-deleted after <strong>4 hours</strong>. No permanent storage.
      </p>
    </div>
  );
}
