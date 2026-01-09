# Tech Context - Revenue Intelligence Platform

**最終更新**: 2025年11月3日 09:30

---

## 🔴 重要: プロジェクトパス変更について

**プロジェクトパスが変更されました**（Turbopack UTF-8バグ解決のため）:
- **旧パス**: `/Users/test/Desktop/fukugyo_plan/01_基本計画/revenue-intelligence-platform/`
- **新パス**: `/Users/test/Desktop/fukugyo_plan/revenue-intelligence-platform/` ← **現在使用中**

### Supabase Docker Volume情報

**Day 1で作成したモックデータは、Dockerボリュームに保存されています**:
```bash
# Dockerボリューム一覧
docker volume ls --filter label=com.supabase.cli.project=frontend

# 保存されているボリューム
- supabase_db_frontend          # PostgreSQLデータ（2社分、60商談、99ミーティング、226メール）
- supabase_storage_frontend     # ストレージデータ
- supabase_config_frontend      # 設定データ
```

**新パスでのSupabase起動方法**:
```bash
# 新パスでSupabaseを起動（空のデータベースが作成される）
cd /Users/test/Desktop/fukugyo_plan/revenue-intelligence-platform
npx supabase start

# 既存データを使用するには、旧パスで起動するか、
# 新パスで起動後にデータを移行する必要がある
```

---

## 技術スタック概要

### フロントエンド
```
Next.js 14 (App Router)
├── TypeScript 5.x
├── React 18.x
├── Tailwind CSS 3.x
├── @tanstack/react-query 5.x (状態管理)
├── Recharts 2.x (グラフ可視化)
├── date-fns 3.x (日付操作)
└── Zod 3.x (バリデーション)
```

### バックエンド
```
Next.js API Routes (軽量ビジネスロジック)
├── CRUD操作 (Supabase/SQLite)
├── キャッシュ管理 (Redis)
└── セッション管理

FastAPI (AI/ML専用マイクロサービス)
├── Python 3.11
├── Pydantic 2.x (バリデーション)
├── Uvicorn (ASGIサーバー)
└── python-dotenv (環境変数)
```

### AI/ML
```
Google Gemini API
├── Gemini 2.0 Flash Experimental (無料枠)
├── text-embedding-004 (Embedding)
├── google-generativeai 0.8.x (Python SDK)
└── Redis (キャッシュ層)

AI Agents
├── CrewAI 0.76.x (Multi-Agent)
├── LangGraph 0.2.x (State Orchestration)
└── LangChain 0.3.x (依存ライブラリ)
```

### データベース
```
Supabase (本番環境)
├── PostgreSQL 15.x
├── @supabase/supabase-js 2.x
└── Supabase CLI (ローカル開発)

SQLite (個社データ)
├── sqlite3 3.x
└── テスト・開発環境用

Redis (キャッシュ)
├── Redis 7.x
├── redis-py 5.x (Python)
└── TTL: 7日間
```

### デプロイ・インフラ
```
Vercel (フロントエンド)
├── Next.js 14最適化
├── Edge Functions
└── 環境変数管理

Railway (FastAPI)
├── Dockerコンテナ
├── 環境変数管理
└── 自動スケーリング

Supabase (本番DB)
├── PostgreSQL Hosted
├── Row Level Security
└── 自動バックアップ
```

---

## 開発環境セットアップ

### 必須ツール
```bash
# Node.js & npm
node --version  # v20.x以上
npm --version   # v10.x以上

# Python & pip
python --version  # v3.11以上
pip --version     # v24.x以上

# Git
git --version  # v2.x以上
```

### プロジェクト初期化（Next.js）
```bash
# プロジェクト作成
npx create-next-app@latest revenue-intelligence-platform \
  --typescript --tailwind --app --use-npm

# 依存関係インストール
cd revenue-intelligence-platform
npm install @supabase/supabase-js @tanstack/react-query
npm install recharts date-fns zod
npm install -D @types/node

# Supabase CLI セットアップ
npx supabase init
npx supabase start  # ローカル環境起動
```

### プロジェクト初期化（FastAPI）
```bash
# FastAPIプロジェクト作成
mkdir backend && cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install fastapi uvicorn python-dotenv
pip install google-generativeai redis
pip install pydantic sqlalchemy
pip install crewai langgraph langchain
```

---

## プロジェクトディレクトリ構成

**最終更新**: 2025年11月3日（フォルダ構成最適化Phase 1-5完了）

### 最上位構成
```
revenue-intelligence-platform/
├── README.md                         # プロジェクト全体概要（Phase 5新規作成）
├── .gitignore                        # Git除外設定（Phase 1修正）
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
├── database/                         # DB定義（Phase 2: 旧supabase/）
│   ├── migrations/
│   │   └── 20251028000000_create_initial_schema.sql
│   ├── seed.sql                     # ダミーデータ（60企業、60商談、116ミーティング）
│   └── .env.example
│
├── domain-models/                    # ドメインモデル定義（Phase 3: 旧docs/data-definitions/）
│   ├── 企業プロフィール詳細.md      # 営業担当・エージェントプロフィール（37KB）
│   ├── 60商談_顧客プロフィール.md   # 商談詳細（課題、予算、競合）（27KB）
│   └── README.md
│
├── docs/                             # ドキュメント
│   └── original_plan/               # 初期実装計画（アーカイブ）
│       ├── 00_実装計画.md
│       ├── 01_モックデータ仕様.md
│       ├── 03_API仕様.md
│       └── 04_開発スケジュール.md
│
├── scripts/                          # ユーティリティスクリプト（Phase 4整理完了）
│   ├── README.md                    # スクリプト用途説明
│   ├── generation/                  # データ生成スクリプト
│   │   ├── data_refresh_implementation.py (25KB)
│   │   └── phase2_generate_transcripts_v3.py (68KB)
│   ├── validation/                  # データ検証スクリプト
│   │   └── phase3_verify_data_quality.py (8KB)
│   ├── backup/                      # バックアップスクリプト
│   │   ├── backup_supabase_full.py
│   │   └── supabase_backup_full_20251102_073312.json (4.08MB)
│   ├── export/                      # データエクスポート
│   │   ├── query_supabase_data.py
│   │   ├── export_meeting_contexts.sh
│   │   └── meeting_contexts*.jsonl
│   ├── dev/                         # ローカル開発スクリプト
│   │   ├── checkCustomerSize.ts
│   │   ├── testSupabaseConnection.ts
│   │   └── testEnvVars.ts
│   └── archive/                     # 廃止スクリプト（45件）
│
└── memory-bank/                      # プロジェクト進捗管理
    ├── activeContext.md
    ├── progress.md
    ├── techContext.md
    ├── systemPatterns.md
    ├── projectbrief.md
    └── productContext.md
```

### パス参照表（Phase 1-5での変更）

| 用途 | 旧パス | 新パス | Phase |
|------|--------|--------|-------|
| **DB定義全体** | `supabase/` | `database/` | Phase 2 |
| **シードSQL** | `supabase/seed.sql` | `database/seed.sql` | Phase 2 |
| **マイグレーション** | `supabase/migrations/` | `database/migrations/` | Phase 2 |
| **ドメインモデル全体** | `docs/data-definitions/` | `domain-models/` | Phase 3 |
| **企業プロフィール** | `docs/data-definitions/企業プロフィール詳細.md` | `domain-models/企業プロフィール詳細.md` | Phase 3 |
| **商談プロフィール** | `docs/data-definitions/60商談_顧客プロフィール.md` | `domain-models/60商談_顧客プロフィール.md` | Phase 3 |
| **スクリプト管理** | `scripts/` (混在) | `scripts/{generation,validation,backup,export,dev,archive}/` | Phase 4 |
| **データ生成** | `scripts/data_refresh_implementation.py` | `scripts/generation/data_refresh_implementation.py` | Phase 4 |
| **データ検証** | `scripts/phase3_verify_data_quality.py` | `scripts/validation/phase3_verify_data_quality.py` | Phase 4 |
| **開発スクリプト** | `frontend/scripts/*.ts` | `scripts/dev/*.ts` | Phase 4 |
| **廃止スクリプト** | `scripts/archive-scripts/` | `scripts/archive/` | Phase 4 |

### スクリプト実行時のパス更新例

```bash
# データ生成（Phase 1）
# 旧: python3 scripts/data_refresh_implementation.py
# 新:
cd scripts/generation
python3 data_refresh_implementation.py

# Transcript生成（Phase 2）
# 旧: python3 scripts/phase2_generate_transcripts_v3.py
# 新:
cd scripts/generation
python3 phase2_generate_transcripts_v3.py

# データ検証（Phase 3）
# 旧: python3 scripts/phase3_verify_data_quality.py
# 新:
cd scripts/validation
python3 phase3_verify_data_quality.py

# 開発スクリプト
# 旧: npx ts-node frontend/scripts/testSupabaseConnection.ts
# 新:
cd scripts/dev
npx ts-node testSupabaseConnection.ts
```

---

## 環境変数

### Next.js (.env.local)
```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# FastAPI
NEXT_PUBLIC_FASTAPI_URL=http://localhost:8000

# Redis
REDIS_URL=redis://localhost:6379
```

### FastAPI (.env)
```bash
# Gemini API
GEMINI_API_KEY=your-gemini-api-key

# Redis
REDIS_URL=redis://localhost:6379

# Database
DATABASE_URL=sqlite:///./data/revenue-intelligence.db

# Rate Limiting
MAX_REQUESTS_PER_DAY=14
CACHE_TTL_SECONDS=604800  # 7日間
```

---

## Gemini API無料枠戦略（重要）

### 無料枠制限
```
制限値: 1,500 requests/day
目標使用量: 無料枠内（1,500 requests/day以内）
実装方針: シンプル実装優先（キャッシュなし）
```

### 予算アラート設定
```python
# 日次リクエスト数追跡
daily_requests = await redis.incr("gemini_requests_today")

# アラート閾値（無料枠の80%）
if daily_requests >= 1200:
    logger.warning("Gemini API: 1,200 requests/day reached (80% of free tier)")
if daily_requests >= 1500:
    raise Exception("Gemini API: 1,500 requests/day limit exceeded (100% of free tier)")
```

### リクエスト数見積もり

プロトタイプ実装期間（4日間）では、無料枠内で自由に使用可能。

**目標**: 開発・テスト期間中は無料枠（1,500 requests/day）を超えないこと

### 2025年11月以降の最適化計画

キャッシュ実装を導入し、API呼び出しを削減する予定:

#### 最適化1: Redis Cache（削減率50%目標）
```python
# キャッシュキー設計
cache_key = f"deal_risk_{deal_id}_{hash(deal_data)}"

# TTL: 7日間（604,800秒）
await redis.set(cache_key, result, ex=604800)

# キャッシュヒット時はGemini API呼び出しスキップ
cached = await redis.get(cache_key)
if cached:
    return json.loads(cached)
```

#### 最適化2: Batch Processing（削減率70-80%目標）
```python
# 複数商談を1回のAPI呼び出しで処理
prompt = f"""
以下の商談のリスクスコアを一括計算してください。

商談1: {deal_1_data}
商談2: {deal_2_data}
...
"""

# バッチサイズに応じて削減効果向上
```

**予想削減効果**: API呼び出し70-80%削減

---

## 依存関係詳細

### package.json（Next.js）
```json
{
  "dependencies": {
    "next": "14.2.0",
    "react": "18.3.0",
    "react-dom": "18.3.0",
    "typescript": "5.4.0",
    "@supabase/supabase-js": "2.45.0",
    "@tanstack/react-query": "5.56.0",
    "recharts": "2.12.0",
    "date-fns": "3.6.0",
    "zod": "3.23.0",
    "tailwindcss": "3.4.0"
  },
  "devDependencies": {
    "@types/node": "20.14.0",
    "@types/react": "18.3.0",
    "eslint": "8.57.0",
    "prettier": "3.3.0"
  }
}
```

### requirements.txt（FastAPI）
```txt
fastapi==0.115.0
uvicorn==0.34.0
python-dotenv==1.0.1
google-generativeai==0.8.3
redis==5.2.0
pydantic==2.9.0
sqlalchemy==2.0.35
crewai==0.76.0
langgraph==0.2.45
langchain==0.3.7
```

---

## データベーススキーマ

### Supabase（PostgreSQL）

#### companies テーブル
```sql
CREATE TABLE companies (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  industry TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### deals テーブル
```sql
CREATE TABLE deals (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID REFERENCES companies(id),
  salesperson_name TEXT NOT NULL,
  deal_name TEXT NOT NULL,
  stage TEXT NOT NULL,
  amount DECIMAL NOT NULL,
  close_date DATE,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### meetings テーブル
```sql
CREATE TABLE meetings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  deal_id UUID REFERENCES deals(id),
  meeting_date TIMESTAMP NOT NULL,
  transcript TEXT,
  attendees JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### emails テーブル
```sql
CREATE TABLE emails (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  deal_id UUID REFERENCES deals(id),
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  sent_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## デプロイ戦略

### Vercel（Next.js）
```bash
# Vercel CLI インストール
npm i -g vercel

# デプロイ
vercel --prod

# 環境変数設定
vercel env add NEXT_PUBLIC_SUPABASE_URL production
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
vercel env add SUPABASE_SERVICE_ROLE_KEY production
vercel env add NEXT_PUBLIC_FASTAPI_URL production
```

### Railway（FastAPI）
```bash
# Railway CLI インストール
npm i -g @railway/cli

# プロジェクト作成
railway init

# デプロイ
railway up

# 環境変数設定
railway variables set GEMINI_API_KEY=xxx
railway variables set REDIS_URL=xxx
railway variables set DATABASE_URL=xxx
```

### Supabase Production
```bash
# プロジェクト作成
npx supabase projects create revenue-intelligence-platform

# マイグレーション実行
npx supabase db push

# モックデータ投入
npm run seed:production
```

---

## パフォーマンス目標

### Next.js API Routes
- 平均レスポンス: < 100ms
- P95レスポンス: < 200ms
- 同時接続: 10リクエスト/秒

### FastAPI
- 平均レスポンス: < 2,000ms（Gemini API含む）
- P95レスポンス: < 5,000ms
- 同時接続: 5リクエスト/秒

### フロントエンド
- 初期ロード: < 3秒
- Lighthouse Performance: 90+
- Core Web Vitals: すべてGood

---

## セキュリティ

### API Key管理
```bash
# 環境変数で管理（.envファイルはGit管理外）
.env.local
.env

# Vercel/Railway環境変数に登録
# ハードコード禁止
```

### Rate Limiting
```python
# FastAPI: 1日あたりのリクエスト数制限
MAX_REQUESTS_PER_DAY = 1500  # Gemini API無料枠

# 超過時はエラー
if daily_requests > MAX_REQUESTS_PER_DAY:
    raise HTTPException(status_code=429, detail="Rate limit exceeded")
```

### CORS設定
```python
# FastAPI: Next.jsのみ許可
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-vercel-app.vercel.app"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)
```

---

## トラブルシューティング

### Gemini API無料枠超過
**症状**: 429 Too Many Requests
**対策**:
1. Redisキャッシュの確認（`redis-cli KEYS "deal_risk_*"`）
2. バッチ処理の確認（1回のAPI呼び出しで複数処理）
3. 手動テストで補完（Gemini API呼び出しをスキップ）

### Supabaseローカル環境が起動しない
**症状**: `npx supabase start`でエラー
**対策**:
1. Dockerが起動しているか確認
2. ポート54321が空いているか確認（`lsof -i :54321`）
3. `npx supabase stop`して再起動

### FastAPIがimportエラー
**症状**: `ModuleNotFoundError: No module named 'crewai'`
**対策**:
1. 仮想環境が有効か確認（`which python`）
2. `pip install -r requirements.txt`を再実行
3. Python 3.11以上を使用しているか確認

---

## 関連ドキュメント

- [API仕様](../03_API仕様.md): エンドポイント詳細
- [開発スケジュール](../04_開発スケジュール.md): Day 1-4のタスク
- [System Patterns](systemPatterns.md): アーキテクチャパターン
