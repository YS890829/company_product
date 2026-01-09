/**
 * Home Page - ランディングページ
 *
 * Revenue Intelligence Platform のランディングページ
 */

import Link from "next/link";

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex min-h-screen w-full max-w-4xl flex-col items-center justify-center py-32 px-8">
        <div className="flex flex-col items-center gap-8 text-center">
          {/* Title */}
          <h1 className="max-w-2xl text-5xl font-bold leading-tight tracking-tight text-zinc-900 dark:text-zinc-50">
            Revenue Intelligence Platform
          </h1>

          {/* Subtitle */}
          <p className="max-w-xl text-xl leading-8 text-zinc-600 dark:text-zinc-400">
            AI-powered Revenue Intelligence Platform with Gemini 2.0 Flash
          </p>

          {/* Description */}
          <div className="max-w-2xl text-base leading-7 text-zinc-600 dark:text-zinc-400 space-y-2">
            <p>
              このプラットフォームは、Gemini 2.0 Flash、CrewAI、LangGraph を活用した
              Revenue Intelligence システムのプロトタイプです。
            </p>
            <p>
              商談リスク分析、成約率予測、売上予測など、10種類の Revenue Intelligence 機能と、
              AI Agents による自動化ワークフローを提供します。
            </p>
          </div>

          {/* Features */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-8 w-full max-w-2xl">
            <div className="p-4 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
              <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50 mb-2">
                Revenue Intelligence
              </h3>
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                10機能の AI 分析
              </p>
            </div>
            <div className="p-4 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
              <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50 mb-2">
                CrewAI Agents
              </h3>
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                3つの Multi-Agent Workers
              </p>
            </div>
            <div className="p-4 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
              <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50 mb-2">
                LangGraph Workflow
              </h3>
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                State Orchestration
              </p>
            </div>
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 mt-8 text-base font-medium">
            <Link
              href="/dashboard"
              className="flex h-14 w-full items-center justify-center gap-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-8 text-zinc-900 dark:text-zinc-50 transition-colors hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-950 hover:text-blue-600 dark:hover:text-blue-400 sm:w-auto"
            >
              ダッシュボードへ
            </Link>
            <Link
              href="/agents"
              className="flex h-14 w-full items-center justify-center rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-8 text-zinc-900 dark:text-zinc-50 transition-colors hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-950 hover:text-blue-600 dark:hover:text-blue-400 sm:w-auto"
            >
              AI Agents
            </Link>
            <Link
              href="/deals"
              className="flex h-14 w-full items-center justify-center rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-8 text-zinc-900 dark:text-zinc-50 transition-colors hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-950 hover:text-blue-600 dark:hover:text-blue-400 sm:w-auto"
            >
              商談一覧
            </Link>
          </div>

          {/* Tech Stack */}
          <div className="mt-12 text-center">
            <p className="text-sm text-zinc-500 dark:text-zinc-500 mb-2">
              技術スタック
            </p>
            <p className="text-xs text-zinc-400 dark:text-zinc-600">
              Next.js 16 • React Query • Recharts • Gemini 2.0 Flash • CrewAI • LangGraph • FastAPI • Supabase
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
