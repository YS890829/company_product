/**
 * Revenue Intelligence Platform - API Client
 *
 * Next.js API Routes と FastAPI Microservice への統一インターフェース
 *
 * @usage
 * const client = new APIClient();
 * const companies = await client.getCompanies();
 * const dealRisk = await client.analyzeDealRisk(dealData);
 */

import type {
  Company,
  Deal,
  Meeting,
  Email,
  DealRiskScore,
  WinRateAnalysis,
  NextAction,
  RevenueForecast,
  ChurnRiskPrediction,
  UpsellOpportunity,
  CompetitorAnalysis,
  SalesPerformance,
  MeetingSummary,
  DealProgress,
  NextBestActionRequest,
  RiskAlert,
  ProposalDraft,
  EmailWorkerResult,
  DocumentWorkerResult,
  CRMWorkerResult,
  MultiAgentWorkflowResult,
  WorkflowState,
  APIResponse,
} from './types';

/**
 * APIClient: 全てのAPI呼び出しを管理するクラス
 */
export class APIClient {
  private nextApiBase: string;
  private fastApiBase: string;

  constructor() {
    // 環境変数から取得（ブラウザ側で動作）
    this.nextApiBase = process.env.NEXT_PUBLIC_API_URL || '';
    this.fastApiBase = process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000';
  }

  // =====================================
  // Helper: HTTP Request Wrapper
  // =====================================

  /**
   * fetchWithErrorHandling: エラーハンドリング付きfetch
   */
  private async fetchWithErrorHandling<T>(
    url: string,
    options?: RequestInit
  ): Promise<T> {
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `API Error: ${response.status} ${response.statusText} - ${errorText}`
        );
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('API Request Failed:', error);
      throw error;
    }
  }

  // =====================================
  // Next.js API Routes (Supabase Data)
  // =====================================

  /**
   * getCompanies: 全会社データ取得
   */
  async getCompanies(): Promise<Company[]> {
    const response = await this.fetchWithErrorHandling<{ companies: Company[] }>(
      `${this.nextApiBase}/api/companies`
    );
    return response.companies;
  }

  /**
   * getCompany: 会社データ取得（ID指定）
   */
  async getCompany(companyId: string): Promise<Company> {
    const response = await this.fetchWithErrorHandling<{ company: Company }>(
      `${this.nextApiBase}/api/companies/${companyId}`
    );
    return response.company;
  }

  /**
   * getDeals: 商談データ取得（会社ID指定可）
   */
  async getDeals(companyId?: string): Promise<Deal[]> {
    const url = companyId
      ? `${this.nextApiBase}/api/deals?company_id=${companyId}`
      : `${this.nextApiBase}/api/deals`;

    const response = await this.fetchWithErrorHandling<{ deals: Deal[] }>(url);
    return response.deals;
  }

  /**
   * getDeal: 商談データ取得（ID指定）
   */
  async getDeal(dealId: string): Promise<Deal> {
    const response = await this.fetchWithErrorHandling<{ deal: Deal }>(
      `${this.nextApiBase}/api/deals/${dealId}`
    );
    return response.deal;
  }

  /**
   * getMeetings: ミーティングデータ取得（商談ID指定可）
   */
  async getMeetings(dealId?: string): Promise<Meeting[]> {
    const url = dealId
      ? `${this.nextApiBase}/api/meetings?deal_id=${dealId}`
      : `${this.nextApiBase}/api/meetings`;

    const response = await this.fetchWithErrorHandling<{ meetings: Meeting[] }>(url);
    return response.meetings;
  }

  /**
   * getEmails: メールデータ取得（商談ID指定可）
   */
  async getEmails(dealId?: string): Promise<Email[]> {
    const url = dealId
      ? `${this.nextApiBase}/api/emails?deal_id=${dealId}`
      : `${this.nextApiBase}/api/emails`;

    const response = await this.fetchWithErrorHandling<{ emails: Email[] }>(url);
    return response.emails;
  }

  // =====================================
  // FastAPI - Revenue Intelligence (10機能)
  // =====================================

  /**
   * analyzeDealRisk: 商談リスク分析
   */
  async analyzeDealRisk(dealData: {
    deal_id: string;
    deal_name: string;
    stage: string;
    amount: number;
    last_contact_days: number;
    engagement_score: number;
  }): Promise<DealRiskScore> {
    const response = await this.fetchWithErrorHandling<APIResponse<DealRiskScore>>(
      `${this.fastApiBase}/api/analyze-deal-risk`,
      {
        method: 'POST',
        body: JSON.stringify(dealData),
      }
    );
    return response.data!;
  }

  /**
   * analyzeWinRate: 成約率分析
   */
  async analyzeWinRate(companyId: string): Promise<WinRateAnalysis> {
    // Step 1: Supabaseから商談データ取得
    const deals = await this.getDeals(companyId);

    // Step 2: FastAPIに商談データを送信
    const response = await this.fetchWithErrorHandling<APIResponse<WinRateAnalysis>>(
      `${this.fastApiBase}/api/analyze-win-rate`,
      {
        method: 'POST',
        body: JSON.stringify({ deals }),
      }
    );
    return response.data!;
  }

  /**
   * generateNextActions: 次のアクション提案
   */
  async generateNextActions(dealId: string): Promise<NextAction[]> {
    const response = await this.fetchWithErrorHandling<APIResponse<{ actions: NextAction[] }>>(
      `${this.fastApiBase}/api/generate-next-actions`,
      {
        method: 'POST',
        body: JSON.stringify({ deal_id: dealId }),
      }
    );
    return response.data!.actions;
  }

  /**
   * forecastRevenue: 売上予測
   */
  async forecastRevenue(companyId: string): Promise<RevenueForecast> {
    // Step 1: Supabaseから商談データ取得
    const deals = await this.getDeals(companyId);

    // Step 2: FastAPIに商談データを送信
    const response = await this.fetchWithErrorHandling<APIResponse<RevenueForecast>>(
      `${this.fastApiBase}/api/forecast-revenue`,
      {
        method: 'POST',
        body: JSON.stringify({ deals }),
      }
    );
    return response.data!;
  }

  /**
   * predictChurnRisk: チャーンリスク予測
   */
  async predictChurnRisk(companyId: string): Promise<ChurnRiskPrediction> {
    const response = await this.fetchWithErrorHandling<APIResponse<ChurnRiskPrediction>>(
      `${this.fastApiBase}/api/predict-churn-risk`,
      {
        method: 'POST',
        body: JSON.stringify({ company_id: companyId }),
      }
    );
    return response.data!;
  }

  /**
   * detectUpsellOpportunities: アップセル機会検知
   */
  async detectUpsellOpportunities(companyId: string): Promise<UpsellOpportunity[]> {
    const response = await this.fetchWithErrorHandling<APIResponse<{ opportunities: UpsellOpportunity[] }>>(
      `${this.fastApiBase}/api/detect-upsell-opportunities`,
      {
        method: 'POST',
        body: JSON.stringify({ company_id: companyId }),
      }
    );
    return response.data!.opportunities;
  }

  /**
   * analyzeCompetitors: 競合分析
   */
  async analyzeCompetitors(companyId: string): Promise<CompetitorAnalysis> {
    const response = await this.fetchWithErrorHandling<APIResponse<CompetitorAnalysis>>(
      `${this.fastApiBase}/api/analyze-competitors`,
      {
        method: 'POST',
        body: JSON.stringify({ company_id: companyId }),
      }
    );
    return response.data!;
  }

  /**
   * analyzeSalesPerformance: 営業パフォーマンス分析
   */
  async analyzeSalesPerformance(companyId: string): Promise<SalesPerformance> {
    const response = await this.fetchWithErrorHandling<APIResponse<SalesPerformance>>(
      `${this.fastApiBase}/api/analyze-sales-performance`,
      {
        method: 'POST',
        body: JSON.stringify({ company_id: companyId }),
      }
    );
    return response.data!;
  }

  /**
   * summarizeMeetings: ミーティング要約
   */
  async summarizeMeetings(dealId: string): Promise<MeetingSummary[]> {
    const response = await this.fetchWithErrorHandling<APIResponse<{ summaries: MeetingSummary[] }>>(
      `${this.fastApiBase}/api/summarize-meetings`,
      {
        method: 'POST',
        body: JSON.stringify({ deal_id: dealId }),
      }
    );
    return response.data!.summaries;
  }

  /**
   * trackDealProgress: 商談進捗トラッキング
   */
  async trackDealProgress(dealId: string): Promise<DealProgress> {
    const response = await this.fetchWithErrorHandling<APIResponse<DealProgress>>(
      `${this.fastApiBase}/api/track-deal-progress`,
      {
        method: 'POST',
        body: JSON.stringify({ deal_id: dealId }),
      }
    );
    return response.data!;
  }

  // =====================================
  // FastAPI - Suggestion Engine (3機能)
  // =====================================

  /**
   * suggestNextBestAction: Next Best Action提案
   */
  async suggestNextBestAction(request: NextBestActionRequest): Promise<NextAction[]> {
    const response = await this.fetchWithErrorHandling<APIResponse<{ actions: NextAction[] }>>(
      `${this.fastApiBase}/api/suggest-next-best-action`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );
    return response.data!.actions;
  }

  /**
   * detectRiskAlerts: リスク検出
   */
  async detectRiskAlerts(deals: Array<{ deal_id: string; risk_score: number }>): Promise<RiskAlert[]> {
    const response = await this.fetchWithErrorHandling<APIResponse<{ alerts: RiskAlert[] }>>(
      `${this.fastApiBase}/api/detect-risk-alerts`,
      {
        method: 'POST',
        body: JSON.stringify({ deals }),
      }
    );
    return response.data!.alerts;
  }

  /**
   * generateProposalDraft: 提案書ドラフト生成
   */
  async generateProposalDraft(data: {
    company_name: string;
    industry: string;
    pain_points: string;
  }): Promise<ProposalDraft> {
    const response = await this.fetchWithErrorHandling<APIResponse<ProposalDraft>>(
      `${this.fastApiBase}/api/generate-proposal-draft`,
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    );
    return response.data!;
  }

  // =====================================
  // FastAPI - CrewAI Multi-Agent (4エンドポイント)
  // =====================================

  /**
   * runEmailWorker: Email Worker実行
   */
  async runEmailWorker(data: {
    deal_name: string;
    last_meeting_summary: string;
    next_action: string;
  }): Promise<EmailWorkerResult> {
    const response = await this.fetchWithErrorHandling<APIResponse<EmailWorkerResult>>(
      `${this.fastApiBase}/api/agents/email`,
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    );
    return response.data!;
  }

  /**
   * runDocumentWorker: Document Worker実行
   */
  async runDocumentWorker(transcript: string): Promise<DocumentWorkerResult> {
    const response = await this.fetchWithErrorHandling<APIResponse<DocumentWorkerResult>>(
      `${this.fastApiBase}/api/agents/document`,
      {
        method: 'POST',
        body: JSON.stringify({ transcript }),
      }
    );
    return response.data!;
  }

  /**
   * runCRMWorker: CRM Worker実行
   */
  async runCRMWorker(dealData: Record<string, unknown>): Promise<CRMWorkerResult> {
    const response = await this.fetchWithErrorHandling<APIResponse<CRMWorkerResult>>(
      `${this.fastApiBase}/api/agents/crm`,
      {
        method: 'POST',
        body: JSON.stringify({ deal_data: dealData }),
      }
    );
    return response.data!;
  }

  /**
   * runMultiAgentWorkflow: Multi-Agent Workflow実行
   */
  async runMultiAgentWorkflow(dealId: string): Promise<MultiAgentWorkflowResult> {
    const response = await this.fetchWithErrorHandling<APIResponse<MultiAgentWorkflowResult>>(
      `${this.fastApiBase}/api/agents/workflow`,
      {
        method: 'POST',
        body: JSON.stringify({ deal_id: dealId }),
      }
    );
    return response.data!;
  }

  // =====================================
  // FastAPI - LangGraph Workflow (1エンドポイント)
  // =====================================

  /**
   * executeWorkflow: LangGraph Workflow実行
   */
  async executeWorkflow(data: { deal_id: string; stage: string }): Promise<WorkflowState> {
    const response = await this.fetchWithErrorHandling<APIResponse<WorkflowState>>(
      `${this.fastApiBase}/api/workflow/execute`,
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    );
    return response.data!;
  }
}

/**
 * デフォルトエクスポート: シングルトンインスタンス
 */
export const apiClient = new APIClient();
