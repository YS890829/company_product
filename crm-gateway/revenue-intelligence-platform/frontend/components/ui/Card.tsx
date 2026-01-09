/**
 * Card - 共通カードコンポーネント
 *
 * Tailwind CSS で統一されたスタイルのカードを提供
 */

import { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  title?: string;
}

export function Card({ children, className = '', title }: CardProps) {
  return (
    <div
      className={`bg-white dark:bg-zinc-900 rounded-lg border border-zinc-200 dark:border-zinc-800 shadow-sm p-6 ${className}`}
    >
      {title && (
        <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50 mb-4">
          {title}
        </h3>
      )}
      {children}
    </div>
  );
}
