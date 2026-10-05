import api from './api';
import { ChatQueryResponse, SemanticSearchResult } from '../types';

export interface ChatPayload {
  message: string;
  job_id?: string;
  candidate_id?: string;
  history?: Array<{ role: string; content: string }>;
}

export const aiAssistantService = {
  async chat(payload: ChatPayload): Promise<ChatQueryResponse> {
    const res = await api.post<ChatQueryResponse>('/ai/assistant/chat', payload);
    return res.data;
  },

  async generateQuestions(candidateId: string, jobId?: string): Promise<ChatQueryResponse> {
    const res = await api.post<ChatQueryResponse>('/ai/assistant/generate-questions', {
      candidate_id: candidateId,
      job_id: jobId
    });
    return res.data;
  },

  async draftOutreach(candidateId: string, jobId?: string, tone: string = 'PROFESSIONAL'): Promise<ChatQueryResponse> {
    const res = await api.post<ChatQueryResponse>('/ai/assistant/draft-outreach', {
      candidate_id: candidateId,
      job_id: jobId,
      tone
    });
    return res.data;
  },

  async semanticSearch(q: string, topK: number = 5): Promise<{ query: string; total_results: number; results: SemanticSearchResult[] }> {
    const res = await api.get('/ai/assistant/search-candidates', {
      params: { q, top_k: topK }
    });
    return res.data;
  },

  async reindexVectors(): Promise<{ message: string; total_vectors: number; dimension: number }> {
    const res = await api.post('/ai/assistant/reindex-vectors');
    return res.data;
  }
};

export default aiAssistantService;
