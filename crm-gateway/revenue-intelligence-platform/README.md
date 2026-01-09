# Revenue Intelligence Platform

**AI駆動型営業分析プラットフォーム** - Gemini API + CrewAI Multi-Agent + LangGraph Workflow

---

## 📖 プロジェクト概要

Revenue Intelligence Platformは、営業組織の商談データを分析し、実行可能なインサイトと提案を生成するAI駆動型SaaSプラットフォームです。

### 核心的価値提案
- **10個のRevenue Intelligence機能**: 商談リスク分析、成約予測、Deal Velocity追跡等
- **3個のSuggestion Engine機能**: Next Best Action、Email Template、Meeting Agenda生成
- **CrewAI Multi-Agent**: Email/Document/CRM Workerによる協調分析
- **LangGraph Workflow**: インテリジェントなタスク自動化

### 技術スタック
- **Frontend**: Next.js 14 (App Router) + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python 3.11
- **AI/ML**: Gemini API (gemini-1.5-flash) + CrewAI + LangGraph
- **Database**: Supabase (PostgreSQL)
- **Deployment**: Vercel (Frontend) + Railway (Backend) + Supabase (DB)

---

## 🚀 クイックスタート

### 前提条件
- Node.js 18.17+
- Python 3.11+
- Supabase プロジェクト
- Gemini API Key（Google AI Studio）

### 1. リポジトリクローン
```bash
git clone <repository-url>
cd revenue-intelligence-platform
```

### 2. データベースセットアップ
```bash
# Supabaseプロジェクト作成後
cd database
# スキーマ適用
psql -h <your-db-host> -U postgres -d postgres -f schema.sql
# シードデータ投入
psql -h <your-db-host> -U postgres -d postgres -f seed.sql
```

### 3. バックエンドセットアップ
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# .env を編集: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, GEMINI_API_KEY

# 開発サーバー起動
uvicorn app.main:app --reload --port 8000
```

### 4. フロントエンドセットアップ
```bash
cd frontend
npm install

# 環境変数設定
cp .env.example .env.local
# .env.local を編集: NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY

# 開発サーバー起動
npm run dev
```

### 5. アクセス
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 📁 プロジェクト構成

```
revenue-intelligence-platform/
├── README.md                         # このファイル
├── .gitignore                        # Git除外設定
│
├── backend/                          # FastAPI マイクロサービス
│   ├── app/
│   │   ├── main.py                  # 17エンドポイント定義
│   │   └── services/                # Gemini API, CrewAI, LangGraph
│   ├── .env.example                 # 環境変数テンプレート
│   ├── requirements.txt
│   └── venv/                        # Python仮想環境（.gitignore対象）
│
├── frontend/                         # Next.js フロントエンド
│   ├── app/                         # 5画面実装
│   │   ├── page.tsx                # ランディングページ
│   │   ├── dashboard/              # Revenue Intelligence Dashboard
│   │   ├── deals/                  # 商談一覧・詳細
│   │   └── agents/                 # AI Agents（CrewAI + LangGraph）
│   ├── components/ui/               # UIコンポーネント
│   ├── lib/                         # ユーティリティ
│   ├── .env.example
│   ├── package.json
│   └── node_modules/                # npm依存関係（.gitignore対象）
│
├── database/                         # DB定義
│   ├── README.md                    # スキーマドキュメント（16テーブル構造）
│   ├── schema-design-final.md       # 完全なスキーマ定義（16テーブル、30外部キー、3NF）
│   ├── database-complete-implementation-plan.md  # Phase 0-7実装プラン
│   └── .env.example
│
├── supabase/                         # Supabase CLI自動生成ディレクトリ
│   ├── migrations/                  # DBマイグレーション管理（空）
│   └── .temp/                       # CLI一時ファイル（自動生成、.gitignore対象）
│
├── domain-models/                    # ドメインモデル定義
│   ├── 企業プロフィール詳細.md      # 営業担当・エージェントプロフィール
│   ├── 60商談_顧客プロフィール.md   # 商談詳細（課題、予算、競合）
│   └── README.md
│
├── docs/                             # ドキュメント
│   └── original_plan/               # 初期実装計画（アーカイブ）
│       ├── 00_実装計画.md
│       ├── 01_モックデータ仕様.md
│       ├── 03_API仕様.md
│       └── 04_開発スケジュール.md
│
├── scripts/                          # ユーティリティスクリプト
│   ├── README.md                    # スクリプト用途説明
│   ├── generation/                  # データ生成
│   ├── validation/                  # データ検証
│   ├── backup/                      # バックアップ
│   ├── export/                      # データエクスポート
│   ├── dev/                         # ローカル開発
│   └── archive/                     # 廃止スクリプト
│
└── memory-bank/                      # プロジェクト進捗管理
    ├── activeContext.md
    ├── progress.md
    ├── techContext.md
    ├── systemPatterns.md
    ├── projectbrief.md
    └── productContext.md
```

---

## 🎯 主要機能

### Revenue Intelligence（10機能）
1. **Deal Risk Analysis** - 商談リスク分析（失注確率予測）
2. **Win Probability** - 成約確率予測（ML モデル）
3. **Deal Velocity Tracking** - 商談速度追跡（ステージ別滞留時間）
4. **Competitor Mentions** - 競合言及分析（トランスクリプト解析）
5. **Stakeholder Mapping** - ステークホルダーマッピング（影響力分析）
6. **Objection Patterns** - 反論パターン検出（頻出異議抽出）
7. **Champion Detection** - チャンピオン検出（推進者特定）
8. **Budget Signals** - 予算シグナル検出（予算確保状況分析）
9. **Timeline Prediction** - タイムライン予測（成約時期予測）
10. **Next Best Action** - 次の最善アクション提案

### Suggestion Engine（3機能）
1. **Email Template Generation** - コンテキストに基づくメール生成
2. **Meeting Agenda Creation** - ミーティングアジェンダ作成
3. **Follow-up Recommendations** - フォローアップ推奨事項

### AI Agents
- **CrewAI Multi-Agent**: EmailWorker, DocumentWorker, CRMWorker
- **LangGraph Workflow**: インテリジェントタスク自動化

---

## 🛠️ 開発ワークフロー

### ローカル開発
```bash
# バックエンド（ターミナル1）
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# フロントエンド（ターミナル2）
cd frontend
npm run dev
```

### データ生成・検証
```bash
# データ生成（Phase 1）
cd scripts/generation
python3 data_refresh_implementation.py

# Transcript生成（Phase 2）
python3 phase2_generate_transcripts_v3.py

# データ検証（Phase 3）
cd ../validation
python3 phase3_verify_data_quality.py
```

詳細は [scripts/README.md](scripts/README.md) を参照

---

## 🌐 デプロイ

### Frontend（Vercel）
```bash
cd frontend
vercel --prod
```

### Backend（Railway）
```bash
cd backend
railway up
```

### Database（Supabase）
- Supabaseダッシュボード > SQL Editor で `database/schema.sql` を実行
- その後、`database/seed.sql` を実行してサンプルデータを投入

---

## 📊 データ品質

### 業界標準準拠メトリクス（Phase 0-7完了後、別ブランチ）

**⚠️ 重要**: Phase 0-7は別ブランチ `feature/data-generation-phase0-7` で完全実装完了

| 項目 | 目標値 | 実績値 | ステータス |
|-----|--------|--------|-----------|
| **テーブル数** | 16テーブル | 16テーブル（companies + 15新規） | ✅ 合格 |
| **外部キー数** | 30個 | 30個 | ✅ 合格 |
| **正規化レベル** | 3NF | 3NF（Third Normal Form） | ✅ 合格 |
| **企業プロフィール** | 300社 | 300社 | ✅ 合格 |
| **商談データ** | 2,000件以上 | 2,251件 | ✅ 合格 |
| **ステークホルダー** | 800-900名 | 800-900名 | ✅ 合格 |
| **ステージ分布** | 業界標準ファンネル | Prospect > Meeting > Proposal > Closed Won | ✅ 合格 |
| **Stakeholders設定率** | 100% | 100%（全商談設定済み） | ✅ 合格 |
| **競合設定率** | 80%以上 | 100%（全商談設定済み） | ✅ 合格 |
| **ミーティング・メール** | 大量生成 | Phase 3-5で生成完了 | ✅ 合格 |
| **CS活動履歴** | 生成完了 | Phase 7で生成完了 | ✅ 合格 |

詳細は [database/README.md](database/README.md) を参照

---

## 🔐 環境変数

### Backend (.env)
```bash
# Supabase
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# Gemini API
GEMINI_API_KEY=your-gemini-api-key-here

# CORS（本番環境のみ）
FRONTEND_URL=https://your-vercel-app.vercel.app
```

### Frontend (.env.local)
```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here

# Backend API（本番環境のみ）
NEXT_PUBLIC_API_URL=https://your-railway-app.railway.app
```

テンプレートは各ディレクトリの `.env.example` を参照

---

## 📚 ドキュメント

### データベース関連（⚠️ 必読）
- **[データベーススキーマ](database/README.md)** - 16テーブル構造、バージョン履歴（v2.0.0）
- **[スキーマ定義](database/schema-design-final.md)** - 完全なDDL定義（16テーブル、30外部キー、3NF）
- **[実装プラン](database/database-complete-implementation-plan.md)** - Phase 0-7詳細プラン

### プロジェクト全体
- [実装計画](docs/original_plan/00_実装計画.md) - プロジェクト全体計画（初期版）
- [モックデータ仕様](docs/original_plan/01_モックデータ仕様.md) - DBスキーマとデータ仕様（初期版、Deprecated）
- [API仕様](docs/original_plan/03_API仕様.md) - 20個のエンドポイント仕様（初期版）
- [開発スケジュール](docs/original_plan/04_開発スケジュール.md) - Day 1-4タスク分解（初期版）
- [ドメインモデル](domain-models/README.md) - ビジネスコンテキスト定義
- [スクリプト](scripts/README.md) - ユーティリティスクリプト用途

---

## 🤝 コントリビューション

### 開発原則
1. **Single Responsibility**: 1ファイル1責務
2. **Extensive Comments**: 各関数にdocstring
3. **Incremental Development**: 小さく動かす、大きく育てる

### Git ワークフロー
```bash
# 新機能開発
git checkout -b feature/your-feature-name
# 実装 + コミット
git commit -m "Add: 機能説明"
# プッシュ
git push origin feature/your-feature-name
```

---

## 📝 ライセンス

MIT License

---

## 📞 サポート

- Issues: [GitHub Issues](https://github.com/your-repo/issues)
- Documentation: [/docs](/docs)
- Email: support@example.com

---

**作成日**: 2025年11月3日
**最終更新**: 2025年11月6日
**プロジェクト期間**: 2025年10月28日〜11月6日
**ステータス**: Phase 0-7完全実装完了（別ブランチ `feature/data-generation-phase0-7`）
**次のタスク**: デモ動画作成（5分間、2-3時間）
