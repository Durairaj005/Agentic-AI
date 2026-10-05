import api from './api';
import { Candidate, CandidateSkill } from '../types';

export interface CandidateFilterParams {
  search?: string;
  min_experience?: number;
  max_experience?: number;
  education_level?: string;
  skill?: string;
  skip?: number;
  limit?: number;
}

export interface CandidatePayload {
  name: string;
  email: string;
  phone?: string;
  location?: string;
  total_experience: number;
  education_level: 'BACHELORS' | 'MASTERS' | 'PHD' | 'DIPLOMA' | 'SELF_TAUGHT' | 'OTHER';
  education_details?: string;
  summary?: string;
  skills?: {
    skill: string;
    years_experience: number;
    confidence_score: number;
  }[];
}

export interface CandidateUploadResponse {
  candidate: Candidate;
  extracted_text_preview: string;
  message: string;
}

export const candidateService = {
  async getCandidates(params?: CandidateFilterParams): Promise<Candidate[]> {
    const res = await api.get<Candidate[]>('/candidates', { params });
    return res.data;
  },

  async getCandidate(id: string): Promise<Candidate> {
    const res = await api.get<Candidate>(`/candidates/${id}`);
    return res.data;
  },

  async createCandidate(payload: CandidatePayload): Promise<Candidate> {
    const res = await api.post<Candidate>('/candidates', payload);
    return res.data;
  },

  async updateCandidate(id: string, payload: Partial<CandidatePayload>): Promise<Candidate> {
    const res = await api.put<Candidate>(`/candidates/${id}`, payload);
    return res.data;
  },

  async deleteCandidate(id: string): Promise<void> {
    await api.delete(`/candidates/${id}`);
  },

  async uploadResume(file: File): Promise<CandidateUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post<CandidateUploadResponse>('/candidates/upload-resume', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  async seedCandidates(): Promise<Candidate[]> {
    const res = await api.post<Candidate[]>('/candidates/seed');
    return res.data;
  },

  getDownloadResumeUrl(candidateId: string): string {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
    return `${baseUrl}/candidates/${candidateId}/download-resume`;
  }
};

export default candidateService;
