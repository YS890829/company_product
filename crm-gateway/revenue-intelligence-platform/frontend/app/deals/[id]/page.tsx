/**
 * Deal Detail Page - 商談詳細画面
 *
 * 商談の詳細情報と AI による Next Best Actions を表示
 */

'use client';

import { use } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/Card';
import { ActionCard } from '@/components/ui/ActionCard';
import { apiClient } from '@/lib/api-client';
import Link from 'next/link';

interface DealDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function DealDetailPage({ params }: DealDetailPageProps) {
  const { id: dealId } = use(params);

  // 商談データ取得
  const { data: deal, isLoading: dealLoading } = useQuery({
    queryKey: ['deal', dealId],
    queryFn: async () => {
      const deals = await apiClient.getDeals();
      return deals.find(d => d.id === dealId);
    },
  });

  // Next Best Actions 取得
  const { data: nextActions, isLoading: actionsLoading } = useQuery({
    queryKey: ['next-actions', dealId],
    queryFn: () => apiClient.generateNextActions(dealId),
    enabled: !!deal,
  });

  // ミーティング履歴取得
  const { data: meetings, isLoading: meetingsLoading } = useQuery({
    queryKey: ['meetings', dealId],
    queryFn: () => apiClient.getMeetings(dealId),
  });

  // メール履歴取得
  const { data: emails, isLoading: emailsLoading } = useQuery({
    queryKey: ['emails', dealId],
    queryFn: () => apiClient.getEmails(dealId),
  });

  // 商談進捗取得
  const { data: dealProgress } = useQuery({
    queryKey: ['deal-progress', dealId],
    queryFn: () => apiClient.trackDealProgress(dealId),
  });

  if (dealLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-lg text-zinc-600 dark:text-zinc-400">読み込み中...</div>
      </div>
    );
  }

  if (!deal) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-lg text-zinc-600 dark:text-zinc-400">商談が見つかりません</div>
      </div>
    );
  }

  // リスクスコア推定（engagement_scoreがnullの場合は0と仮定）
  const engagementScore = deal.engagement_score ?? 0;
  const estimatedRisk = 100 - engagementScore;
  const riskLevel = estimatedRisk >= 70 ? 'critical' : estimatedRisk >= 50 ? 'high' : estimatedRisk >= 30 ? 'medium' : 'low';

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-black">
      {/* Header */}
      <header className="bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">
                  {deal.customer_name}
                </h1>
                {deal.customer_industry && (
                  <span className="text-sm text-zinc-600 dark:text-zinc-400 px-3 py-1 rounded-md bg-zinc-100 dark:bg-zinc-800">
                    {deal.customer_industry}
                  </span>
                )}
              </div>
              <div className="text-base text-zinc-600 dark:text-zinc-400 mb-3">
                {deal.deal_name}
              </div>
              <div className="flex items-center gap-4 text-sm">
                <span className="px-3 py-1 rounded-md bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 font-medium">
                  {deal.stage}
                </span>
                <span className={`px-3 py-1 rounded-md font-medium ${
                  riskLevel === 'critical' ? 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200' :
                  riskLevel === 'high' ? 'bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200' :
                  riskLevel === 'medium' ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200' :
                  'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                }`}>
                  リスク: {estimatedRisk} ({riskLevel})
                </span>
              </div>
            </div>
            <Link
              href="/deals"
              className="px-4 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 hover:bg-zinc-50 dark:hover:bg-zinc-800 text-sm font-medium text-zinc-900 dark:text-zinc-50 transition-colors"
            >
              ← 商談一覧
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 商談基本情報 */}
          <Card title="商談情報" className="lg:col-span-1">
            <div className="space-y-4 text-sm">
              <div>
                <div className="text-zinc-600 dark:text-zinc-400 mb-1">金額</div>
                <div className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
                  ¥{deal.amount.toLocaleString()}
                </div>
              </div>

              <div>
                <div className="text-zinc-600 dark:text-zinc-400 mb-1">担当者</div>
                <div className="text-base text-zinc-900 dark:text-zinc-50">
                  {deal.owner_name}
                </div>
              </div>

              <div>
                <div className="text-zinc-600 dark:text-zinc-400 mb-1">商談実施日</div>
                <div className="text-base text-zinc-900 dark:text-zinc-50">
                  {new Date(deal.created_at).toLocaleDateString('ja-JP')}
                </div>
              </div>

              {deal.probability !== null && deal.probability !== undefined && (
                <div>
                  <div className="text-zinc-600 dark:text-zinc-400 mb-1">成約確率</div>
                  <div className="text-base text-zinc-900 dark:text-zinc-50">
                    {(deal.probability * 100).toFixed(0)}%
                  </div>
                </div>
              )}

              {deal.next_action && (
                <div>
                  <div className="text-zinc-600 dark:text-zinc-400 mb-1">次のアクション</div>
                  <div className="text-base text-zinc-900 dark:text-zinc-50">
                    {deal.next_action}
                  </div>
                </div>
              )}

              {deal.next_action_date && (
                <div>
                  <div className="text-zinc-600 dark:text-zinc-400 mb-1">次回予定日</div>
                  <div className="text-base text-zinc-900 dark:text-zinc-50">
                    {new Date(deal.next_action_date).toLocaleDateString('ja-JP')}
                  </div>
                </div>
              )}

              {deal.expected_close_date && (
                <div>
                  <div className="text-zinc-600 dark:text-zinc-400 mb-1">クローズ予定日</div>
                  <div className="text-base text-zinc-900 dark:text-zinc-50">
                    {new Date(deal.expected_close_date).toLocaleDateString('ja-JP')}
                  </div>
                </div>
              )}

              {deal.customer_size && (
                <div>
                  <div className="text-zinc-600 dark:text-zinc-400 mb-1">顧客規模</div>
                  <div className="text-base text-zinc-900 dark:text-zinc-50">
                    {deal.customer_size}名
                  </div>
                </div>
              )}

              <div className="pt-4 border-t border-zinc-200 dark:border-zinc-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-zinc-600 dark:text-zinc-400">予算確定</span>
                  <span className={deal.budget_confirmed ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
                    {deal.budget_confirmed ? '✓ 確定' : '✗ 未確定'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-zinc-600 dark:text-zinc-400">決裁者特定</span>
                  <span className={deal.decision_maker_identified ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
                    {deal.decision_maker_identified ? '✓ 特定済' : '✗ 未特定'}
                  </span>
                </div>
              </div>
            </div>
          </Card>

          {/* Risk Analysis Section */}
          <Card title="リスク分析" className="lg:col-span-2">
            <div className="space-y-6">
              {/* Risk Factors */}
              {deal.risk_factors && deal.risk_factors.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50 mb-3">
                    リスク要因:
                  </h3>
                  <ul className="list-disc list-inside space-y-2">
                    {deal.risk_factors.map((factor, i) => (
                      <li key={i} className="text-sm text-zinc-600 dark:text-zinc-400 pl-2">
                        {factor}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Strengths */}
              {deal.strengths && deal.strengths.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50 mb-3">
                    強み:
                  </h3>
                  <ul className="list-disc list-inside space-y-2">
                    {deal.strengths.map((strength, i) => (
                      <li key={i} className="text-sm text-zinc-600 dark:text-zinc-400 pl-2">
                        {strength}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Empty State */}
              {(!deal.risk_factors || deal.risk_factors.length === 0) &&
               (!deal.strengths || deal.strengths.length === 0) && (
                <div className="text-center py-8 text-zinc-600 dark:text-zinc-400">
                  リスク分析データがありません
                </div>
              )}
            </div>
          </Card>

          {/* Next Best Actions */}
          <Card title="推奨アクション" className="lg:col-span-2">
            {actionsLoading ? (
              <div className="h-64 flex items-center justify-center text-zinc-600 dark:text-zinc-400">
                読み込み中...
              </div>
            ) : nextActions && nextActions.length > 0 ? (
              <div className="space-y-4">
                {nextActions.map((action, index) => (
                  <ActionCard key={index} action={action} />
                ))}
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-zinc-600 dark:text-zinc-400">
                推奨アクションがありません
              </div>
            )}
          </Card>

          {/* 商談進捗 */}
          {dealProgress && (
            <Card title="商談進捗" className="lg:col-span-3">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-zinc-600 dark:text-zinc-400">進捗率</span>
                  <span className="text-base font-semibold text-zinc-900 dark:text-zinc-50">
                    {dealProgress.progress_rate}%
                  </span>
                </div>

                <div className="w-full bg-zinc-200 dark:bg-zinc-800 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{ width: `${dealProgress.progress_rate}%` }}
                  />
                </div>

                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="text-zinc-600 dark:text-zinc-400 mb-1">現在のステージ</div>
                    <div className="text-base text-zinc-900 dark:text-zinc-50">
                      {dealProgress.current_stage}
                    </div>
                  </div>
                  <div>
                    <div className="text-zinc-600 dark:text-zinc-400 mb-1">次のマイルストーン</div>
                    <div className="text-base text-zinc-900 dark:text-zinc-50">
                      {dealProgress.next_milestone}
                    </div>
                  </div>
                  <div>
                    <div className="text-zinc-600 dark:text-zinc-400 mb-1">健全性ステータス</div>
                    <div className={`text-base font-semibold ${
                      dealProgress.health_status === 'high' ? 'text-green-600 dark:text-green-400' :
                      dealProgress.health_status === 'medium' ? 'text-yellow-600 dark:text-yellow-400' :
                      'text-red-600 dark:text-red-400'
                    }`}>
                      {dealProgress.health_status === 'high' ? '良好' :
                       dealProgress.health_status === 'medium' ? '注意' : '要対応'}
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* ミーティング履歴 */}
          <Card title="ミーティング履歴" className="lg:col-span-3">
            {meetingsLoading ? (
              <div className="h-64 flex items-center justify-center text-zinc-600 dark:text-zinc-400">
                読み込み中...
              </div>
            ) : meetings && meetings.length > 0 ? (
              <div className="space-y-4">
                {meetings.slice(0, 5).map((meeting) => (
                  <div
                    key={meeting.id}
                    className="p-4 rounded-lg border border-zinc-200 dark:border-zinc-800"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="text-base font-semibold text-zinc-900 dark:text-zinc-50">
                        {new Date(meeting.date).toLocaleDateString('ja-JP', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })}
                      </h4>
                      {meeting.sentiment_analysis && (
                        <span className={`text-xs px-2 py-1 rounded-md font-medium ${
                          meeting.sentiment_analysis.overall === 'positive' ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200' :
                          meeting.sentiment_analysis.overall === 'negative' ? 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200' :
                          'bg-zinc-100 dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200'
                        }`}>
                          {meeting.sentiment_analysis.overall === 'positive' ? '肯定的' :
                           meeting.sentiment_analysis.overall === 'negative' ? '否定的' : '中立'}
                        </span>
                      )}
                    </div>

                    {meeting.transcript && (
                      <p className="text-sm text-zinc-600 dark:text-zinc-400 line-clamp-3">
                        {meeting.transcript}
                      </p>
                    )}

                    {meeting.duration_minutes && (
                      <div className="text-xs text-zinc-500 dark:text-zinc-500 mt-2">
                        時間: {meeting.duration_minutes}分
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-zinc-600 dark:text-zinc-400">
                ミーティング履歴がありません
              </div>
            )}
          </Card>

          {/* メール履歴 */}
          <Card title="メール履歴" className="lg:col-span-3">
            {emailsLoading ? (
              <div className="h-64 flex items-center justify-center text-zinc-600 dark:text-zinc-400">
                読み込み中...
              </div>
            ) : emails && emails.length > 0 ? (
              <div className="space-y-4">
                {emails.slice(0, 10).map((email) => (
                  <div
                    key={email.id}
                    className="p-4 rounded-lg border border-zinc-200 dark:border-zinc-800"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h4 className="text-base font-semibold text-zinc-900 dark:text-zinc-50">
                          {email.subject}
                        </h4>
                        <div className="text-xs text-zinc-500 dark:text-zinc-500 mt-1">
                          {email.from_email} → {email.to_email}
                        </div>
                      </div>
                      <span className="text-xs text-zinc-500 dark:text-zinc-500">
                        {new Date(email.sent_at).toLocaleDateString('ja-JP', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                        })}
                      </span>
                    </div>

                    {email.body && (
                      <p className="text-sm text-zinc-600 dark:text-zinc-400 line-clamp-3 mt-2">
                        {email.body}
                      </p>
                    )}

                    {email.sentiment_analysis && (
                      <div className="mt-2 flex items-center gap-2">
                        <span className={`text-xs px-2 py-1 rounded-md font-medium ${
                          email.sentiment_analysis.overall === 'positive' ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200' :
                          email.sentiment_analysis.overall === 'negative' ? 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200' :
                          'bg-zinc-100 dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200'
                        }`}>
                          {email.sentiment_analysis.overall === 'positive' ? '肯定的' :
                           email.sentiment_analysis.overall === 'negative' ? '否定的' : '中立'}
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-zinc-600 dark:text-zinc-400">
                メール履歴がありません
              </div>
            )}
          </Card>
        </div>
      </main>
    </div>
  );
}
