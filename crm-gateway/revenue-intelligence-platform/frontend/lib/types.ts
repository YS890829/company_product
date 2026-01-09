/**
 * Revenue Intelligence Platform - TypeScript Type Definitions
 *
 * 全てのAPI レスポンス、リクエスト、データモデルの型定義
 */

// =====================================
// Database Models (Supabase)
// =====================================

/**
 * Company: 会社データ
 */
export interface Company {
  id: string;
  name: string;
  industry: string;
  created_at: string;
}

/**
 * Stakeholder: 意思決定者情報
 */
export interface Stakeholder {
  name: string;
  role: string;
  email: string;
  phone?: string;
  influence: 'high' | 'medium' | 'low';
  engagement_level?: 'high' | 'medium' | 'low';
}

/**
 * Deal: 商談データ
 */
export interface Deal {
  id: string;
  company_id: string;
  owner_name: string;
  deal_name?: string;
  stage: DealStage | string;
  amount: number;
  close_date: string | null;
  customer_size: number | null;
  probability: number | null;
  next_action: string | null;
  next_action_date: string | null;
  expected_close_date: string | null;
  budget_confirmed?: boolean;
  decision_maker_identified?: boolean;
  stakeholders: Stakeholder[] | null; // DB実カラム: stakeholders (jsonb型)
  created_at: string;
  updated_at: string;
  // Additional fields from database
  customer_name: string;
  customer_industry: string | null;
  risk_factors: string[];
  strengths: string[];
  company_name: string;
  // Legacy fields (optional for backwards compatibility)
  salesperson_name?: string;
  engagement_score?: number;
  pain_points?: string | null;
  last_contact_date?: string | null;
}

/**
 * DealStage: 商談ステージ
 */
export type DealStage =
  | 'prospect'
  | 'qualification'
  | 'proposal'
  | 'negotiation'
  | 'closed_won'
  | 'closed_lost';

/**
 * Meeting: ミーティングデータ
 */
export interface Meeting {
  id: string;
  deal_id: string;
  date: string; // DB実カラム名: date (meeting_date から変更)
  transcript: string | null;
  attendees: string[] | null;
  duration_minutes: number | null;
  sentiment_analysis: { // DB実カラム名: sentiment_analysis (jsonb型)
    overall: MeetingSentiment;
    confidence: number;
  } | null;
  meeting_type: string | null; // DB実カラム: meeting_type
  location: string | null; // DB実カラム: location
  summary: string | null; // DB実カラム: summary
  action_items: string[] | null; // DB実カラム: action_items
  created_at: string;
}

/**
 * MeetingSentiment: ミーティング感情
 */
export type MeetingSentiment = 'positive' | 'neutral' | 'negative';

/**
 * Email: メールデータ
 */
export interface Email {
  id: string;
  deal_id: string;
  from_email: string; // DB実カラム: from_email
  to_email: string; // DB実カラム: to_email
  cc: string | null; // DB実カラム: cc
  subject: string;
  body: string;
  sent_at: string;
  opened: boolean | null; // DB実カラム: opened
  opened_at: string | null; // DB実カラム: opened_at
  clicked_links: string[] | null; // DB実カラム: clicked_links (配列)
  engagement_score: number | null; // DB実カラム: engagement_score (NUMERIC 3,2)
  attachments: string[] | null; // DB実カラム: attachments (配列)
  created_at: string;
}

// =====================================
// Revenue Intelligence API Types
// =====================================

/**
 * DealRiskScore: 商談リスクスコア
 */
export interface DealRiskScore {
  deal_id: string;
  deal_name: string;
  risk_score: number; // 0-100
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  risk_factors: string[];
  recommendations: string[];
}

/**
 * WinRateAnalysis: 成約率分析
 */
export interface WinRateAnalysis {
  overall_win_rate: number;
  total_deals: number;
  won_deals: number;
  lost_deals: number;
  by_stage: {
    stage: DealStage;
    win_rate: number;
    count: number;
  }[];
  by_salesperson: {
    name: string;
    win_rate: number;
    deals_count: number;
  }[];
}

/**
 * NextAction: 次のアクション提案
 */
export interface NextAction {
  action: string;
  priority: 'urgent' | 'high' | 'medium' | 'low';
  rationale: string;
  estimated_impact: string;
  deadline: string | null;
}

/**
 * RevenueForecast: 売上予測
 */
export interface RevenueForecast {
  forecasts: {
    month: string; // YYYY-MM
    predicted_revenue: number;
    confidence: number; // 0.0-1.0
  }[];
  total_predicted_revenue: number;
  average_confidence: number;
  growth_rate: number;
}

/**
 * ChurnRiskPrediction: チャーンリスク予測
 */
export interface ChurnRiskPrediction {
  company_id: string;
  company_name: string;
  churn_probability: number; // 0.0-1.0
  risk_level: 'low' | 'medium' | 'high';
  risk_factors: string[];
  recommended_actions: string[];
}

/**
 * UpsellOpportunity: アップセル機会
 */
export interface UpsellOpportunity {
  deal_id: string;
  company_name: string;
  current_plan: string;
  suggested_plan: string;
  upsell_score: number; // 0-100
  estimated_additional_revenue: number;
  timing: string;
  rationale: string;
}

/**
 * CompetitorAnalysis: 競合分析
 */
export interface CompetitorAnalysis {
  competitors: {
    name: string;
    encounter_count: number;
    win_rate: number;
    market_share: number;
    strengths: string[];
    weaknesses: string[];
  }[];
}

/**
 * SalesPerformance: 営業パフォーマンス
 */
export interface SalesPerformance {
  salesperson_rankings: {
    name: string;
    win_rate: number;
    total_revenue: number;
    deals_closed: number;
    avg_deal_size: number;
    kpi_achievement_rate: number;
  }[];
  top_performer: string;
  team_average_win_rate: number;
}

/**
 * MeetingSummary: ミーティング要約
 */
export interface MeetingSummary {
  meeting_id: string;
  meeting_date: string;
  summary: string;
  key_points: string[];
  action_items: string[];
  sentiment: MeetingSentiment;
}

/**
 * DealProgress: 商談進捗
 */
export interface DealProgress {
  deal_id: string;
  deal_name: string;
  current_stage: DealStage;
  progress_percentage: number;
  next_milestone: string;
  health_status: 'low' | 'medium' | 'high';
  days_in_current_stage: number;
}

// =====================================
// Suggestion Engine API Types
// =====================================

/**
 * NextBestActionRequest: Next Best Action リクエスト
 */
export interface NextBestActionRequest {
  deal_id: string;
  stage: DealStage;
  risk_score: number;
  last_contact_days: number;
  last_meeting_summary: string;
}

/**
 * RiskAlert: リスクアラート
 */
export interface RiskAlert {
  deal_id: string;
  deal_name: string;
  risk_score: number;
  urgency_level: 'critical' | 'high' | 'medium' | 'low';
  risk_factors: string[];
  recommended_actions: string[];
}

/**
 * ProposalDraft: 提案書ドラフト
 */
export interface ProposalDraft {
  company_name: string;
  industry: string;
  proposal: string;
  sections: {
    executive_summary: string;
    problem_analysis: string;
    solution_proposal: string;
    expected_outcomes: string;
    pricing: string;
    implementation_timeline: string;
  };
  metadata: {
    generated_at: string;
    word_count: number;
    estimated_read_time: string;
  };
}

// =====================================
// AI Agents API Types
// =====================================

/**
 * EmailWorkerResult: Email Worker 実行結果
 */
export interface EmailWorkerResult {
  email_subject: string;
  email_body: string;
  tone: string;
  word_count: number;
}

/**
 * DocumentWorkerResult: Document Worker 実行結果
 */
export interface DocumentWorkerResult {
  summary: string;
  key_points: string[];
  action_items: string[];
  sentiment: MeetingSentiment;
}

/**
 * CRMWorkerResult: CRM Worker 実行結果
 */
export interface CRMWorkerResult {
  field_updates: string;
  missing_info: string;
  data_quality_score: number;
}

/**
 * MultiAgentWorkflowResult: Multi-Agent Workflow 実行結果
 */
export interface MultiAgentWorkflowResult {
  meeting_analysis: DocumentWorkerResult;
  crm_updates: CRMWorkerResult;
  followup_email: EmailWorkerResult;
  workflow_summary: {
    total_workers_executed: number;
    execution_time: string;
    sentiment: MeetingSentiment;
  };
}

// =====================================
// LangGraph Workflow API Types
// =====================================

/**
 * WorkflowState: LangGraph ワークフロー状態
 */
export interface WorkflowState {
  deal_id: string;
  deal_name?: string;
  stage: DealStage | string;
  risk_score: number;
  next_actions: string[];
  email_sent: boolean;
  crm_updated: boolean;
  nodes_executed?: string[];
  workflow_steps?: string[];
  execution_time: string | number;
}

// =====================================
// API Response Wrappers
// =====================================

/**
 * APIResponse: 標準APIレスポンス
 */
export interface APIResponse<T> {
  status: 'success' | 'error';
  data?: T;
  error?: string;
  timestamp?: string;
}

/**
 * PaginatedResponse: ページネーション付きレスポンス
 */
export interface PaginatedResponse<T> {
  data: T[];
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}
