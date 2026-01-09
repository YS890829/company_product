/**
 * Deals Page - 商談一覧画面
 *
 * 全商談をリスト表示し、詳細ページへのリンクを提供
 */

'use client';

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/Card';
import { apiClient } from '@/lib/api-client';
import Link from 'next/link';

export default function DealsPage() {
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>('all');
  const [selectedStage, setSelectedStage] = useState<string>('all');

  // 会社一覧取得
  const { data: companies } = useQuery({
    queryKey: ['companies'],
    queryFn: () => apiClient.getCompanies(),
  });

  // 商談一覧取得
  const { data: deals, isLoading } = useQuery({
    queryKey: ['all-deals'],
    queryFn: () => apiClient.getDeals(),
  });

  // フィルタリング
  const filteredDeals = useMemo(() => {
    if (!deals) return [];

    return deals.filter(deal => {
      const companyMatch = selectedCompanyId === 'all' || deal.company_id === selectedCompanyId;
      const stageMatch = selectedStage === 'all' || deal.stage === selectedStage;
      return companyMatch && stageMatch;
    });
  }, [deals, selectedCompanyId, selectedStage]);

  // ステージ一覧（ユニーク）
  const stages = useMemo(() => {
    if (!deals) return [];
    const uniqueStages = [...new Set(deals.map(d => d.stage))];
    return uniqueStages;
  }, [deals]);

  if (isLoading) {
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
              商談一覧
            </h1>
            <Link
              href="/dashboard"
              className="px-4 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 hover:bg-zinc-50 dark:hover:bg-zinc-800 text-sm font-medium text-zinc-900 dark:text-zinc-50 transition-colors"
            >
              ← ダッシュボード
            </Link>
          </div>

          {/* フィルター */}
          <div className="mt-6 flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <label htmlFor="company-filter" className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                会社:
              </label>
              <select
                id="company-filter"
                value={selectedCompanyId}
                onChange={(e) => setSelectedCompanyId(e.target.value)}
                className="px-3 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">全て</option>
                {companies?.map((company) => (
                  <option key={company.id} value={company.id}>
                    {company.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2">
              <label htmlFor="stage-filter" className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                ステージ:
              </label>
              <select
                id="stage-filter"
                value={selectedStage}
                onChange={(e) => setSelectedStage(e.target.value)}
                className="px-3 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">全て</option>
                {stages.map((stage) => (
                  <option key={stage} value={stage}>
                    {stage}
                  </option>
                ))}
              </select>
            </div>

            <div className="text-sm text-zinc-600 dark:text-zinc-400">
              {filteredDeals.length}件の商談
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card>
          <div className="space-y-3">
            {filteredDeals?.map((deal) => (
              <Link
                key={deal.id}
                href={`/deals/${deal.id}`}
                className="block p-4 rounded-lg border border-zinc-200 dark:border-zinc-800 hover:border-blue-500 dark:hover:border-blue-500 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
                      {deal.deal_name || '商談名未設定'}
                    </h3>
                  </div>
                  <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
                    {deal.stage}
                  </span>
                </div>
                <div className="text-sm text-zinc-600 dark:text-zinc-400">
                  金額: ¥{deal.amount.toLocaleString()} | 担当: {deal.owner_name}
                </div>
                <div className="text-sm text-zinc-600 dark:text-zinc-400 mt-1">
                  商談実施日: {new Date(deal.created_at).toLocaleDateString('ja-JP')}
                </div>
                <div className="text-sm text-zinc-600 dark:text-zinc-400 mt-1">
                  成約率: {deal.probability ? (deal.probability * 100).toFixed(0) : 0}% | 次回予定: {deal.next_action_date ? new Date(deal.next_action_date).toLocaleDateString('ja-JP') : 'なし'}
                </div>
              </Link>
            ))}
          </div>
        </Card>
      </main>
    </div>
  );
}
