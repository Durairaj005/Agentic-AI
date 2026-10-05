import api from './api';
import { Application, ApplicationStatus, Interview, Followup, Note } from '../types';

export interface ApplicationFilterParams {
  job_id?: string;
  status?: string;
  search?: string;
  min_score?: number;
}

export interface FollowupPayload {
  candidate_id: string;
  followup_date: string;
  method: string;
  notes?: string;
}

export interface InterviewPayload {
  application_id: string;
  interview_date: string;
  interview_type: string;
  interviewer: string;
  feedback?: string;
  rating?: number;
}

export const pipelineService = {
  // Applications & Stage
  async getApplications(params?: ApplicationFilterParams): Promise<Application[]> {
    const res = await api.get<Application[]>('/applications', { params });
    return res.data;
  },

  async getApplication(id: string): Promise<Application> {
    const res = await api.get<Application>(`/applications/${id}`);
    return res.data;
  },

  async updateStage(
    applicationId: string,
    status: ApplicationStatus | string,
    recruiter_notes?: string
  ): Promise<Application> {
    const res = await api.put<Application>(`/applications/${applicationId}/stage`, {
      status,
      recruiter_notes
    });
    return res.data;
  },

  // Candidate Notes
  async getCandidateNotes(candidateId: string): Promise<Note[]> {
    const res = await api.get<Note[]>(`/candidates/${candidateId}/notes`);
    return res.data;
  },

  async addCandidateNote(candidateId: string, note: string): Promise<Note> {
    const res = await api.post<Note>(`/candidates/${candidateId}/notes`, { note });
    return res.data;
  },

  // Followups
  async getFollowups(params?: { candidate_id?: string; status?: string }): Promise<Followup[]> {
    const res = await api.get<Followup[]>('/followups', { params });
    return res.data;
  },

  async createFollowup(payload: FollowupPayload): Promise<Followup> {
    const res = await api.post<Followup>('/followups', payload);
    return res.data;
  },

  async updateFollowup(
    id: string,
    payload: Partial<{ status: string; notes: string; followup_date: string; method: string }>
  ): Promise<Followup> {
    const res = await api.patch<Followup>(`/followups/${id}`, payload);
    return res.data;
  },

  async deleteFollowup(id: string): Promise<{ message: string }> {
    const res = await api.delete<{ message: string }>(`/followups/${id}`);
    return res.data;
  },

  // Interviews
  async getInterviews(params?: { application_id?: string; status?: string }): Promise<Interview[]> {
    const res = await api.get<Interview[]>('/interviews', { params });
    return res.data;
  },

  async scheduleInterview(payload: InterviewPayload): Promise<Interview> {
    const res = await api.post<Interview>('/interviews', payload);
    return res.data;
  },

  async updateInterview(
    id: string,
    payload: Partial<{ status: string; feedback: string; rating: number; interview_date: string; interview_type: string; interviewer: string }>
  ): Promise<Interview> {
    const res = await api.patch<Interview>(`/interviews/${id}`, payload);
    return res.data;
  },

  // Seed Pipeline
  async seedPipeline(): Promise<{ message: string; total_applications: number }> {
    const res = await api.post<{ message: string; total_applications: number }>('/pipeline/seed');
    return res.data;
  }
};

export default pipelineService;
