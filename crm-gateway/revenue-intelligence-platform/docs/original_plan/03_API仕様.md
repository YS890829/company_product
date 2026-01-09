# API仕様書

**作成日**: 2025年10月27日
**バージョン**: 1.0.0
**アーキテクチャ**: Next.js API Routes + FastAPI Microservice

---

## 📋 API概要

### アーキテクチャ構成

```
フロントエンド（Next.js）
    ↓ fetch API
Next.js API Routes（軽量ビジネスロジック）
    ↓ HTTP Request
FastAPI（AI/ML専用マイクロサービス）
    ↓ Data Access
Supabase + SQLite
```

### エンドポイント一覧

| カテゴリ | エンドポイント | メソッド | 実装場所 |
|---------|--------------|---------|---------|
| **データCRUD** | `/api/companies` | GET/POST | Next.js |
| | `/api/deals` | GET/POST/PUT | Next.js |
| | `/api/meetings` | GET/POST | Next.js |
| **AI/ML** | `/api/v1/revenue-intelligence` | POST | FastAPI |
| | `/api/v1/suggestions` | POST | FastAPI |
| | `/api/v1/agents/email` | POST | FastAPI |
| | `/api/v1/agents/document` | POST | FastAPI |
| | `/api/v1/agents/crm` | POST | FastAPI |
| | `/api/v1/workflow` | POST | FastAPI |

---

## 🔷 Next.js API Routes（軽量ビジネスロジック）

### 1. 企業データCRUD

#### GET /api/companies

全企業データを取得

**リクエスト**:
```http
GET /api/companies
```

**レスポンス**:
```json
{
  "companies": [
    {
      "id": "saas-1",
      "name": "株式会社クラウドテック",
      "industry": "saas",
      "arr": 300000000,
      "sales_team_size": 10,
      "deals_count": 30
    }
  ],
  "total": 6
}
```

#### GET /api/companies/:id

特定企業の詳細データを取得

**リクエスト**:
```http
GET /api/companies/saas-1
```

**レスポンス**:
```json
{
  "id": "saas-1",
  "name": "株式会社クラウドテック",
  "industry": "saas",
  "arr": 300000000,
  "sales_team": [...],
  "deals": [...],
  "meetings": [...]
}
```

---

### 2. 商談データCRUD

#### GET /api/deals

商談データ一覧を取得

**クエリパラメータ**:
- `company_id`: 企業ID（必須）
- `stage`: stage絞り込み（オプション）
- `owner_id`: 担当者ID（オプション）
- `limit`: 取得件数（デフォルト: 50）
- `offset`: オフセット（デフォルト: 0）

**リクエスト**:
```http
GET /api/deals?company_id=saas-1&stage=proposal&limit=10
```

**レスポンス**:
```json
{
  "deals": [
    {
      "id": "saas1-deal-001",
      "customer_name": "株式会社マーケティングX",
      "stage": "proposal",
      "amount": 1500000,
      "probability": 0.65,
      "created_at": "2025-09-15",
      "updated_at": "2025-10-20",
      "owner_name": "佐藤花子"
    }
  ],
  "total": 6,
  "limit": 10,
  "offset": 0
}
```

#### POST /api/deals

新規商談を作成

**リクエスト**:
```json
{
  "company_id": "saas-1",
  "customer_name": "株式会社新規顧客",
  "stage": "prospect",
  "amount": 1000000,
  "owner_id": "saas1-rep1"
}
```

**レスポンス**:
```json
{
  "id": "saas1-deal-031",
  "created_at": "2025-10-27T10:00:00Z",
  "message": "Deal created successfully"
}
```

#### PUT /api/deals/:id

商談データを更新

**リクエスト**:
```json
{
  "stage": "meeting",
  "probability": 0.45,
  "next_action": "デモ実施予定"
}
```

**レスポンス**:
```json
{
  "id": "saas1-deal-001",
  "updated_at": "2025-10-27T10:05:00Z",
  "message": "Deal updated successfully"
}
```

---

### 3. 面談記録CRUD

#### GET /api/meetings

面談記録一覧を取得

**クエリパラメータ**:
- `deal_id`: 商談ID（必須）

**リクエスト**:
```http
GET /api/meetings?deal_id=saas1-deal-001
```

**レスポンス**:
```json
{
  "meetings": [
    {
      "id": "saas1-mtg-001",
      "deal_id": "saas1-deal-001",
      "date": "2025-10-15",
      "duration_minutes": 60,
      "summary": "予算確保済み、ROIに関心",
      "attendees": ["山田部長", "佐藤課長"]
    }
  ],
  "total": 3
}
```

#### POST /api/meetings

新規面談記録を作成

**リクエスト**:
```json
{
  "deal_id": "saas1-deal-001",
  "date": "2025-10-27",
  "duration_minutes": 45,
  "transcript": "商談内容のテキスト...",
  "attendees": ["山田部長"]
}
```

**レスポンス**:
```json
{
  "id": "saas1-mtg-002",
  "created_at": "2025-10-27T11:00:00Z",
  "message": "Meeting record created successfully"
}
```

---

### 4. キャッシュ管理

#### GET /api/cache/:key

キャッシュデータを取得

**リクエスト**:
```http
GET /api/cache/ri:saas-1
```

**レスポンス**:
```json
{
  "key": "ri:saas-1",
  "value": {...},
  "ttl": 3600,
  "cached_at": "2025-10-27T09:00:00Z"
}
```

#### DELETE /api/cache/:key

キャッシュをクリア

**リクエスト**:
```http
DELETE /api/cache/ri:saas-1
```

**レスポンス**:
```json
{
  "message": "Cache cleared successfully"
}
```

---

## 🔶 FastAPI（AI/ML専用マイクロサービス）

### ベースURL

- **開発環境**: `http://localhost:8000`
- **本番環境**: `https://your-fastapi.railway.app`

### 認証

すべてのエンドポイントでAPI Key認証を使用

**ヘッダー**:
```http
X-API-Key: your_api_key_here
```

---

### 1. Revenue Intelligence API

#### POST /api/v1/revenue-intelligence

Revenue Intelligence 10機能を一括計算

**リクエスト**:
```json
{
  "company_id": "saas-1",
  "deals": [
    {
      "id": "saas1-deal-001",
      "customer_name": "株式会社マーケティングX",
      "stage": "proposal",
      "amount": 1500000,
      "probability": 0.65,
      "created_at": "2025-09-15",
      "stakeholders": [...]
    }
  ],
  "sales_team": [
    {
      "id": "saas1-rep1",
      "name": "佐藤花子",
      "performance": {...}
    }
  ]
}
```

**レスポンス**:
```json
{
  "company_id": "saas-1",
  "calculated_at": "2025-10-27T10:00:00Z",
  "results": {
    "deal_risk_scores": [
      {
        "deal_id": "saas1-deal-001",
        "risk_score": 0.35,
        "risk_level": "medium",
        "risk_factors": [
          "予算確保が未確定",
          "競合他社も商談中"
        ]
      }
    ],
    "win_rate_analysis": {
      "overall_win_rate": 0.28,
      "by_stage": {
        "prospect": 0.15,
        "meeting": 0.25,
        "proposal": 0.40,
        "negotiation": 0.60
      },
      "by_rep": [
        {
          "rep_id": "saas1-rep1",
          "rep_name": "佐藤花子",
          "win_rate": 0.28,
          "deals_won": 12,
          "deals_total": 43
        }
      ]
    },
    "buyer_engagement_scores": [
      {
        "deal_id": "saas1-deal-001",
        "overall_score": 0.67,
        "stakeholders": [
          {
            "name": "山田部長",
            "engagement_score": 0.75,
            "last_contact_days_ago": 7
          }
        ]
      }
    ],
    "stakeholder_mapping": [
      {
        "deal_id": "saas1-deal-001",
        "stakeholders": [
          {
            "name": "山田部長",
            "title": "営業部長",
            "role": "決裁者",
            "influence": 0.9,
            "support_level": "champion"
          }
        ]
      }
    ],
    "champion_identification": [
      {
        "deal_id": "saas1-deal-001",
        "champions": [
          {
            "name": "山田部長",
            "champion_score": 0.85,
            "evidence": [
              "強力な支持表明",
              "社内調整を積極的に実施"
            ]
          }
        ]
      }
    ],
    "win_loss_analysis": {
      "total_won": 4,
      "total_lost": 2,
      "win_rate": 0.67,
      "common_win_factors": [
        "Champion存在",
        "ROI明確",
        "予算確保済み"
      ],
      "common_loss_factors": [
        "予算不足",
        "競合優位",
        "意思決定遅延"
      ]
    },
    "competitive_intelligence": {
      "top_competitors": [
        {
          "name": "Salesforce",
          "deals_count": 8,
          "win_rate_against": 0.40
        },
        {
          "name": "HubSpot",
          "deals_count": 5,
          "win_rate_against": 0.60
        }
      ]
    },
    "pipeline_velocity": {
      "avg_days_to_close": 45,
      "by_stage": {
        "prospect_to_meeting": 7,
        "meeting_to_proposal": 14,
        "proposal_to_negotiation": 10,
        "negotiation_to_close": 14
      },
      "bottleneck_stage": "meeting_to_proposal"
    },
    "next_best_actions": [
      {
        "deal_id": "saas1-deal-001",
        "actions": [
          {
            "action": "フォローアップ電話",
            "priority": "high",
            "due_date": "2025-10-23",
            "expected_impact": 0.15
          },
          {
            "action": "ROI再試算",
            "priority": "medium",
            "due_date": "2025-10-25",
            "expected_impact": 0.10
          }
        ]
      }
    ],
    "revenue_forecasting": {
      "forecast_30days": 4500000,
      "forecast_60days": 9000000,
      "forecast_90days": 13500000,
      "confidence_30days": 0.89,
      "confidence_60days": 0.75,
      "confidence_90days": 0.60,
      "accuracy_last_quarter": 0.87
    }
  }
}
```

---

### 2. Suggestion Engine API

#### POST /api/v1/suggestions

Next Action推奨とRisk Detectionを実行

**リクエスト**:
```json
{
  "company_id": "saas-1",
  "deal_id": "saas1-deal-001",
  "deal_data": {
    "stage": "proposal",
    "last_contact": "2025-10-20",
    "stakeholders": [...],
    "probability": 0.65
  }
}
```

**レスポンス**:
```json
{
  "deal_id": "saas1-deal-001",
  "suggestions": {
    "next_actions": [
      {
        "action": "フォローアップ電話（提案書送付後3日以内）",
        "priority": "high",
        "due_date": "2025-10-23",
        "reasoning": "提案書送付後3日が経過。顧客エンゲージメント維持のため緊急",
        "success_probability": 0.75
      },
      {
        "action": "Champion（山田部長）と1on1ミーティング設定",
        "priority": "high",
        "due_date": "2025-10-25",
        "reasoning": "決裁者との関係強化が成約率向上に直結",
        "success_probability": 0.65
      },
      {
        "action": "競合比較資料を作成・送付",
        "priority": "medium",
        "due_date": "2025-10-28",
        "reasoning": "Salesforceと比較検討中のため差別化資料が有効",
        "success_probability": 0.55
      }
    ],
    "risk_alerts": [
      {
        "risk_type": "budget_uncertainty",
        "severity": "medium",
        "description": "予算確保が未確定",
        "mitigation": "財務担当者を商談に巻き込む",
        "impact_on_probability": -0.15
      },
      {
        "risk_type": "competitor_threat",
        "severity": "medium",
        "description": "Salesforceも商談中",
        "mitigation": "価格優位性とROIを強調",
        "impact_on_probability": -0.10
      }
    ]
  }
}
```

#### POST /api/v1/suggestions/proposal

提案書ドラフトを生成

**リクエスト**:
```json
{
  "deal_id": "saas1-deal-001",
  "customer_data": {
    "name": "株式会社マーケティングX",
    "industry": "マーケティング",
    "pain_points": [
      "CRM活用率30%",
      "営業記録入力負担"
    ]
  },
  "template_type": "saas"
}
```

**レスポンス**:
```json
{
  "deal_id": "saas1-deal-001",
  "proposal": {
    "title": "株式会社マーケティングX様 Revenue Intelligence導入提案書",
    "sections": [
      {
        "title": "エグゼクティブサマリー",
        "content": "貴社の課題である「CRM活用率30%」「営業記録入力負担」を解決..."
      },
      {
        "title": "貴社の課題整理",
        "content": "現状分析: Salesforce導入済みだが活用率が低い..."
      }
    ],
    "roi_calculation": {
      "current_cost": 1800000,
      "proposed_cost": 1020000,
      "annual_saving": 6000000
    }
  }
}
```

---

### 3. AI Agents API

#### POST /api/v1/agents/email

Email Worker（フォローアップメール生成）

**リクエスト**:
```json
{
  "deal_id": "saas1-deal-001",
  "email_type": "followup_after_proposal",
  "recipient": {
    "name": "山田部長",
    "email": "yamada@marketing-x.co.jp",
    "title": "営業部長"
  },
  "context": {
    "proposal_sent_date": "2025-10-18",
    "key_points": ["ROI 520%", "投資回収期間2ヶ月"]
  }
}
```

**レスポンス**:
```json
{
  "deal_id": "saas1-deal-001",
  "email_draft": {
    "subject": "【株式会社マーケティングX様】提案書のご確認状況について",
    "body": "山田部長\n\nお世話になっております。株式会社クラウドテック 佐藤です。\n\n先日お送りした提案書はご確認いただけましたでしょうか？...",
    "optimal_send_time": "2025-10-23 10:00:00",
    "expected_open_rate": 0.75,
    "expected_response_rate": 0.45
  },
  "requires_approval": true,
  "approval_id": "approval-001"
}
```

#### POST /api/v1/agents/document

Document Worker（提案書自動生成）

**リクエスト**:
```json
{
  "deal_id": "saas1-deal-001",
  "document_type": "proposal",
  "customer_data": {...},
  "template_id": "saas_standard"
}
```

**レスポンス**:
```json
{
  "deal_id": "saas1-deal-001",
  "document": {
    "url": "https://storage.../proposal_saas1-deal-001.pdf",
    "pages": 15,
    "sections": [...],
    "generation_time_seconds": 30
  },
  "requires_approval": true,
  "approval_id": "approval-002"
}
```

#### POST /api/v1/agents/crm

CRM Worker（データ自動更新）

**リクエスト**:
```json
{
  "meeting_id": "saas1-mtg-001",
  "transcript": "商談音声の文字起こしテキスト...",
  "auto_update": false
}
```

**レスポンス**:
```json
{
  "meeting_id": "saas1-mtg-001",
  "extracted_data": {
    "stakeholders": [
      {
        "name": "山田部長",
        "title": "営業部長",
        "role": "決裁者"
      }
    ],
    "budget": 1500000,
    "timeline": "2026年1月導入希望",
    "next_actions": [
      "ROI試算資料送付",
      "フォローアップ電話"
    ],
    "sentiment": "positive"
  },
  "crm_update_preview": {
    "deal_id": "saas1-deal-001",
    "fields_to_update": {
      "budget": 1500000,
      "expected_close_date": "2026-01-15",
      "next_action": "ROI試算資料送付"
    }
  },
  "requires_approval": false
}
```

---

### 4. Workflow API

#### POST /api/v1/workflow

LangGraph State-based Orchestration実行

**リクエスト**:
```json
{
  "workflow_type": "end_to_end_sales",
  "deal_id": "saas1-deal-001",
  "initial_state": {
    "stage": "meeting",
    "risk_score": 0.35,
    "next_actions": []
  },
  "auto_execute": false
}
```

**レスポンス**:
```json
{
  "workflow_id": "workflow-001",
  "deal_id": "saas1-deal-001",
  "execution_log": [
    {
      "step": 1,
      "node": "analyze_deal",
      "status": "completed",
      "output": {
        "risk_score": 0.35,
        "next_actions": ["email_worker", "proposal_worker"]
      }
    },
    {
      "step": 2,
      "node": "email_worker",
      "status": "pending_approval",
      "output": {
        "email_draft": {...},
        "approval_id": "approval-003"
      }
    }
  ],
  "current_state": {
    "stage": "meeting",
    "risk_score": 0.35,
    "pending_approvals": ["approval-003"]
  },
  "next_steps": ["await_approval", "proposal_worker"]
}
```

#### GET /api/v1/workflow/:id

ワークフロー実行状況を取得

**リクエスト**:
```http
GET /api/v1/workflow/workflow-001
```

**レスポンス**:
```json
{
  "workflow_id": "workflow-001",
  "status": "in_progress",
  "progress": 0.40,
  "steps_completed": 2,
  "steps_total": 5,
  "execution_log": [...]
}
```

---

## 🔐 エラーレスポンス

### 標準エラーフォーマット

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Deal ID is required",
    "details": {
      "field": "deal_id",
      "constraint": "required"
    }
  }
}
```

### エラーコード一覧

| コード | HTTPステータス | 説明 |
|--------|--------------|------|
| `INVALID_REQUEST` | 400 | リクエストパラメータが不正 |
| `UNAUTHORIZED` | 401 | API Key認証エラー |
| `NOT_FOUND` | 404 | リソースが見つからない |
| `RATE_LIMIT_EXCEEDED` | 429 | レート制限超過 |
| `INTERNAL_ERROR` | 500 | サーバー内部エラー |
| `GEMINI_API_ERROR` | 503 | Gemini API呼び出しエラー |

---

## 📊 レート制限

### Next.js API Routes
- なし（開発環境）
- 本番環境: Vercel制限に準拠

### FastAPI
- 15 requests/minute（Gemini API制限に合わせる）
- 100 requests/hour
- 1,000 requests/day

---

## 🛠️ 開発環境セットアップ

### 環境変数

**Next.js (.env.local)**:
```bash
# FastAPI URL
FASTAPI_URL=http://localhost:8000

# Supabase
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# Redis
REDIS_URL=redis://localhost:6379
```

**FastAPI (.env)**:
```bash
# Gemini API
GEMINI_API_KEY=your_gemini_api_key

# Cloud Billing
GOOGLE_CLOUD_PROJECT=your_project_id

# Redis
REDIS_URL=redis://localhost:6379

# API Key
API_KEY=your_api_key_for_authentication
```

### ローカル起動

**Next.js**:
```bash
npm run dev
# http://localhost:3000
```

**FastAPI**:
```bash
cd backend
uvicorn app.main:app --reload
# http://localhost:8000
# Docs: http://localhost:8000/docs
```

---

**最終更新**: 2025年10月27日
**次回レビュー**: 2025年10月28日（実装開始時）
