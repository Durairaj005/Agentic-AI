export interface User {
  id: string;
  name: string;
  email: string;
  role: 'RECRUITER' | 'ADMIN';
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface JobSkill {
  id?: string;
  job_id?: string;
  skill: string;
  importance: 'HIGH' | 'MEDIUM' | 'LOW';
  required: boolean;
}

export interface Job {
  id: string;
  title: string;
  company: string;
  description: string;
  location: string;
  employment_type: 'FULL_TIME' | 'PART_TIME' | 'CONTRACT' | 'REMOTE';
  experience_min: number;
  experience_max: number;
  status: 'ACTIVE' | 'DRAFT' | 'CLOSED';
  created_by?: string;
  created_at: string;
  updated_at: string;
  skills: JobSkill[];
  applicant_count?: number;
}

export interface CandidateSkill {
  id?: string;
  skill: string;
  years_experience: number;
  confidence_score: number;
}

export interface Candidate {
  id: string;
  name: string;
  email: string;
  phone?: string;
  location: string;
  total_experience: number;
  education_level: 'BACHELORS' | 'MASTERS' | 'PHD' | 'DIPLOMA' | 'SELF_TAUGHT' | 'OTHER';
  education_details?: string;
  resume_filename?: string;
  resume_path?: string;
  resume_raw_text?: string;
  summary?: string;
  created_at: string;
  skills?: CandidateSkill[];
}

export interface ScoreExplanation {
  matched_required_skills: string[];
  missing_required_skills: string[];
  matched_preferred_skills: string[];
  missing_preferred_skills: string[];
  experience_summary: string;
  education_summary: string;
  natural_language_explanation: string;
}

export type ApplicationStatus =
  | 'NEW'
  | 'SCREENING'
  | 'SHORTLISTED'
  | 'CONTACTED'
  | 'INTERVIEW'
  | 'SELECTED'
  | 'REJECTED'
  | 'HIRED';

export interface Application {
  id: string;
  job_id: string;
  candidate_id: string;
  match_score: number;
  required_skills_score: number;
  preferred_skills_score: number;
  experience_score: number;
  education_score: number;
  semantic_score: number;
  score_explanation?: ScoreExplanation | string;
  status: ApplicationStatus;
  recruiter_notes?: string;
  applied_at: string;
  candidate?: Candidate;
  job?: Job;
}

export interface Note {
  id: string;
  candidate_id: string;
  recruiter_id?: string;
  recruiter_name?: string;
  note: string;
  created_at: string;
}

export interface Interview {
  id: string;
  application_id: string;
  candidate_id?: string;
  candidate_name?: string;
  job_title?: string;
  company?: string;
  interview_date: string;
  interview_type: 'SCREENING' | 'TECHNICAL' | 'BEHAVIORAL' | 'FINAL' | string;
  interviewer: string;
  status: 'SCHEDULED' | 'COMPLETED' | 'CANCELLED' | 'NO_SHOW' | string;
  feedback?: string;
  rating?: number;
  created_at?: string;
}

export interface Followup {
  id: string;
  candidate_id: string;
  recruiter_id?: string;
  candidate_name?: string;
  candidate_email?: string;
  followup_date: string;
  method: 'CALL' | 'EMAIL' | 'LINKEDIN' | 'MEETING' | string;
  status: 'PENDING' | 'COMPLETED' | 'OVERDUE' | string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface HealthCheckResponse {
  status: string;
  app_name: string;
  version: string;
  database: string;
  environment: string;
}

export interface MatchWeightConfig {
  weight_required_skills: number;
  weight_preferred_skills: number;
  weight_experience: number;
  weight_education: number;
  weight_semantic: number;
}

export interface CandidateMatchResult {
  candidate: Candidate;
  application_id?: string;
  overall_score: number;
  required_skills_score: number;
  preferred_skills_score: number;
  experience_score: number;
  education_score: number;
  semantic_score: number;
  status: ApplicationStatus | string;
  recruiter_notes?: string;
  explanation: ScoreExplanation;
}

export interface RankedMatchesResponse {
  job_id: string;
  job_title: string;
  total_evaluated: number;
  matches: CandidateMatchResult[];
  weight_config: MatchWeightConfig;
}

export interface FunnelStageMetric {
  stage: string;
  count: number;
  conversion_rate: number;
}

export interface ScoreBucketMetric {
  bucket: string;
  count: number;
  label: string;
}

export interface SkillDemandSupplyMetric {
  skill: string;
  job_demand_count: number;
  talent_supply_count: number;
}

export interface EducationDistributionMetric {
  level: string;
  count: number;
  percentage: number;
}

export interface RecentActivityItem {
  id: string;
  type: 'APPLICATION' | 'STAGE_CHANGE' | 'INTERVIEW' | 'NOTE' | string;
  title: string;
  description: string;
  timestamp: string;
}

export interface AnalyticsOverviewResponse {
  total_jobs: number;
  active_jobs: number;
  total_candidates: number;
  total_applications: number;
  hired_count: number;
  interviewing_count: number;
  average_match_score: number;
  funnel: FunnelStageMetric[];
  score_distribution: ScoreBucketMetric[];
  skills_gap: SkillDemandSupplyMetric[];
  education_breakdown: EducationDistributionMetric[];
  recent_activity: RecentActivityItem[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  intent?: string;
  results?: any[];
  suggested_actions?: string[];
  candidate_id?: string;
  job_id?: string;
}

export interface ChatQueryResponse {
  reply: string;
  intent: string;
  candidate_id?: string;
  job_id?: string;
  results?: any[];
  suggested_actions: string[];
}

export interface SemanticSearchResult {
  candidate_id: string;
  name: string;
  skills: string[];
  experience: number;
  location: string;
  email: string;
  summary: string;
  similarity_score: number;
  raw_cosine: number;
}

export interface CandidateComparisonItem {
  candidate: Candidate;
  overall_match_score?: number;
  required_skills_score?: number;
  preferred_skills_score?: number;
  experience_score?: number;
  education_score?: number;
  semantic_score?: number;
  matched_skills: string[];
  missing_skills: string[];
  unique_skills: string[];
}

export interface ComparisonMatrixResponse {
  job?: Job;
  candidates: CandidateComparisonItem[];
  common_skills: string[];
  all_compared_skills: string[];
  skill_matrix: Record<string, Record<string, boolean>>;
  ai_comparative_synthesis: string;
}




