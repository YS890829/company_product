# System Patterns - Revenue Intelligence Platform

**最終更新**: 2025年10月28日

---

## アーキテクチャ概要

### ハイブリッド型アーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│  フロントエンド（Next.js 14 App Router）                  │
│  ┌───────────────┐ ┌──────────────┐ ┌────────────────┐ │
│  │ Dashboard UI  │ │ Suggestion   │ │ AI Agents UI   │ │
│  │ (RI 10機能)   │ │ Engine UI    │ │ (CrewAI/       │ │
│  │               │ │ (3機能)      │ │  LangGraph)    │ │
│  └───────────────┘ └──────────────┘ └────────────────┘ │
└─────────────────────────────────────────────────────────┘
                        ↓ API Call
┌─────────────────────────────────────────────────────────┐
│  Next.js API Routes（軽量ビジネスロジック）               │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────┐ │
│  │ Companies   │ │ Deals        │ │ Sessions        │ │
│  │ CRUD        │ │ CRUD + Filter│ │ Management      │ │
│  └─────────────┘ └──────────────┘ └─────────────────┘ │
└─────────────────────────────────────────────────────────┘
                        ↓ HTTP Request
┌─────────────────────────────────────────────────────────┐
│  FastAPI（AI/ML専用マイクロサービス）                     │
│  ┌──────────────────┐ ┌───────────────────────────────┐│
│  │ Revenue          │ │ AI Agents                     ││
│  │ Intelligence     │ │ - CrewAI Multi-Agent          ││
│  │ (10機能)         │ │ - LangGraph Orchestration     ││
│  └──────────────────┘ └───────────────────────────────┘│
│  ┌──────────────────┐ ┌───────────────────────────────┐│
│  │ Suggestion       │ │ Gemini Service                ││
│  │ Engine (3機能)   │ │ - API呼び出し                  ││
│  │                  │ │ - 予算アラート                 ││
│  └──────────────────┘ └───────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
                        ↓ Data Access
┌─────────────────────────────────────────────────────────┐
│  データ層                                                │
│  ┌──────────────┐ ┌────────────┐ ┌──────────────────┐ │
│  │ Supabase     │ │ SQLite     │ │                  │ │
│  │ (マルチ      │ │ (個社      │ │                  │ │
│  │  テナント)   │ │  データ)   │ │                  │ │
│  └──────────────┘ └────────────┘ └──────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## デザインパターン

### 1. Repository Pattern（データアクセス層）

#### Next.js API Routes
```typescript
// app/api/companies/route.ts
import { createClient } from '@supabase/supabase-js';

export async function GET(request: Request) {
  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );

  const { data, error } = await supabase
    .from('companies')
    .select('*');

  if (error) {
    return Response.json({ error: error.message }, { status: 500 });
  }

  return Response.json({ companies: data });
}
```

**責務分離**:
- Next.js API Routes: CRUD操作のみ
- FastAPI: AI/ML処理のみ
- データベース: データ永続化のみ

---

### 2. Service Layer Pattern（ビジネスロジック）

#### FastAPI Service Layer
```python
# app/services/gemini_service.py
class GeminiService:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")

    async def analyze_deal_risk(self, deal_data: dict) -> dict:
        """Deal Risk Score計算（シンプル実装）"""
        # Gemini API呼び出し
        prompt = self._build_risk_prompt(deal_data)
        response = await self.model.generate_content_async(prompt)
        result = json.loads(response.text)
        return result

    def _build_risk_prompt(self, deal_data: dict) -> str:
        """リスク分析用プロンプト生成"""
        return f"""
        以下の商談データからリスクスコアを0-100で算出してください。

        商談データ: {json.dumps(deal_data, ensure_ascii=False)}

        JSON形式で返してください:
        {{"risk_score": 0-100, "risk_factors": ["要因1", "要因2"]}}
        """
```

**2層構造**:
1. Controller（FastAPI Router）: リクエスト/レスポンス処理
2. Service（GeminiService）: ビジネスロジック

---

### 3. 将来の最適化: キャッシュ戦略（2025年11月以降）

**プロトタイプ実装期間**: キャッシュ実装はスキップし、シンプルな直接API呼び出しを使用

**2025年11月以降の最適化計画**:
- Redis Cache: API呼び出しの50%削減目標
- Batch Processing: 複数商談を1回のAPI呼び出しで処理（70-80%削減目標）
- Budget Alert: 予算監視システム（1,000/1,200/1,400 requests/day）

詳細は [Tech Context](techContext.md) の「2025年11月以降の最適化計画」セクションを参照。

---

### 4. Strategy Pattern（AI Agents切り替え）

#### CrewAI vs LangGraph切り替え
```python
# app/services/agent_service.py
class AgentService:
    def __init__(self, agent_type: str = "crewai"):
        self.agent_type = agent_type

    async def execute_workflow(self, deal_id: str) -> dict:
        """エージェントタイプに応じてワークフロー実行"""
        if self.agent_type == "crewai":
            return await self._execute_crewai(deal_id)
        elif self.agent_type == "langgraph":
            return await self._execute_langgraph(deal_id)
        else:
            raise ValueError(f"Unknown agent type: {self.agent_type}")

    async def _execute_crewai(self, deal_id: str) -> dict:
        """CrewAI Multi-Agent実行"""
        crew = Crew(
            agents=[self.email_worker, self.document_worker, self.crm_worker],
            tasks=[...]
        )
        return await crew.kickoff_async()

    async def _execute_langgraph(self, deal_id: str) -> dict:
        """LangGraph State Machine実行"""
        workflow = LangGraphWorkflow()
        return await workflow.execute({"deal_id": deal_id})
```

**切り替え基準**:
- **CrewAI**: タスク並列実行、シンプルなワークフロー
- **LangGraph**: 複雑な条件分岐、State管理が必要なケース

---

### 5. State Machine Pattern（LangGraph）

#### LangGraph State-based Orchestration
```python
# app/services/workflow_service.py
from langgraph.graph import StateGraph, END

class DealWorkflowState(TypedDict):
    deal_id: str
    stage: str
    risk_score: int
    next_actions: List[str]
    email_sent: bool
    crm_updated: bool

class LangGraphWorkflow:
    def __init__(self):
        self.workflow = StateGraph(DealWorkflowState)
        self._build_graph()

    def _build_graph(self):
        # ノード定義
        self.workflow.add_node("assess_risk", self._assess_risk)
        self.workflow.add_node("generate_actions", self._generate_actions)
        self.workflow.add_node("send_email", self._send_email)
        self.workflow.add_node("update_crm", self._update_crm)

        # エッジ定義（条件分岐）
        self.workflow.set_entry_point("assess_risk")
        self.workflow.add_edge("assess_risk", "generate_actions")

        # 条件分岐: リスクスコア >= 70ならメール送信
        self.workflow.add_conditional_edges(
            "generate_actions",
            self._should_send_email,
            {
                "send_email": "send_email",
                "update_crm": "update_crm"
            }
        )

        self.workflow.add_edge("send_email", "update_crm")
        self.workflow.add_edge("update_crm", END)

    def _should_send_email(self, state: DealWorkflowState) -> str:
        """条件分岐ロジック"""
        return "send_email" if state["risk_score"] >= 70 else "update_crm"
```

**State遷移**:
```
START
  ↓
assess_risk（リスク評価）
  ↓
generate_actions（アクション生成）
  ↓
[条件分岐]
  ├─ risk_score >= 70 → send_email（メール送信）
  └─ risk_score < 70  → update_crm（CRM更新）
       ↓
     update_crm（CRM更新）
       ↓
      END
```

---

## エラーハンドリングパターン

### 1. Retry with Exponential Backoff

#### Gemini API呼び出し時のリトライ
```python
# app/utils/retry.py
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def call_gemini_api(prompt: str) -> str:
    """Gemini API呼び出し（最大3回リトライ）"""
    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise
```

**リトライ戦略**:
- 最大試行回数: 3回
- 待機時間: 2秒、4秒、8秒（指数バックオフ）
- 最大待機時間: 10秒

### 2. Circuit Breaker Pattern

#### Gemini APIのCircuit Breaker
```python
# app/services/circuit_breaker.py
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    async def call(self, func, *args, **kwargs):
        """Circuit Breaker経由でAPI呼び出し"""
        if self.state == "OPEN":
            raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self.failure_count = 0
            self.state = "CLOSED"
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.error("Circuit breaker opened")
            raise
```

**状態遷移**:
- **CLOSED**: 正常動作
- **OPEN**: エラー5回以上で開放（API呼び出し停止）
- **HALF_OPEN**: 一定時間後、試験的に再開

---

## セキュリティパターン

### 1. Environment Variable Pattern

#### API Key管理
```python
# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set")
```

**禁止事項**:
- ❌ ハードコード: `GEMINI_API_KEY = "AIza..."`
- ❌ Gitコミット: `.env`ファイルをGit管理
- ✅ 環境変数: `.env.local`、Vercel/Railway環境変数

### 2. Rate Limiting Pattern

#### API呼び出し制限
```python
# app/middleware/rate_limiter.py
from fastapi import HTTPException

class RateLimiter:
    def __init__(self, max_requests: int = 15):
        self.max_requests = max_requests
        self.redis = redis.Redis.from_url(os.getenv("REDIS_URL"))

    async def check_rate_limit(self, client_id: str):
        """レート制限チェック"""
        key = f"rate_limit:{client_id}:{datetime.now().strftime('%Y%m%d')}"
        requests = self.redis.incr(key)
        self.redis.expire(key, 86400)  # 24時間

        if requests > self.max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {requests}/{self.max_requests}"
            )
```

**制限値**:
- 1日あたり: 15 requests/client
- 1時間あたり: 5 requests/client（オプション）

---

## テストパターン

### 1. Mock Pattern（Gemini API）

#### テスト時のAPI呼び出しモック
```python
# tests/test_gemini_service.py
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_analyze_deal_risk():
    """Deal Risk Score計算テスト（Gemini APIモック）"""
    mock_response = {"risk_score": 75, "risk_factors": ["長期停滞"]}

    with patch("app.services.gemini_service.genai.GenerativeModel") as mock:
        mock.return_value.generate_content_async = AsyncMock(
            return_value=MagicMock(text=json.dumps(mock_response))
        )

        service = GeminiService()
        result = await service.analyze_deal_risk({"id": "deal-123"})

        assert result["risk_score"] == 75
        assert "長期停滞" in result["risk_factors"]
```

**モック理由**:
- Gemini API無料枠を消費しない
- テスト実行速度向上（API呼び出し不要）
- 確定的なテスト（API応答のばらつきがない）

---

## パフォーマンスパターン

### 1. Lazy Loading Pattern（Next.js）

#### Dynamic Import
```typescript
// app/dashboard/page.tsx
import dynamic from 'next/dynamic';

// Rechartsを遅延ロード（初期バンドルサイズ削減）
const RevenueChart = dynamic(() => import('@/components/RevenueChart'), {
  loading: () => <p>Loading chart...</p>,
  ssr: false
});

export default function DashboardPage() {
  return (
    <div>
      <h1>Revenue Intelligence Dashboard</h1>
      <RevenueChart />
    </div>
  );
}
```

**効果**:
- 初期バンドルサイズ: 300KB → 150KB（50%削減）
- 初期ロード時間: 2.5秒 → 1.5秒

---

## 関連ドキュメント

- [Tech Context](techContext.md): 技術スタック詳細
- [API仕様](../03_API仕様.md): エンドポイント仕様
- [開発スケジュール](../04_開発スケジュール.md): Day 1-4タスク
