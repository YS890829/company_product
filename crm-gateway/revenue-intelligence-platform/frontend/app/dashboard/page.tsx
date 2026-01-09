/**
 * Dashboard Page - ダッシュボード画面
 *
 * Revenue Intelligence 10機能を全て表示:
 * 1. Revenue Forecasting (売上予測)
 * 2. High Risk Deals (高リスク商談)
 * 3. Win Rate Analysis (成約率分析)
 * 4. Churn Risk Prediction (チャーンリスク予測)
 * 5. Upsell Opportunities (アップセル機会検知)
 * 6. Competitor Analysis (競合分析)
 * 7. Sales Performance Analysis (営業パフォーマンス分析)
 * 8. Meeting Summary (ミーティング要約)
 * 9. Deal Progress Tracking (商談進捗トラッキング)
 * 10. Next Actions Suggestion (次のアクション提案)
 */

'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { usePathname, useRouter } from 'next/navigation';
import Link from 'next/link';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card } from '@/components/ui/Card';
import { apiClient } from '@/lib/api-client';
import type { Company } from '@/lib/types';

export default function DashboardPage() {
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>('');
  const pathname = usePathname();
  const router = useRouter();

  // 会社一覧取得
  const { data: companies, isLoading: companiesLoading } = useQuery({
    queryKey: ['companies'],
    queryFn: async () => {
      const data = await apiClient.getCompanies();
      if (data.length > 0 && !selectedCompanyId) {
        setSelectedCompanyId(data[0].id);
      }
      return data;
    },
  });

  // Revenue Forecasting (手動実行)
  const { data: revenueForecast, isLoading: forecastLoading, refetch: refetchForecast } = useQuery({
    queryKey: ['revenue-forecast', selectedCompanyId],
    queryFn: () => apiClient.forecastRevenue(selectedCompanyId),
    enabled: false,
  });

  // Deal Risk Scores (高リスク商談) - 商談データは常に取得（ミーティング要約のドロップダウンで使用）
  const { data: deals, isLoading: dealsLoading, refetch: refetchDeals } = useQuery({
    queryKey: ['deals', selectedCompanyId],
    queryFn: () => apiClient.getDeals(selectedCompanyId),
    enabled: !!selectedCompanyId,  // 会社が選択されている場合は自動取得
  });

  // Win Rate Analysis (手動実行)
  const { data: winRateAnalysis, isLoading: winRateLoading, refetch: refetchWinRate } = useQuery({
    queryKey: ['win-rate', selectedCompanyId],
    queryFn: () => apiClient.analyzeWinRate(selectedCompanyId),
    enabled: false,
  });

  // Churn Risk Prediction
  const { data: churnRisk, isLoading: churnLoading, refetch: refetchChurn } = useQuery({
    queryKey: ['churn-risk', selectedCompanyId],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/api/predict-churn-risk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_id: selectedCompanyId,
          engagement_score: 45,
        }),
      });
      const data = await response.json();
      return data.data;
    },
    enabled: false,
  });

  // Upsell Opportunities
  const { data: upsellOpps, isLoading: upsellLoading, refetch: refetchUpsell } = useQuery({
    queryKey: ['upsell-opportunities', selectedCompanyId],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/api/detect-upsell-opportunities', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ customer_id: selectedCompanyId }),
      });
      const data = await response.json();
      return data.data;
    },
    enabled: false,
  });

  // Competitor Analysis
  const { data: competitorAnalysis, isLoading: competitorLoading, refetch: refetchCompetitor } = useQuery({
    queryKey: ['competitor-analysis', selectedCompanyId],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/api/analyze-competitors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company_id: selectedCompanyId }),
      });
      const data = await response.json();
      return data.data;
    },
    enabled: false,
  });

  // Sales Performance Analysis
  const { data: salesPerformance, isLoading: salesLoading, refetch: refetchSales } = useQuery({
    queryKey: ['sales-performance', selectedCompanyId],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/api/analyze-sales-performance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company_id: selectedCompanyId }),
      });
      const data = await response.json();
      return data.data || { rankings: [], top_performer: null, team_avg_win_rate: 0 };
    },
    enabled: false,
  });

  // Meeting Summary
  const [selectedDealId, setSelectedDealId] = useState<string>('');
  const { data: meetingSummary, isLoading: meetingLoading, refetch: refetchMeeting } = useQuery({
    queryKey: ['meeting-summary', selectedDealId],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/api/summarize-meetings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ deal_id: selectedDealId }),
      });
      const data = await response.json();
      return data.data;
    },
    enabled: false,
  });

  // 高リスク商談フィルタリング（risk_score >= 70）
  const highRiskDeals = deals?.filter(deal => {
    // engagement_score を逆算してリスクスコアを推定
    const engagementScore = deal.engagement_score ?? 0; // null の場合は 0 とみなす
    const estimatedRisk = 100 - engagementScore;
    return estimatedRisk >= 70;
  }) || [];

  if (companiesLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-lg text-zinc-600 dark:text-zinc-400">読み込み中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-black">
      {/* Header */}
      <header className="bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">
              Revenue Intelligence Dashboard
            </h1>

            {/* 会社選択ドロップダウン */}
            <div className="flex items-center gap-3">
              <label htmlFor="company-select" className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                会社:
              </label>
              <select
                id="company-select"
                value={selectedCompanyId}
                onChange={(e) => setSelectedCompanyId(e.target.value)}
                className="px-4 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {companies?.map((company: Company) => (
                  <option key={company.id} value={company.id}>
                    {company.name} ({company.industry})
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Revenue Forecasting */}
          <Card title="売上予測（6ヶ月）" className="lg:col-span-2">
            {!revenueForecast ? (
              <div className="h-64 flex items-center justify-center">
                <button
                  onClick={() => refetchForecast()}
                  disabled={forecastLoading}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-400 text-white rounded-lg transition-colors"
                >
                  {forecastLoading ? '実行中...' : '実行'}
                </button>
              </div>
            ) : (
              <>
                {Array.isArray(revenueForecast.forecasts) ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={revenueForecast.forecasts}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
                      <XAxis dataKey="month" stroke="#71717a" />
                      <YAxis stroke="#71717a" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#27272a',
                          border: '1px solid #3f3f46',
                          borderRadius: '8px',
                        }}
                        labelStyle={{ color: '#fafafa' }}
                      />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="predicted_revenue"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        name="予測売上"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-64 flex items-center justify-center text-zinc-600 dark:text-zinc-400">
                    データがありません
                  </div>
                )}

                <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="text-zinc-600 dark:text-zinc-400">総予測売上</div>
                    <div className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
                      ¥{(revenueForecast.total_predicted_revenue || 0).toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <div className="text-zinc-600 dark:text-zinc-400">平均信頼度</div>
                    <div className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
                      {((revenueForecast.average_confidence || 0) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-zinc-600 dark:text-zinc-400">成長率</div>
                    <div className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
                      +{(revenueForecast.growth_rate || 0).toFixed(1)}%
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => refetchForecast()}
                  className="w-full mt-4 px-4 py-2 text-sm bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-900 dark:text-zinc-50 rounded-lg transition-colors"
                >
                  再実行
                </button>
              </>
            )}
          </Card>

          {/* High Risk Deals */}
          <Card title="高リスク商談" className="lg:col-span-1">
            {!deals ? (
              <div className="h-64 flex items-center justify-center">
                <button
                  onClick={() => refetchDeals()}
                  disabled={dealsLoading}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-400 text-white rounded-lg transition-colors"
                >
                  {dealsLoading ? '実行中...' : '実行'}
                </button>
              </div>
            ) : (
              <>
                {highRiskDeals.length > 0 ? (
                  <div className="space-y-3 max-h-80 overflow-y-auto">
                    {highRiskDeals.slice(0, 5).map((deal) => {
                      const engagementScore = deal.engagement_score ?? 0;
                      const estimatedRisk = 100 - engagementScore;

                      // リスク要因の生成（ステージとエンゲージメントスコアに基づく）
                      const riskFactors: string[] = [];
                      const stage = deal.stage?.toLowerCase() || '';

                      // ステージ別のリスク要因
                      if (stage === 'prospect') {
                        riskFactors.push('初期段階で進捗不明');
                        riskFactors.push('顧客エンゲージメント低い');
                      } else if (stage === 'meeting') {
                        riskFactors.push('ヒアリング不十分の可能性');
                        riskFactors.push('予算確認が必要');
                      } else if (stage === 'proposal') {
                        riskFactors.push('提案書送付後のフォロー不足');
                        riskFactors.push('競合状況が不明確');
                      } else if (stage === 'negotiation') {
                        riskFactors.push('価格交渉が難航している可能性');
                        riskFactors.push('契約条件の調整が必要');
                      }

                      // エンゲージメントスコア別のリスク要因
                      if (engagementScore < 30) {
                        riskFactors.push('長期間接触なし');
                      } else if (engagementScore < 50) {
                        riskFactors.push('エンゲージメント低下傾向');
                      }

                      return (
                        <div
                          key={deal.id}
                          className="p-3 rounded-lg border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950"
                        >
                          <div className="flex items-start justify-between mb-1">
                            <h4 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50 cursor-pointer hover:underline"
                                onClick={() => router.push(`/deals/${deal.id}`)}>
                              {deal.deal_name || '商談名未設定'}
                            </h4>
                            <span className="text-xs font-medium text-red-600 dark:text-red-400">
                              リスク: {estimatedRisk}
                            </span>
                          </div>
                          <div className="text-xs text-zinc-600 dark:text-zinc-400">
                            ステージ: {deal.stage} | 金額: ¥{(deal.amount || 0).toLocaleString()}
                          </div>
                          <div className="text-xs text-zinc-600 dark:text-zinc-400 mt-1">
                            担当: {deal.owner_name}
                          </div>

                          {/* リスク要因の表示 */}
                          {riskFactors.length > 0 && (
                            <div className="mt-2 pt-2 border-t border-red-200 dark:border-red-800">
                              <h5 className="text-xs font-semibold text-zinc-900 dark:text-zinc-50 mb-1">
                                リスク要因:
                              </h5>
                              <ul className="text-xs text-zinc-600 dark:text-zinc-400 space-y-0.5">
                                {riskFactors.map((factor, idx) => (
                                  <li key={idx}>• {factor}</li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {/* アクションボタン */}
                          <button
                            onClick={() => router.push(`/deals/${deal.id}`)}
                            className="w-full mt-3 px-3 py-1.5 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
                          >
                            詳細を見る
                          </button>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="h-64 flex items-center justify-center text-zinc-600 dark:text-zinc-400">
                    高リスク商談はありません
                  </div>
                )}
              </>
            )}
          </Card>

          {/* Win Rate Analysis */}
          <Card title="成約率分析（ステージ別）" className="lg:col-span-3">
            {!winRateAnalysis ? (
              <div className="h-64 flex items-center justify-center">
                <button
                  onClick={() => refetchWinRate()}
                  disabled={winRateLoading}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-400 text-white rounded-lg transition-colors"
                >
                  {winRateLoading ? '実行中...' : '実行'}
                </button>
              </div>
            ) : (
              <>
                {Array.isArray(winRateAnalysis.by_stage) ? (
                  <>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={winRateAnalysis.by_stage}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
                        <XAxis dataKey="stage" stroke="#71717a" />
                        <YAxis stroke="#71717a" />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#27272a',
                            border: '1px solid #3f3f46',
                            borderRadius: '8px',
                          }}
                          labelStyle={{ color: '#fafafa' }}
                        />
                        <Legend />
                        <Bar dataKey="win_rate" fill="#10b981" name="成約率 (%)" />
                        <Bar dataKey="count" fill="#6366f1" name="商談数" />
                      </BarChart>
                    </ResponsiveContainer>

                    <div className="mt-4 grid grid-cols-4 gap-4 text-sm">
                      <div>
                        <div className="text-zinc-600 dark:text-zinc-400">全体成約率</div>
                        <div className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
                          {(winRateAnalysis.overall_win_rate || 0).toFixed(1)}%
                        </div>
                      </div>
                      <div>
                        <div className="text-zinc-600 dark:text-zinc-400">総商談数</div>
                        <div className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
                          {winRateAnalysis.total_deals || 0}
                        </div>
                      </div>
                      <div>
                        <div className="text-zinc-600 dark:text-zinc-400">成約数</div>
                        <div className="text-lg font-semibold text-green-600 dark:text-green-400">
                          {winRateAnalysis.won_deals || 0}
                        </div>
                      </div>
                      <div>
                        <div className="text-zinc-600 dark:text-zinc-400">失注数</div>
                        <div className="text-lg font-semibold text-red-600 dark:text-red-400">
                          {winRateAnalysis.lost_deals || 0}
                        </div>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="h-64 flex items-center justify-center text-zinc-600 dark:text-zinc-400">
                    データがありません
                  </div>
                )}
                <button
                  onClick={() => refetchWinRate()}
                  className="w-full mt-4 px-4 py-2 text-sm bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-900 dark:text-zinc-50 rounded-lg transition-colors"
                >
                  再実行
                </button>
              </>
            )}
          </Card>

          {/* Churn Risk Prediction */}
          <Card title="チャーンリスク予測" className="lg:col-span-1">
            {!churnRisk ? (
              <div className="h-64 flex items-center justify-center">
                <button
                  onClick={() => refetchChurn()}
                  disabled={churnLoading}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-400 text-white rounded-lg transition-colors"
                >
                  {churnLoading ? '実行中...' : '実行'}
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-zinc-600 dark:text-zinc-400">リスクスコア</div>
                  <div className={`text-2xl font-bold ${
                    churnRisk.risk_score >= 70 ? 'text-red-600 dark:text-red-400' :
                    churnRisk.risk_score >= 40 ? 'text-yellow-600 dark:text-yellow-400' :
                    'text-green-600 dark:text-green-400'
                  }`}>
                    {churnRisk.risk_score}
                  </div>
                </div>
                <div className="text-sm">
                  <div className="text-zinc-600 dark:text-zinc-400 mb-2">リスクレベル</div>
                  <div className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${
                    churnRisk.risk_level === 'high' ? 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300' :
                    churnRisk.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-950 dark:text-yellow-300' :
                    'bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300'
                  }`}>
                    {churnRisk.risk_level}
                  </div>
                </div>
                {churnRisk.risk_factors && churnRisk.risk_factors.length > 0 && (
                  <div className="text-sm">
                    <div className="text-zinc-600 dark:text-zinc-400 mb-2">リスク要因</div>
                    <ul className="space-y-1">
                      {churnRisk.risk_factors.map((factor: string, idx: number) => (
                        <li key={idx} className="text-zinc-700 dark:text-zinc-300 text-xs">
                          • {factor}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {churnRisk.recommendations && churnRisk.recommendations.length > 0 && (
                  <div className="text-sm">
                    <div className="text-zinc-600 dark:text-zinc-400 mb-2">推奨アクション</div>
                    <ul className="space-y-1">
                      {churnRisk.recommendations.slice(0, 2).map((rec: string, idx: number) => (
                        <li key={idx} className="text-blue-600 dark:text-blue-400 text-xs">
                          → {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                <button
                  onClick={() => refetchChurn()}
                  className="w-full mt-2 px-4 py-2 text-sm bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-900 dark:text-zinc-50 rounded-lg transition-colors"
                >
                  再実行
                </button>
              </div>
            )}
          </Card>

          {/* Upsell Opportunities */}
          <Card title="アップセル機会検知" className="lg:col-span-2">
            {!upsellOpps ? (
              <div className="h-64 flex items-center justify-center">
                <button
                  onClick={() => refetchUpsell()}
                  disabled={upsellLoading}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-400 text-white rounded-lg transition-colors"
                >
                  {upsellLoading ? '実行中...' : '実行'}
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {upsellOpps.opportunities && upsellOpps.opportunities.length > 0 ? (
                  <>
                    <div className="space-y-3">
                      {upsellOpps.opportunities.map((opp: any, idx: number) => (
                        <div key={idx} className="p-4 rounded-lg border border-green-200 dark:border-green-900 bg-green-50 dark:bg-green-950">
                          <div className="flex items-start justify-between mb-2">
                            <h4 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
                              {opp.product}
                            </h4>
                            <span className="text-xs font-medium text-green-600 dark:text-green-400">
                              スコア: {opp.score}
                            </span>
                          </div>
                          <div className="text-xs text-zinc-600 dark:text-zinc-400 mb-1">
                            タイミング: {opp.timing}
                          </div>
                          <div className="text-xs text-zinc-600 dark:text-zinc-400 mb-2">
                            期待収益: ¥{(opp.expected_revenue || 0).toLocaleString()}
                          </div>
                          <div className="text-xs text-zinc-700 dark:text-zinc-300">
                            {opp.reason}
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="pt-3 border-t border-zinc-200 dark:border-zinc-800">
                      <div className="text-sm text-zinc-600 dark:text-zinc-400">合計潜在収益</div>
                      <div className="text-xl font-bold text-green-600 dark:text-green-400">
                        ¥{(upsellOpps.total_potential_revenue || 0).toLocaleString()}
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="h-48 flex items-center justify-center text-zinc-600 dark:text-zinc-400">
                    現時点でアップセル機会はありません
                  </div>
                )}
                <button
                  onClick={() => refetchUpsell()}
                  className="w-full mt-2 px-4 py-2 text-sm bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-900 dark:text-zinc-50 rounded-lg transition-colors"
                >
                  再実行
                </button>
              </div>
            )}
          </Card>

          {/* Competitor Analysis */}
          <Card title="競合分析" className="lg:col-span-3">
            {!competitorAnalysis ? (
              <div className="h-64 flex items-center justify-center">
                <button
                  onClick={() => refetchCompetitor()}
                  disabled={competitorLoading}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-400 text-white rounded-lg transition-colors"
                >
                  {competitorLoading ? '実行中...' : '実行'}
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {competitorAnalysis.competitors && competitorAnalysis.competitors.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {competitorAnalysis.competitors.map((comp: any, idx: number) => (
                      <div key={idx} className="p-4 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
                        <h4 className="text-base font-semibold text-zinc-900 dark:text-zinc-50 mb-3">
                          {comp.name}
                        </h4>
                        <div className="grid grid-cols-3 gap-3 mb-3 text-sm">
                          <div>
                            <div className="text-zinc-600 dark:text-zinc-400 text-xs">遭遇回数</div>
                            <div className="font-semibold text-zinc-900 dark:text-zinc-50">{comp.encounter_count}</div>
                          </div>
                          <div>
                            <div className="text-zinc-600 dark:text-zinc-400 text-xs">勝率</div>
                            <div className="font-semibold text-green-600 dark:text-green-400">{Math.round(comp.win_rate * 100)}%</div>
                          </div>
                          <div>
                            <div className="text-zinc-600 dark:text-zinc-400 text-xs">シェア</div>
                            <div className="font-semibold text-zinc-900 dark:text-zinc-50">{Math.round(comp.market_share * 100)}%</div>
                          </div>
                        </div>
                        <div className="space-y-2 text-xs">
                          <div>
                            <div className="text-zinc-600 dark:text-zinc-400 mb-1">強み</div>
                            <ul className="space-y-0.5">
                              {comp.strengths?.slice(0, 2).map((str: string, i: number) => (
                                <li key={i} className="text-zinc-700 dark:text-zinc-300">• {str}</li>
                              ))}
                            </ul>
                          </div>
                          <div>
                            <div className="text-zinc-600 dark:text-zinc-400 mb-1">弱み</div>
                            <ul className="space-y-0.5">
                              {comp.weaknesses?.slice(0, 2).map((weak: string, i: number) => (
                                <li key={i} className="text-zinc-700 dark:text-zinc-300">• {weak}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="h-48 flex items-center justify-center text-zinc-600 dark:text-zinc-400">
                    競合データがありません
                  </div>
                )}
                <button
                  onClick={() => refetchCompetitor()}
                  className="w-full mt-2 px-4 py-2 text-sm bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-900 dark:text-zinc-50 rounded-lg transition-colors"
                >
                  再実行
                </button>
              </div>
            )}
          </Card>

          {/* Sales Performance Analysis */}
          <Card title="営業パフォーマンス分析" className="lg:col-span-3">
            {!salesPerformance ? (
              <div className="h-64 flex items-center justify-center">
                <button
                  onClick={() => refetchSales()}
                  disabled={salesLoading}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-400 text-white rounded-lg transition-colors"
                >
                  {salesLoading ? '実行中...' : '実行'}
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {salesPerformance.rankings && salesPerformance.rankings.length > 0 ? (
                  <>
                    <ResponsiveContainer width="100%" height={250}>
                      <BarChart data={salesPerformance.rankings}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
                        <XAxis dataKey="name" stroke="#71717a" />
                        <YAxis stroke="#71717a" />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#27272a',
                            border: '1px solid #3f3f46',
                            borderRadius: '8px',
                          }}
                          labelStyle={{ color: '#fafafa' }}
                        />
                        <Legend />
                        <Bar dataKey="win_rate" fill="#10b981" name="成約率" />
                        <Bar dataKey="won_deals" fill="#3b82f6" name="成約数" />
                      </BarChart>
                    </ResponsiveContainer>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <div className="text-zinc-600 dark:text-zinc-400">トップパフォーマー</div>
                        <div className="font-semibold text-zinc-900 dark:text-zinc-50">
                          {salesPerformance.top_performer?.name || 'N/A'}
                        </div>
                      </div>
                      <div>
                        <div className="text-zinc-600 dark:text-zinc-400">平均成約率</div>
                        <div className="font-semibold text-green-600 dark:text-green-400">
                          {((salesPerformance.team_avg_win_rate || 0) * 100).toFixed(1)}%
                        </div>
                      </div>
                      <div>
                        <div className="text-zinc-600 dark:text-zinc-400">営業人数</div>
                        <div className="font-semibold text-zinc-900 dark:text-zinc-50">
                          {(salesPerformance.rankings || []).length}人
                        </div>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="h-48 flex items-center justify-center text-zinc-600 dark:text-zinc-400">
                    営業パフォーマンスデータがありません
                  </div>
                )}
                <button
                  onClick={() => refetchSales()}
                  className="w-full mt-2 px-4 py-2 text-sm bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-900 dark:text-zinc-50 rounded-lg transition-colors"
                >
                  再実行
                </button>
              </div>
            )}
          </Card>

          {/* Meeting Summary */}
          <Card title="ミーティング要約" className="lg:col-span-2">
            {!meetingSummary ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                    商談を選択
                  </label>
                  <select
                    value={selectedDealId}
                    onChange={(e) => setSelectedDealId(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">選択してください</option>
                    {deals?.map((deal) => (
                      <option key={deal.id} value={deal.id}>
                        {deal.customer_name} - {deal.stage}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="h-40 flex items-center justify-center">
                  <button
                    onClick={() => selectedDealId && refetchMeeting()}
                    disabled={!selectedDealId || meetingLoading}
                    className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-400 text-white rounded-lg transition-colors"
                  >
                    {meetingLoading ? '実行中...' : '実行'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {meetingSummary.meetings && meetingSummary.meetings.length > 0 ? (
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {meetingSummary.meetings.map((meeting: any, idx: number) => (
                      <div key={idx} className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900">
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
                            {meeting.title || `ミーティング ${idx + 1}`}
                          </h4>
                          <span className={`text-xs px-2 py-1 rounded ${
                            meeting.sentiment === 'positive' ? 'bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300' :
                            meeting.sentiment === 'negative' ? 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300' :
                            'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300'
                          }`}>
                            {meeting.sentiment}
                          </span>
                        </div>
                        <p className="text-xs text-zinc-700 dark:text-zinc-300 mb-2">
                          {meeting.summary}
                        </p>
                        {meeting.key_points && meeting.key_points.length > 0 && (
                          <div className="text-xs">
                            <div className="text-zinc-600 dark:text-zinc-400 mb-1">重要ポイント</div>
                            <ul className="space-y-0.5">
                              {meeting.key_points.slice(0, 2).map((point: string, i: number) => (
                                <li key={i} className="text-zinc-700 dark:text-zinc-300">• {point}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="h-48 flex items-center justify-center text-zinc-600 dark:text-zinc-400">
                    ミーティングデータがありません
                  </div>
                )}
                <button
                  onClick={() => refetchMeeting()}
                  className="w-full mt-2 px-4 py-2 text-sm bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-900 dark:text-zinc-50 rounded-lg transition-colors"
                >
                  再実行
                </button>
              </div>
            )}
          </Card>

          {/* Deal Progress Tracking - Note: Already integrated in deal detail page */}
          <Card title="商談進捗トラッキング" className="lg:col-span-1">
            <div className="h-64 flex flex-col items-center justify-center space-y-3">
              <p className="text-sm text-zinc-600 dark:text-zinc-400 text-center">
                この機能は商談詳細ページに統合されています
              </p>
              <Link
                href="/deals"
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
              >
                商談一覧へ
              </Link>
            </div>
          </Card>

          {/* Next Actions Suggestion - Note: Already integrated in deal detail page */}
          <Card title="次のアクション提案" className="lg:col-span-3">
            <div className="h-64 flex flex-col items-center justify-center space-y-3">
              <p className="text-sm text-zinc-600 dark:text-zinc-400 text-center">
                この機能は商談詳細ページに統合されています（各商談の「AI分析」タブ）
              </p>
              <Link
                href="/deals"
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
              >
                商談一覧へ
              </Link>
            </div>
          </Card>
        </div>

        {/* Quick Links */}
        <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Link
            href="/deals"
            className={`flex items-center justify-center gap-2 px-6 py-4 rounded-lg border transition-colors ${
              pathname === '/deals'
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-950'
                : 'border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 hover:bg-zinc-50 dark:hover:bg-zinc-800'
            }`}
          >
            <span className={`text-base font-medium ${
              pathname === '/deals'
                ? 'text-blue-600 dark:text-blue-400'
                : 'text-zinc-900 dark:text-zinc-50'
            }`}>商談一覧</span>
          </Link>
          <Link
            href="/agents"
            className={`flex items-center justify-center gap-2 px-6 py-4 rounded-lg border transition-colors ${
              pathname === '/agents'
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-950'
                : 'border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 hover:bg-zinc-50 dark:hover:bg-zinc-800'
            }`}
          >
            <span className={`text-base font-medium ${
              pathname === '/agents'
                ? 'text-blue-600 dark:text-blue-400'
                : 'text-zinc-900 dark:text-zinc-50'
            }`}>AI Agents</span>
          </Link>
          {/* レポートボタン削除: 実装計画（Day 1-4スケジュール）に含まれていないため */}
        </div>
      </main>
    </div>
  );
}
