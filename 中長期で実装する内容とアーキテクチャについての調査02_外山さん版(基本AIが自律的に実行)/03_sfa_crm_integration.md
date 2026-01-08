# SFA/CRM連携

## 調査日
2026-01-09

## 調査目的

ボイスメモアプリの文字起こしデータを revenue-intelligence-platform（SFA/CRMシステム）と連携する方式を調査・決定する。

### 明らかにしたいこと
1. 連携方式（REST API / GraphQL / Webhook / 共有DB）の最適解
2. データ形式・スキーマ設計
3. 認証方式の選定
4. リアルタイム性（同期 vs 非同期）の要件と実現方式
5. エラーハンドリング・リトライ戦略

---

## 既存システム分析

### revenue-intelligence-platform の構成

```
revenue-intelligence-platform/
├── backend/                      # FastAPI マイクロサービス
│   ├── app/
│   │   ├── main.py              # 17エンドポイント定義
│   │   └── services/
│   │       ├── gemini_service.py    # AI分析サービス
│   │       ├── agent_service.py     # CrewAI Multi-Agent
│   │       └── workflow_service.py  # LangGraph Workflow
├── frontend/                     # Next.js 14 (App Router)
├── database/                     # Supabase (PostgreSQL) - 16テーブル
└── docs/                         # API仕様書
```

### 既存APIエンドポイント

| カテゴリ | エンドポイント | 認証方式 |
|---------|--------------|---------|
| **AI分析** | POST `/api/analyze-deal-risk` | API Key (X-API-Key) |
| | POST `/api/analyze-win-rate` | API Key |
| | POST `/api/generate-next-actions` | API Key |
| | POST `/api/summarize-meetings` | API Key |
| **Suggestion** | POST `/api/suggest-next-best-action` | API Key |
| | POST `/api/detect-risk-alerts` | API Key |
| **Multi-Agent** | POST `/api/agents/email` | API Key |
| | POST `/api/agents/document` | API Key |
| | POST `/api/agents/crm` | API Key |
| | POST `/api/agents/workflow` | API Key |
| **Workflow** | POST `/api/workflow/execute` | API Key |

### 既存データスキーマ（関連テーブル）

```sql
-- ミーティング記録
meetings (
  id, deal_id,
  date, duration_minutes, meeting_type, location,
  transcript, summary,              -- ← 文字起こしデータ
  created_by, meeting_owner_id,
  created_at
)

-- 商談マスタ
deals (
  id, company_id, deal_name, customer_name,
  stage, amount, probability,
  last_contact_date, next_action,
  ...
)
```

---

## 調査結果

### 1. 連携方式の比較

| 方式 | メリット | デメリット | 適用ケース |
|------|---------|-----------|-----------|
| **REST API** | シンプル、広く普及、ツール充実 | ポーリング必要、オーバーフェッチ | CRUD操作、オンデマンドアクセス |
| **GraphQL** | 柔軟なクエリ、型安全、単一エンドポイント | 学習コスト、キャッシュ複雑 | 複雑なデータ取得、BFF |
| **Webhook** | リアルタイム、プッシュ型、効率的 | エンドポイント公開必要、順序保証困難 | イベント通知、状態変更検知 |
| **共有DB** | 低遅延、シンプル | 密結合、スケーラビリティ問題 | 非推奨（マイクロサービスではアンチパターン）|

#### 2025-2026年のトレンド

- **REST API**: 依然として最も普及（Postman調査: 74%の組織が「API-first」）
- **GraphQL Federation**: マイクロサービス間のAPI統合で採用増加
- **Event-Driven Architecture**: リアルタイム連携の標準化（AsyncAPI仕様）
- **ハイブリッドアプローチ**: REST + Webhook の組み合わせが主流

### 2. 認証方式の比較

| 方式 | 複雑さ | ユーザーコンテキスト | 有効期限 | 取り消し容易性 | 適用ケース |
|------|-------|-------------------|---------|--------------|-----------|
| **API Key** | 低 | なし | オプション | 容易 | 内部API、M2M通信 |
| **JWT** | 中 | あり | あり | 困難 | ステートレスAPI、分散システム |
| **OAuth 2.0** | 高 | あり | あり | 中 | サードパーティ連携、スコープ制御 |

#### 推奨: ハイブリッドアプローチ

```
ボイスメモアプリ → (JWT) → Transcription Service
Transcription Service → (API Key + JWT) → revenue-intelligence-platform
```

- **サービス間通信**: API Key（シンプル、内部通信）
- **ユーザー認証**: JWT（ステートレス、自己完結型）
- **将来のサードパーティ連携**: OAuth 2.0（スコープ制御）

### 3. リアルタイム性の検討

| 要件 | 方式 | 遅延 | 実装難易度 |
|------|-----|------|-----------|
| **即時通知** | Webhook / WebSocket | < 1秒 | 中 |
| **準リアルタイム** | ポーリング（短間隔） | 1-30秒 | 低 |
| **バッチ処理** | 定期同期 | 分〜時間 | 低 |

#### 文字起こし連携の要件分析

```
┌─────────────────────────────────────────────────────────────────┐
│                     データフロー                                  │
│                                                                 │
│  [iPhone App] ──録音──▶ [Cloud Storage]                         │
│       │                      │                                  │
│       │                      ▼                                  │
│       │              [Transcription Service]                    │
│       │                      │                                  │
│       │                      │ (Webhook: 文字起こし完了)          │
│       │                      ▼                                  │
│       │              [revenue-intelligence-platform]            │
│       │                      │                                  │
│       │                      │ (REST API: AI分析結果取得)         │
│       ◀──────────分析結果表示───┘                                │
└─────────────────────────────────────────────────────────────────┘
```

**推奨**:
- **文字起こし完了通知**: Webhook（イベント駆動、効率的）
- **AI分析結果取得**: REST API（オンデマンド、柔軟）
- **バルクデータ同期**: 定期バッチ（夜間同期など）

### 4. エラーハンドリング戦略

#### 4.1 リトライ戦略

```python
# 推奨: Exponential Backoff with Jitter
retry_config = {
    "max_attempts": 5,
    "base_delay": 1.0,  # 秒
    "max_delay": 60.0,  # 秒
    "jitter": True,     # ランダム化でThundering Herd防止
    "retryable_status_codes": [429, 500, 502, 503, 504]
}
```

#### 4.2 エラー分類

| エラー種別 | HTTPステータス | リトライ | 対応 |
|-----------|--------------|---------|------|
| 一時的エラー | 429, 500, 502, 503, 504 | ○ | Exponential Backoff |
| クライアントエラー | 400, 401, 403, 404 | × | 即座にエラー返却 |
| データ整合性エラー | 409 Conflict | △ | 最新データ取得後リトライ |

#### 4.3 Circuit Breaker パターン

```
┌──────────────────────────────────────────────┐
│              Circuit Breaker                  │
│                                              │
│  [Closed] ──失敗5回以上──▶ [Open]             │
│     ▲                         │              │
│     │                    30秒経過             │
│     │                         ▼              │
│     └───────成功───── [Half-Open]            │
└──────────────────────────────────────────────┘
```

#### 4.4 冪等性の確保

```json
// リクエストに一意のidempotency_keyを含める
{
  "idempotency_key": "transcript-uuid-12345",
  "recording_id": "rec-001",
  "transcript_text": "...",
  "timestamp": "2026-01-09T10:00:00Z"
}
```

### 5. データ形式・スキーマ設計

#### 5.1 文字起こしデータ送信スキーマ

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["recording_id", "transcript", "metadata"],
  "properties": {
    "idempotency_key": {
      "type": "string",
      "format": "uuid"
    },
    "recording_id": {
      "type": "string",
      "description": "ボイスメモアプリでの録音ID"
    },
    "transcript": {
      "type": "object",
      "properties": {
        "text": {
          "type": "string",
          "description": "文字起こし全文"
        },
        "segments": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "start_time": { "type": "number" },
              "end_time": { "type": "number" },
              "text": { "type": "string" },
              "speaker": { "type": "string" }
            }
          }
        },
        "language": {
          "type": "string",
          "default": "ja"
        }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "duration_seconds": { "type": "number" },
        "recorded_at": { "type": "string", "format": "date-time" },
        "device_type": { "type": "string" },
        "audio_format": { "type": "string" }
      }
    },
    "deal_context": {
      "type": "object",
      "description": "既存商談との紐付け情報（オプション）",
      "properties": {
        "deal_id": { "type": "string" },
        "customer_name": { "type": "string" }
      }
    }
  }
}
```

#### 5.2 API レスポンススキーマ

```json
{
  "status": "success | error",
  "data": {
    "meeting_id": "mtg-uuid-12345",
    "transcript_processed": true,
    "ai_analysis": {
      "summary": "ミーティング要約...",
      "key_points": ["ポイント1", "ポイント2"],
      "action_items": ["アクション1", "アクション2"],
      "sentiment": "positive | neutral | negative",
      "risk_score": 35
    },
    "linked_deal": {
      "deal_id": "deal-001",
      "updated_fields": ["last_contact_date", "next_action"]
    }
  },
  "error": {
    "code": "ERROR_CODE",
    "message": "エラーメッセージ",
    "details": {}
  }
}
```

---

## 推奨案

### アーキテクチャ概要

```
┌────────────────────────────────────────────────────────────────────────┐
│                          連携アーキテクチャ                              │
│                                                                        │
│  ┌─────────────┐      ┌─────────────────────┐      ┌────────────────┐ │
│  │  iPhone     │      │   Transcription     │      │   Revenue      │ │
│  │  VoiceMemo  │      │   Service           │      │   Intelligence │ │
│  │  App        │      │   (Cloud Run)       │      │   Platform     │ │
│  └─────────────┘      └─────────────────────┘      └────────────────┘ │
│        │                       │                          │           │
│        │ ① 録音アップロード     │                          │           │
│        │    (REST + JWT)       │                          │           │
│        ├──────────────────────▶│                          │           │
│        │                       │                          │           │
│        │                       │ ② 文字起こし完了通知       │           │
│        │                       │    (Webhook + API Key)   │           │
│        │                       ├─────────────────────────▶│           │
│        │                       │                          │           │
│        │                       │ ③ AI分析リクエスト         │           │
│        │                       │    (REST + API Key)      │           │
│        │                       │◀─────────────────────────┤           │
│        │                       │                          │           │
│        │ ④ 分析結果通知         │ ⑤ 分析結果レスポンス      │           │
│        │    (Push / Polling)   │    (REST)                │           │
│        │◀──────────────────────│◀─────────────────────────┤           │
│        │                       │                          │           │
└────────────────────────────────────────────────────────────────────────┘
```

### 技術選定

| 項目 | 選定 | 理由 |
|------|-----|------|
| **連携方式** | REST API + Webhook | シンプル＆リアルタイム通知の両立 |
| **データ形式** | JSON | 既存システム互換、可読性 |
| **認証（M2M）** | API Key + JWT | 内部通信はシンプルに、ユーザーコンテキストはJWTで |
| **認証（将来）** | OAuth 2.0 | サードパーティ連携時に導入 |
| **リアルタイム性** | Webhook（イベント通知）+ REST（データ取得） | ハイブリッド |
| **エラーハンドリング** | Exponential Backoff + Circuit Breaker | 業界標準パターン |

### 新規エンドポイント設計（revenue-intelligence-platform側）

```python
# 文字起こしデータ受信エンドポイント
@app.post("/api/v2/transcripts")
async def receive_transcript(
    request: TranscriptRequest,
    x_api_key: str = Header(...),
    x_idempotency_key: str = Header(None)
):
    """
    ボイスメモからの文字起こしデータを受信
    - 冪等性: x-idempotency-key ヘッダーで重複防止
    - 非同期処理: 受信後すぐにACK、バックグラウンドでAI分析
    """
    pass

# 文字起こし処理状況確認
@app.get("/api/v2/transcripts/{transcript_id}/status")
async def get_transcript_status(transcript_id: str):
    """処理状況: pending → processing → completed → analyzed"""
    pass

# Webhook登録
@app.post("/api/v2/webhooks")
async def register_webhook(webhook: WebhookRegistration):
    """文字起こし完了通知などのWebhook登録"""
    pass
```

---

## 参考資料

### Web検索結果

- [10 Best Practices for Microservices Architecture in 2025 - GeeksforGeeks](https://www.geeksforgeeks.org/blogs/best-practices-for-microservices-architecture/)
- [API Design Best Practices in 2025: Trends and Techniques - MyAppAPI](https://myappapi.com/blog/api-design-best-practices-2025)
- [REST API Authentication Guide 2025: 4 Methods Compared - Knowi](https://www.knowi.com/blog/4-ways-of-rest-api-authentication-methods/)
- [Top 7 API Authentication Methods Compared - Zuplo](https://zuplo.com/blog/2025/01/03/top-7-api-authentication-methods-compared)
- [API key vs JWT: Secure B2B SaaS - Scalekit](https://www.scalekit.com/blog/apikey-jwt-comparison)
- [Webhooks vs REST APIs: when to use one over the other - Merge](https://www.merge.dev/blog/rest-api-vs-webhooks)
- [Error handling in distributed systems - Temporal](https://temporal.io/blog/error-handling-in-distributed-systems)
- [API Retry Mechanism: How It Works + Best Practices - BoldSign](https://boldsign.com/blogs/api-retry-mechanism-how-it-works-best-practices/)
- [8 Salesforce Integration Patterns and Best Practices - CloudConsultings](https://cloudconsultings.com/salesforce-integration-patterns/)

### 既存リソース

- `/Users/test/Desktop/fukugyo_plan/revenue-intelligence-platform/docs/original_plan/03_API仕様.md`
- `/Users/test/Desktop/fukugyo_plan/revenue-intelligence-platform/database/README.md`
- `/Users/test/Desktop/fukugyo_plan/revenue-intelligence-platform/backend/app/main.py`

---

## 結論・決定事項

### 連携方式
**REST API + Webhook のハイブリッドアプローチを採用**

1. **文字起こしデータ送信**: REST API（POST /api/v2/transcripts）
2. **処理完了通知**: Webhook（イベント駆動）
3. **分析結果取得**: REST API（GET /api/v2/transcripts/{id}/analysis）

### 認証方式
**段階的導入**

| フェーズ | 認証方式 | 対象 |
|---------|---------|------|
| Phase 1 | API Key | 内部サービス間通信 |
| Phase 2 | API Key + JWT | ユーザーコンテキスト付与 |
| Phase 3 | OAuth 2.0 | 外部サービス連携（Salesforce等） |

### データ形式
- **JSON**（既存システム互換）
- **冪等性キー必須**（重複処理防止）
- **非同期処理**（大容量データ対応）

### エラーハンドリング
- **Exponential Backoff with Jitter**（最大5回、最大60秒待機）
- **Circuit Breaker**（連続5回失敗で30秒Open）
- **Dead Letter Queue**（処理失敗データの保全）

---

## 残課題

1. **Webhook署名検証の実装方式**
   - HMAC-SHA256 vs RSA署名の選定

2. **レート制限の設計**
   - 現在の15 req/min（Gemini API制限）との整合性

3. **データ保持ポリシー**
   - 文字起こしデータの保持期間
   - GDPR/個人情報保護法への対応

4. **テスト戦略**
   - 連携テストの自動化
   - モックサーバーの構築

5. **モニタリング・アラート**
   - 連携エラー率の監視閾値
   - アラート通知先の設計

---

**作成日**: 2026-01-09
**次回レビュー**: 統合アーキテクチャ策定時（テーマ5）
