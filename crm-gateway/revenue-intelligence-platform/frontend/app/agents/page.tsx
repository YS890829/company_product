/**
 * AI Agents Page - AI Agents実行画面
 *
 * CrewAI Multi-Agent と LangGraph Workflow を実行できる画面
 */

'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Card } from '@/components/ui/Card';
import { apiClient } from '@/lib/api-client';
import Link from 'next/link';
import type { MultiAgentWorkflowResult, WorkflowState } from '@/lib/types';

export default function AgentsPage() {
  const [selectedDealId, setSelectedDealId] = useState<string>('');
  const [multiAgentResult, setMultiAgentResult] = useState<MultiAgentWorkflowResult | null>(null);
  const [langGraphResult, setLangGraphResult] = useState<WorkflowState | null>(null);
  const [nextBestActionResult, setNextBestActionResult] = useState<any>(null);
  const [riskDetectionResult, setRiskDetectionResult] = useState<any>(null);
  const [proposalDraftResult, setProposalDraftResult] = useState<any>(null);

  // 商談一覧取得
  const { data: deals } = useQuery({
    queryKey: ['all-deals'],
    queryFn: async () => {
      const data = await apiClient.getDeals();
      if (data.length > 0 && !selectedDealId) {
        setSelectedDealId(data[0].id);
      }
      return data;
    },
  });

  // Multi-Agent Workflow実行
  const multiAgentMutation = useMutation({
    mutationFn: (dealId: string) => apiClient.runMultiAgentWorkflow(dealId),
    onSuccess: (data) => {
      setMultiAgentResult(data);
    },
  });

  // LangGraph Workflow実行
  const langGraphMutation = useMutation({
    mutationFn: (data: { deal_id: string; stage: string }) => apiClient.executeWorkflow(data),
    onSuccess: (data) => {
      setLangGraphResult(data);
    },
  });

  // Next Best Action実行
  const nextBestActionMutation = useMutation({
    mutationFn: (data: { deal_id: string; stage: string; risk_score: number }) =>
      apiClient.suggestNextBestAction(data),
    onSuccess: (actions) => {
      setNextBestActionResult({ actions });
    },
  });

  // Risk Detection実行
  const riskDetectionMutation = useMutation({
    mutationFn: (deals: Array<{ deal_id: string; risk_score: number }>) => apiClient.detectRiskAlerts(deals),
    onSuccess: (alerts) => {
      setRiskDetectionResult({ alerts });
    },
  });

  // Proposal Draft実行
  const proposalDraftMutation = useMutation({
    mutationFn: (data: { company_name: string; industry: string; deal_amount: number }) =>
      apiClient.generateProposalDraft(data),
    onSuccess: (proposal) => {
      setProposalDraftResult(proposal);
    },
  });

  const executeMultiAgent = () => {
    if (selectedDealId) {
      multiAgentMutation.mutate(selectedDealId);
    }
  };

  const executeLangGraph = () => {
    if (selectedDealId && deals) {
      const deal = deals.find(d => d.id === selectedDealId);
      if (deal) {
        langGraphMutation.mutate({ deal_id: selectedDealId, stage: deal.stage });
      }
    }
  };

  const executeNextBestAction = () => {
    if (selectedDealId && deals) {
      const deal = deals.find(d => d.id === selectedDealId);
      if (deal) {
        const engagementScore = deal.engagement_score ?? 0;
        const riskScore = 100 - engagementScore;
        nextBestActionMutation.mutate({
          deal_id: selectedDealId,
          stage: deal.stage,
          risk_score: riskScore
        });
      }
    }
  };

  const executeRiskDetection = () => {
    if (deals && deals.length > 0) {
      const dealsData = deals.slice(0, 5).map(d => ({
        deal_id: d.id,
        risk_score: 100 - (d.engagement_score ?? 0)
      }));
      riskDetectionMutation.mutate(dealsData);
    }
  };

  const executeProposalDraft = () => {
    if (selectedDealId && deals) {
      const deal = deals.find(d => d.id === selectedDealId);
      if (deal) {
        proposalDraftMutation.mutate({
          company_name: deal.customer_name,
          industry: deal.customer_industry || 'SaaS',
          deal_amount: deal.amount
        });
      }
    }
  };

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-black">
      {/* Header */}
      <header className="bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">
              AI Agents Workflow
            </h1>
            <Link
              href="/dashboard"
              className="px-4 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 hover:bg-zinc-50 dark:hover:bg-zinc-800 text-sm font-medium text-zinc-900 dark:text-zinc-50 transition-colors"
            >
              ← ダッシュボード
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 商談選択 */}
        <Card title="商談選択" className="mb-6">
          <div className="flex items-center gap-4">
            <label htmlFor="deal-select" className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
              商談:
            </label>
            <select
              id="deal-select"
              value={selectedDealId}
              onChange={(e) => setSelectedDealId(e.target.value)}
              className="flex-1 px-4 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {deals?.map((deal) => (
                <option key={deal.id} value={deal.id}>
                  {deal.customer_name} - {deal.next_action || deal.stage} ({deal.stage})
                </option>
              ))}
            </select>
          </div>
        </Card>

        {/* Suggestion Engine Section */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-50 mb-4">
            Suggestion Engine
          </h2>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Next Best Action */}
            <Card title="Next Best Action" className="lg:col-span-1">
              <div className="space-y-4">
                <button
                  onClick={executeNextBestAction}
                  disabled={!selectedDealId || nextBestActionMutation.isPending}
                  className="w-full px-6 py-3 rounded-lg bg-green-600 hover:bg-green-700 disabled:bg-zinc-400 text-white font-medium transition-colors"
                >
                  {nextBestActionMutation.isPending ? '実行中...' : '次のアクション提案'}
                </button>

                {nextBestActionResult && (
                  <div className="space-y-3 mt-4">
                    {nextBestActionResult.actions?.map((action: any, index: number) => (
                      <div
                        key={index}
                        className={`p-3 rounded-lg border ${
                          action.priority === 'urgent' ? 'border-red-300 bg-red-50 dark:border-red-800 dark:bg-red-950' :
                          action.priority === 'high' ? 'border-orange-300 bg-orange-50 dark:border-orange-800 dark:bg-orange-950' :
                          action.priority === 'medium' ? 'border-yellow-300 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-950' :
                          'border-blue-300 bg-blue-50 dark:border-blue-800 dark:bg-blue-950'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
                            {action.action}
                          </h4>
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            action.priority === 'urgent' ? 'bg-red-200 text-red-800 dark:bg-red-900 dark:text-red-200' :
                            action.priority === 'high' ? 'bg-orange-200 text-orange-800 dark:bg-orange-900 dark:text-orange-200' :
                            action.priority === 'medium' ? 'bg-yellow-200 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' :
                            'bg-blue-200 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                          }`}>
                            {action.priority}
                          </span>
                        </div>
                        <p className="text-sm text-zinc-600 dark:text-zinc-400">
                          {action.rationale || action.reason}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </Card>

            {/* Risk Detection */}
            <Card title="Risk Detection" className="lg:col-span-1">
              <div className="space-y-4">
                <button
                  onClick={executeRiskDetection}
                  disabled={!deals || deals.length === 0 || riskDetectionMutation.isPending}
                  className="w-full px-6 py-3 rounded-lg bg-red-600 hover:bg-red-700 disabled:bg-zinc-400 text-white font-medium transition-colors"
                >
                  {riskDetectionMutation.isPending ? '実行中...' : 'リスク検知（全商談）'}
                </button>

                {riskDetectionResult && (
                  <div className="space-y-3 mt-4">
                    {riskDetectionResult.alerts?.slice(0, 3).map((alert: any, index: number) => {
                      const urgency = alert.urgency || alert.severity;
                      return (
                      <div
                        key={index}
                        className={`p-3 rounded-lg border ${
                          urgency === 'critical' ? 'border-red-300 bg-red-50 dark:border-red-800 dark:bg-red-950' :
                          urgency === 'high' ? 'border-orange-300 bg-orange-50 dark:border-orange-800 dark:bg-orange-950' :
                          urgency === 'medium' ? 'border-yellow-300 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-950' :
                          'border-blue-300 bg-blue-50 dark:border-blue-800 dark:bg-blue-950'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
                            {alert.deal_name || `商談 ${index + 1}`}
                          </h4>
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            urgency === 'critical' ? 'bg-red-200 text-red-800 dark:bg-red-900 dark:text-red-200' :
                            urgency === 'high' ? 'bg-orange-200 text-orange-800 dark:bg-orange-900 dark:text-orange-200' :
                            urgency === 'medium' ? 'bg-yellow-200 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' :
                            'bg-blue-200 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                          }`}>
                            {urgency}
                          </span>
                        </div>
                        <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-2">
                          リスクスコア: {alert.risk_score}
                        </p>
                        <p className="text-sm text-zinc-600 dark:text-zinc-400">
                          推奨: {alert.recommended_action || (alert.recommended_actions && alert.recommended_actions.join(', '))}
                        </p>
                      </div>
                    );})}
                    {riskDetectionResult.alerts?.length > 3 && (
                      <p className="text-sm text-zinc-600 dark:text-zinc-400 text-center">
                        他 {riskDetectionResult.alerts.length - 3} 件のアラート
                      </p>
                    )}
                  </div>
                )}
              </div>
            </Card>

            {/* Proposal Generation */}
            <Card title="Proposal Generation" className="lg:col-span-1">
              <div className="space-y-4">
                <button
                  onClick={executeProposalDraft}
                  disabled={!selectedDealId || proposalDraftMutation.isPending}
                  className="w-full px-6 py-3 rounded-lg bg-purple-600 hover:bg-purple-700 disabled:bg-zinc-400 text-white font-medium transition-colors"
                >
                  {proposalDraftMutation.isPending ? '実行中...' : '提案書生成'}
                </button>

                {proposalDraftResult && (
                  <div className="space-y-3 mt-4">
                    <div className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800 max-h-96 overflow-y-auto">
                      <h4 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50 mb-3 sticky top-0 bg-white dark:bg-zinc-900 pb-2">
                        {proposalDraftResult.title || '提案書タイトル'}
                      </h4>
                      <div className="space-y-3">
                        {proposalDraftResult.sections?.map((section: any, index: number) => (
                          <div key={index} className="pb-3 border-b border-zinc-200 dark:border-zinc-800 last:border-b-0">
                            <h5 className="text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-1">
                              {section.heading}
                            </h5>
                            <p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
                              {section.content}
                            </p>
                          </div>
                        ))}
                      </div>
                      {proposalDraftResult.metadata && (
                        <div className="mt-3 pt-3 border-t border-zinc-200 dark:border-zinc-800 sticky bottom-0 bg-white dark:bg-zinc-900">
                          <p className="text-xs text-zinc-600 dark:text-zinc-400">
                            読了時間: {proposalDraftResult.metadata.estimated_reading_time}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </Card>
          </div>
        </div>

        {/* Multi-Agent Systems Section */}
        <div>
          <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-50 mb-4">
            Multi-Agent Systems
          </h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* CrewAI Multi-Agent */}
          <Card title="CrewAI Multi-Agent Workflow" className="lg:col-span-1">
            <div className="space-y-4">
              {/* Workers Status */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 text-center">
                  <div className="text-xs text-zinc-600 dark:text-zinc-400 mb-1">Email Worker</div>
                  <div className="text-sm font-semibold text-green-600 dark:text-green-400">Ready</div>
                </div>
                <div className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 text-center">
                  <div className="text-xs text-zinc-600 dark:text-zinc-400 mb-1">Document Worker</div>
                  <div className="text-sm font-semibold text-green-600 dark:text-green-400">Ready</div>
                </div>
                <div className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 text-center">
                  <div className="text-xs text-zinc-600 dark:text-zinc-400 mb-1">CRM Worker</div>
                  <div className="text-sm font-semibold text-green-600 dark:text-green-400">Ready</div>
                </div>
              </div>

              {/* Execute Button */}
              <button
                onClick={executeMultiAgent}
                disabled={!selectedDealId || multiAgentMutation.isPending}
                className="w-full px-6 py-3 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-400 text-white font-medium transition-colors"
              >
                {multiAgentMutation.isPending ? '実行中...' : 'Multi-Agent Workflow 実行'}
              </button>

              {/* Results */}
              {multiAgentResult && (
                <div className="space-y-3 mt-4">
                  <div className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800">
                    <h4 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50 mb-2">
                      ミーティング分析
                    </h4>
                    <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-2">
                      {multiAgentResult.meeting_analysis.summary}
                    </p>
                    {multiAgentResult.meeting_analysis.key_points && multiAgentResult.meeting_analysis.key_points.length > 0 && (
                      <div className="mt-2">
                        <p className="text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-1">キーポイント:</p>
                        <ul className="list-disc list-inside text-xs text-zinc-600 dark:text-zinc-400 space-y-1">
                          {multiAgentResult.meeting_analysis.key_points.map((point: string, idx: number) => (
                            <li key={idx}>{point}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {multiAgentResult.meeting_analysis.action_items && multiAgentResult.meeting_analysis.action_items.length > 0 && (
                      <div className="mt-2">
                        <p className="text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-1">アクションアイテム:</p>
                        <ul className="list-disc list-inside text-xs text-zinc-600 dark:text-zinc-400 space-y-1">
                          {multiAgentResult.meeting_analysis.action_items.map((item: string, idx: number) => (
                            <li key={idx}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {multiAgentResult.meeting_analysis.sentiment && (
                      <div className="mt-2">
                        <span className="text-xs text-zinc-700 dark:text-zinc-300">センチメント: </span>
                        <span className={`text-xs font-semibold ${
                          multiAgentResult.meeting_analysis.sentiment === 'positive' ? 'text-green-600' :
                          multiAgentResult.meeting_analysis.sentiment === 'negative' ? 'text-red-600' :
                          'text-yellow-600'
                        }`}>
                          {multiAgentResult.meeting_analysis.sentiment}
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800">
                    <h4 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50 mb-2">
                      CRM更新提案
                    </h4>
                    <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-2">
                      品質スコア: {multiAgentResult.crm_updates.data_quality_score}/100
                    </p>
                    {multiAgentResult.crm_updates.field_updates && Object.keys(multiAgentResult.crm_updates.field_updates).length > 0 && (
                      <div className="mt-2">
                        <p className="text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-1">フィールド更新提案:</p>
                        <ul className="list-disc list-inside text-xs text-zinc-600 dark:text-zinc-400 space-y-1">
                          {Object.entries(multiAgentResult.crm_updates.field_updates).map(([key, value]: [string, any], idx: number) => (
                            <li key={idx}><strong>{key}:</strong> {value}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {multiAgentResult.crm_updates.missing_info && multiAgentResult.crm_updates.missing_info.length > 0 && (
                      <div className="mt-2">
                        <p className="text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-1">不足情報:</p>
                        <ul className="list-disc list-inside text-xs text-zinc-600 dark:text-zinc-400 space-y-1">
                          {multiAgentResult.crm_updates.missing_info.map((info: string, idx: number) => (
                            <li key={idx}>{info}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  <div className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800">
                    <h4 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50 mb-2">
                      フォローメール
                    </h4>
                    <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-2">
                      <strong>件名:</strong> {multiAgentResult.followup_email.email_subject}
                    </p>
                    <p className="text-sm text-zinc-600 dark:text-zinc-400 whitespace-pre-wrap">
                      {multiAgentResult.followup_email.email_body}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </Card>

          {/* LangGraph Workflow */}
          <Card title="LangGraph State Orchestration" className="lg:col-span-1">
            <div className="space-y-4">
              {/* Workflow Diagram */}
              <div className="p-4 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900">
                <div className="text-xs text-center text-zinc-600 dark:text-zinc-400 mb-3">
                  Workflow ステップ
                </div>
                <div className="flex items-center justify-between text-xs">
                  <div className="flex-1 text-center p-2 rounded-md bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                    Risk Assessment
                  </div>
                  <div className="px-2">→</div>
                  <div className="flex-1 text-center p-2 rounded-md bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                    Generate Actions
                  </div>
                  <div className="px-2">→</div>
                  <div className="flex-1 text-center p-2 rounded-md bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                    Send Email
                  </div>
                  <div className="px-2">→</div>
                  <div className="flex-1 text-center p-2 rounded-md bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                    Update CRM
                  </div>
                </div>
              </div>

              {/* Execute Button */}
              <button
                onClick={executeLangGraph}
                disabled={!selectedDealId || langGraphMutation.isPending}
                className="w-full px-6 py-3 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:bg-zinc-400 text-white font-medium transition-colors"
              >
                {langGraphMutation.isPending ? '実行中...' : 'LangGraph Workflow 実行'}
              </button>

              {/* Results */}
              {langGraphResult && (
                <div className="space-y-3 mt-4">
                  <div className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800">
                    <h4 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50 mb-2">
                      ワークフロー結果
                    </h4>
                    <div className="space-y-2 text-sm">
                      {langGraphResult.deal_name && (
                        <div className="flex items-center justify-between">
                          <span className="text-zinc-600 dark:text-zinc-400">商談名:</span>
                          <span className="text-zinc-900 dark:text-zinc-50 font-medium">
                            {langGraphResult.deal_name}
                          </span>
                        </div>
                      )}
                      <div className="flex items-center justify-between">
                        <span className="text-zinc-600 dark:text-zinc-400">リスクスコア:</span>
                        <span className={`font-medium ${
                          langGraphResult.risk_score >= 70 ? 'text-red-600 dark:text-red-400' :
                          langGraphResult.risk_score >= 50 ? 'text-orange-600 dark:text-orange-400' :
                          'text-green-600 dark:text-green-400'
                        }`}>
                          {langGraphResult.risk_score}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-zinc-600 dark:text-zinc-400">メール送信:</span>
                        <span className={langGraphResult.email_sent ? 'text-green-600 dark:text-green-400' : 'text-zinc-600 dark:text-zinc-400'}>
                          {langGraphResult.email_sent ? '✓ 送信済' : '✗ スキップ'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-zinc-600 dark:text-zinc-400">CRM更新:</span>
                        <span className={langGraphResult.crm_updated ? 'text-green-600 dark:text-green-400' : 'text-zinc-600 dark:text-zinc-400'}>
                          {langGraphResult.crm_updated ? '✓ 更新済' : '✗ 未更新'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {(langGraphResult.nodes_executed || langGraphResult.workflow_steps) && (
                    <div className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800">
                      <h4 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50 mb-2">
                        実行ノード
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {(langGraphResult.nodes_executed || langGraphResult.workflow_steps)?.map((node, index) => (
                          <span
                            key={index}
                            className="px-2 py-1 rounded-md bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-200 text-xs"
                          >
                            {node}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </Card>
        </div>
        </div>
      </main>
    </div>
  );
}
