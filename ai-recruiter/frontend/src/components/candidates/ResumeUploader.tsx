import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, X, Sparkles } from 'lucide-react';
import candidateService, { CandidateUploadResponse } from '../../services/candidateService';

interface ResumeUploaderProps {
  onSuccess: (response: CandidateUploadResponse) => void;
  onClose?: () => void;
}

export const ResumeUploader: React.FC<ResumeUploaderProps> = ({ onSuccess, onClose }) => {
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successResult, setSuccessResult] = useState<CandidateUploadResponse | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileProcess = async (file: File) => {
    const validExtensions = ['.pdf', '.docx', '.txt'];
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();

    if (!validExtensions.includes(fileExt)) {
      setError(`Invalid format. Please upload a PDF, DOCX, or TXT file.`);
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError('File size exceeds the 10 MB limit.');
      return;
    }

    setError(null);
    setUploading(true);

    try {
      const res = await candidateService.uploadResume(file);
      setSuccessResult(res);
      onSuccess(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to parse resume document.');
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileProcess(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="space-y-4">
      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs rounded-xl flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {successResult ? (
        <div className="p-5 rounded-2xl bg-emerald-950/40 border border-emerald-800/60 space-y-3 animate-fade-in">
          <div className="flex items-center space-x-2 text-emerald-400 text-sm font-bold">
            <CheckCircle2 className="w-5 h-5" />
            <span>Resume Ingested & Parsed Successfully</span>
          </div>

          <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800 text-xs space-y-1.5 text-slate-300">
            <div className="font-bold text-white text-sm">{successResult.candidate.name}</div>
            <div className="text-slate-400">{successResult.candidate.email} &bull; {successResult.candidate.location}</div>
            <div className="text-brand-300 font-medium pt-1">
              Experience: {successResult.candidate.total_experience} Years &bull; Degree: {successResult.candidate.education_level}
            </div>
            <div className="flex flex-wrap gap-1.5 pt-2">
              {successResult.candidate.skills?.map((s, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 rounded-md bg-brand-500/10 border border-brand-500/30 text-brand-300 text-[10px] font-semibold"
                >
                  {s.skill}
                </span>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-end space-x-2 pt-1">
            <button
              onClick={() => {
                setSuccessResult(null);
                if (onClose) onClose();
              }}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold transition"
            >
              Done
            </button>
          </div>
        </div>
      ) : (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition flex flex-col items-center justify-center space-y-3 ${
            dragOver
              ? 'border-brand-500 bg-brand-500/10'
              : 'border-slate-800 hover:border-slate-700 bg-slate-900/50'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                handleFileProcess(e.target.files[0]);
              }
            }}
          />

          <div className="w-12 h-12 rounded-2xl bg-brand-500/10 border border-brand-500/20 text-brand-400 flex items-center justify-center">
            {uploading ? (
              <div className="w-6 h-6 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" />
            ) : (
              <UploadCloud className="w-6 h-6" />
            )}
          </div>

          <div className="space-y-1">
            <p className="text-sm font-semibold text-white">
              {uploading ? 'Parsing resume document...' : 'Click to upload or drag & drop'}
            </p>
            <p className="text-xs text-slate-400">
              Supports PDF (PyMuPDF), DOCX (python-docx), and TXT files (up to 10 MB)
            </p>
          </div>

          <div className="flex items-center space-x-2 text-[11px] text-slate-500 font-medium">
            <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700">PDF</span>
            <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700">DOCX</span>
            <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700">TXT</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResumeUploader;
