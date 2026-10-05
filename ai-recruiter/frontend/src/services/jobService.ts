import api from './api';
import { Job, JobSkill } from '../types';

export interface JobFilterParams {
  status?: string;
  search?: string;
  employment_type?: string;
  skip?: number;
  limit?: number;
}

export interface JobPayload {
  title: string;
  company: string;
  description: string;
  location: string;
  employment_type: 'FULL_TIME' | 'PART_TIME' | 'CONTRACT' | 'REMOTE';
  experience_min: number;
  experience_max: number;
  status: 'ACTIVE' | 'DRAFT' | 'CLOSED';
  skills: {
    skill: string;
    importance: 'HIGH' | 'MEDIUM' | 'LOW';
    required: boolean;
  }[];
}

export const jobService = {
  async getJobs(params?: JobFilterParams): Promise<Job[]> {
    const res = await api.get<Job[]>('/jobs', { params });
    return res.data;
  },

  async getJob(id: string): Promise<Job> {
    const res = await api.get<Job>(`/jobs/${id}`);
    return res.data;
  },

  async createJob(payload: JobPayload): Promise<Job> {
    const res = await api.post<Job>('/jobs', payload);
    return res.data;
  },

  async updateJob(id: string, payload: Partial<JobPayload>): Promise<Job> {
    const res = await api.put<Job>(`/jobs/${id}`, payload);
    return res.data;
  },

  async deleteJob(id: string): Promise<void> {
    await api.delete(`/jobs/${id}`);
  },

  async toggleStatus(id: string): Promise<Job> {
    const res = await api.patch<Job>(`/jobs/${id}/toggle-status`);
    return res.data;
  },

  async seedJobs(): Promise<Job[]> {
    const res = await api.post<Job[]>('/jobs/seed');
    return res.data;
  }
};

export default jobService;
