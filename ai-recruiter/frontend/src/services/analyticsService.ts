import api from './api';
import { AnalyticsOverviewResponse } from '../types';

export const analyticsService = {
  async getOverview(): Promise<AnalyticsOverviewResponse> {
    const res = await api.get<AnalyticsOverviewResponse>('/analytics/overview');
    return res.data;
  }
};

export default analyticsService;
