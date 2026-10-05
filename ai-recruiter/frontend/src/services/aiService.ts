import api from './api';
import { Candidate } from '../types';

export interface ParsedJobDescriptionResponse {
  title: string;
  company: string;
  location: string;
  employment_type: 'FULL_TIME' | 'PART_TIME' | 'CONTRACT' | 'REMOTE';
  experience_min: number;
  experience_max: number;
  education: string;
  description: string;
  skills: {
    skill: string;
    importance: 'HIGH' | 'MEDIUM' | 'LOW';
    required: boolean;
    category: string;
  }[];
  responsibilities: string[];
  keywords: string[];
}

export interface NormalizedSkillItem {
  input: string;
  canonical: string;
  category: string;
}

export const aiService = {
  async parseJD(text: string): Promise<ParsedJobDescriptionResponse> {
    const res = await api.post<ParsedJobDescriptionResponse>('/ai/parse-jd', { text });
    return res.data;
  },

  async normalizeSkills(skills: string[]): Promise<NormalizedSkillItem[]> {
    const res = await api.post<{ normalized: NormalizedSkillItem[] }>('/ai/skills/normalize', { skills });
    return res.data.normalized;
  },

  async reparseCandidate(candidateId: string): Promise<Candidate> {
    const res = await api.post<Candidate>(`/ai/candidates/${candidateId}/reparse`);
    return res.data;
  }
};

export default aiService;
