/**
 * ActionCard - アクションカードコンポーネント
 *
 * Next Best Actions を表示するカード
 * 優先度別にスタイルが変わる（urgent/high/medium/low）
 */

import type { NextAction } from '@/lib/types';

interface ActionCardProps {
  action: NextAction;
}

export function ActionCard({ action }: ActionCardProps) {
  // 優先度別のスタイル
  const priorityStyles = {
    urgent: 'border-red-500 bg-red-50 dark:bg-red-950',
    high: 'border-orange-500 bg-orange-50 dark:bg-orange-950',
    medium: 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950',
    low: 'border-blue-500 bg-blue-50 dark:bg-blue-950',
  };

  const priorityBadgeStyles = {
    urgent: 'bg-red-600 text-white',
    high: 'bg-orange-600 text-white',
    medium: 'bg-yellow-600 text-white',
    low: 'bg-blue-600 text-white',
  };

  const priorityLabels = {
    urgent: '緊急',
    high: '高',
    medium: '中',
    low: '低',
  };

  return (
    <div
      className={`border-l-4 rounded-lg p-4 ${priorityStyles[action.priority]}`}
    >
      <div className="flex items-start justify-between mb-2">
        <h4 className="text-base font-semibold text-zinc-900 dark:text-zinc-50">
          {action.action}
        </h4>
        <span
          className={`px-2 py-1 rounded-md text-xs font-medium ${priorityBadgeStyles[action.priority]}`}
        >
          {priorityLabels[action.priority]}
        </span>
      </div>

      <p className="text-sm text-zinc-700 dark:text-zinc-300 mb-3">
        {action.rationale}
      </p>

      {action.estimated_impact && (
        <div className="text-xs text-zinc-600 dark:text-zinc-400">
          <span className="font-medium">期待効果:</span> {action.estimated_impact}
        </div>
      )}

      {action.deadline && (
        <div className="text-xs text-zinc-600 dark:text-zinc-400 mt-1">
          <span className="font-medium">期限:</span>{' '}
          {new Date(action.deadline).toLocaleDateString('ja-JP')}
        </div>
      )}
    </div>
  );
}
