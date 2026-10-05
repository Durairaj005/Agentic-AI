import api from './api';
import { ComparisonMatrixResponse } from '../types';

export const comparisonService = {
  async compareCandidates(candidateIds: string[], jobId?: string): Promise<ComparisonMatrixResponse> {
    const res = await api.post<ComparisonMatrixResponse>('/candidates/compare', {
      candidate_ids: candidateIds,
      job_id: jobId || undefined
    });
    return res.data;
  }
};

export default comparisonService;
