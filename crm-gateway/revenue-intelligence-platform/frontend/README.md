# Frontend - Revenue Intelligence Platform

**技術スタック**: Next.js 14 (App Router) + TypeScript + Tailwind CSS
**最終更新**: 2025年11月4日

---

## 📖 概要

Revenue Intelligence Platformのフロントエンドは、Next.js 14のApp Routerを使用したモダンなSPAです。
5つの主要画面と10個のRevenue Intelligence機能を実装しています。

---

## 🚀 クイックスタート

### 前提条件
- Node.js 18.17+
- npm または yarn

### インストール

```bash
cd frontend
npm install
```

### 環境変数設定

```bash
cp .env.example .env.local
```

`.env.local`を編集:
```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here

# Backend API（本番環境のみ）
NEXT_PUBLIC_API_URL=https://your-railway-app.railway.app
```

### 開発サーバー起動

```bash
npm run dev
```

ブラウザで [http://localhost:3000](http://localhost:3000) を開く

---

## 📁 プロジェクト構成

```
frontend/
├── app/                          # Next.js App Router
│   ├── page.tsx                 # ランディングページ
│   ├── layout.tsx               # ルートレイアウト
│   ├── globals.css              # グローバルスタイル
│   │
│   ├── dashboard/               # Revenue Intelligence Dashboard
│   │   └── page.tsx            # ダッシュボード画面
│   │
│   ├── deals/                   # 商談管理
│   │   ├── page.tsx            # 商談一覧
│   │   └── [id]/               # 商談詳細
│   │       └── page.tsx
│   │
│   └── agents/                  # AI Agents
│       └── page.tsx            # CrewAI + LangGraph
│
├── components/                   # Reactコンポーネント
│   ├── ui/                      # UIコンポーネント（shadcn/ui）
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── badge.tsx
│   │   ├── tabs.tsx
│   │   └── ...
│   │
│   ├── Dashboard/               # ダッシュボードコンポーネント
│   │   ├── RevenueIntelligence.tsx
│   │   ├── DealVelocityChart.tsx
│   │   └── ...
│   │
│   └── Deals/                   # 商談コンポーネント
│       ├── DealCard.tsx
│       ├── DealDetails.tsx
│       └── ...
│
├── lib/                         # ユーティリティ
│   ├── supabase.ts             # Supabaseクライアント
│   └── utils.ts                # ヘルパー関数
│
├── public/                      # 静的アセット
│   └── ...
│
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.ts
└── .env.example
```

---

## 🎨 実装済み画面

### 1. ランディングページ (`/`)
- プロダクト概要
- 主要機能紹介
- CTAボタン

### 2. Revenue Intelligence Dashboard (`/dashboard`)
- **10個のRevenue Intelligence機能**:
  1. Deal Risk Analysis - 商談リスク分析
  2. Win Probability - 成約確率予測
  3. Deal Velocity Tracking - 商談速度追跡
  4. Competitor Mentions - 競合言及分析
  5. Stakeholder Mapping - ステークホルダーマッピング
  6. Objection Patterns - 反論パターン検出
  7. Champion Detection - チャンピオン検出
  8. Budget Signals - 予算シグナル検出
  9. Timeline Prediction - タイムライン予測
  10. Next Best Action - 次の最善アクション提案

- **チャートとグラフ**:
  - 売上予測（折れ線グラフ）
  - 成約率分析（棒グラフ）
  - チャーンリスク予測（進捗バー）

### 3. 商談一覧 (`/deals`)
- 商談カード表示（310商談）
- ステージ別フィルタリング
- 検索機能
- 成約確率表示

### 4. 商談詳細 (`/deals/[id]`)
- 商談基本情報
- ステークホルダー一覧
- ミーティング履歴
- メール履歴
- AI分析結果

### 5. AI Agents (`/agents`)
- CrewAI Multi-Agent（3 Workers）
- LangGraph Workflow
- タスク実行画面

---

## 🧩 主要コンポーネント

### UIコンポーネント（shadcn/ui）
- `Button` - アクションボタン
- `Card` - カードレイアウト
- `Badge` - ステータス表示
- `Tabs` - タブナビゲーション
- その他20+コンポーネント

### ビジネスコンポーネント
- `RevenueIntelligence.tsx` - RI機能統合コンポーネント
- `DealVelocityChart.tsx` - 商談速度チャート
- `DealCard.tsx` - 商談カード
- `DealDetails.tsx` - 商談詳細表示

---

## 🔌 API連携

### Supabase
```typescript
import { createClient } from '@/lib/supabase'

const supabase = createClient()

// 商談一覧取得
const { data: deals } = await supabase
  .from('deals')
  .select('*')
  .order('created_at', { ascending: false })
```

### Backend API（FastAPI）
```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Deal Risk Analysis
const response = await fetch(`${API_URL}/api/deals/${dealId}/risk-analysis`)
const riskAnalysis = await response.json()
```

---

## 🎨 スタイリング

### Tailwind CSS
```tsx
<div className="flex flex-col gap-4 p-6 bg-white rounded-lg shadow-md">
  <h2 className="text-2xl font-bold text-gray-900">Revenue Intelligence</h2>
  <p className="text-gray-600">AI駆動型営業分析プラットフォーム</p>
</div>
```

### カスタムスタイル
- `globals.css` - グローバルスタイル定義
- Tailwind Config - テーマカスタマイズ

---

## 📦 ビルド & デプロイ

### ローカルビルド
```bash
npm run build
npm start
```

### Vercelデプロイ
```bash
# Vercel CLIインストール
npm i -g vercel

# デプロイ
vercel --prod
```

### 環境変数（Vercel）
Vercelダッシュボードで以下を設定:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_API_URL`

---

## 🧪 開発ガイドライン

### TypeScript
- 全てのコンポーネントは型定義必須
- `any`型の使用を避ける
- インターフェースを明確に定義

### コンポーネント設計
- Single Responsibility Principle
- Propsインターフェースを定義
- ドキュメントコメント追加

### ファイル命名規則
- コンポーネント: `PascalCase.tsx`
- ユーティリティ: `camelCase.ts`
- ページ: `page.tsx`, `layout.tsx`

---

## 🔍 トラブルシューティング

### Turbopack UTF-8エラー
```bash
# 問題: 日本語ファイル名でUTF-8エラー
# 解決策: プロジェクトパスを英語のみに変更
```

### Supabase接続エラー
```bash
# 環境変数確認
echo $NEXT_PUBLIC_SUPABASE_URL
echo $NEXT_PUBLIC_SUPABASE_ANON_KEY

# .env.local再読み込み
npm run dev
```

### ビルドエラー
```bash
# キャッシュクリア
rm -rf .next
npm run dev
```

---

## 📚 参考資料

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [shadcn/ui](https://ui.shadcn.com)
- [Supabase JavaScript Client](https://supabase.com/docs/reference/javascript/introduction)
- [プロジェクトREADME](../README.md)

---

**作成日**: 2025年11月4日
**プロジェクト**: Revenue Intelligence Platform
**役割**: モダンなSPA実装（Next.js 14 + TypeScript）
