import api from './api';
import { RankedMatchesResponse, CandidateMatchResult } from '../types';

export interface MatchFilterParams {
  sort_by?: 'score' | 'experience';
  min_score?: number;
  status?: string;
  search?: string;
  skill?: string;
}

export interface MatchWeightPayload {
  weight_required_skills?: number;
  weight_preferred_skills?: number;
  weight_experience?: number;
  weight_education?: number;
  weight_semantic?: number;
}

export interface MatchExecutionSummary {
  job_id: string;
  evaluated_count: number;
  created_applications_count: number;
  message: string;
}

export const matchService = {
  async runMatching(
    jobId: string,
    weights?: MatchWeightPayload,
    candidateIds?: string[]
  ): Promise<MatchExecutionSummary> {
    const res = await api.post<MatchExecutionSummary>(`/jobs/${jobId}/match`, {
      weights: weights || {},
      candidate_ids: candidateIds || []
    });
    return res.data;
  },

  async getRankedMatches(jobId: string, params?: MatchFilterParams): Promise<RankedMatchesResponse> {
    const res = await api.get<RankedMatchesResponse>(`/jobs/${jobId}/matches`, { params });
    return res.data;
  }
};

export default matchService;
