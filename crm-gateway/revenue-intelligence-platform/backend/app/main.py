"""
Revenue Intelligence Platform - FastAPI Microservice
AI/ML専用マイクロサービス（Gemini API統合）
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import logging
from supabase import create_client

# 環境変数読み込み
load_dotenv()

# FastAPIアプリケーション作成
app = FastAPI(
    title="Revenue Intelligence API",
    description="AI/ML専用マイクロサービス（Gemini API統合）",
    version="1.0.0"
)

# CORS設定（Next.jsからのリクエストを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js開発環境
        "https://*.vercel.app",   # Vercel本番環境
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
# from app.routers import health, revenue_intelligence, suggestions, agents, workflow
# app.include_router(health.router)
# app.include_router(revenue_intelligence.router)
# app.include_router(suggestions.router)
# app.include_router(agents.router)
# app.include_router(workflow.router)

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Revenue Intelligence Platform API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "healthy",
        "service": "fastapi-microservice",
        "gemini_api_configured": bool(os.getenv("GEMINI_API_KEY")),
        "redis_url_configured": bool(os.getenv("REDIS_URL"))
    }

@app.get("/test-gemini")
async def test_gemini():
    """Gemini API接続テスト"""
    from app.services.gemini_service import GeminiService

    try:
        gemini = GeminiService()
        connection_ok = gemini.test_connection()

        return {
            "status": "success" if connection_ok else "failed",
            "message": "Gemini API connection test completed",
            "connection_ok": connection_ok
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "connection_ok": False
        }

@app.post("/api/analyze-deal-risk")
async def analyze_deal_risk_endpoint(deal_data: dict):
    """商談リスク分析エンドポイント"""
    from app.services.gemini_service import GeminiService

    try:
        gemini = GeminiService()
        result = await gemini.analyze_deal_risk(deal_data)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/analyze-win-rate")
async def analyze_win_rate_endpoint(request: dict):
    """成約率分析エンドポイント"""
    from app.services.gemini_service import GeminiService

    try:
        gemini = GeminiService()
        deals = request.get("deals", [])
        result = await gemini.analyze_win_rate(deals)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/generate-next-actions")
async def generate_next_actions_endpoint(deal_data: dict):
    """次のアクション提案エンドポイント"""
    from app.services.gemini_service import GeminiService

    try:
        gemini = GeminiService()
        result = await gemini.generate_next_actions(deal_data)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/forecast-revenue")
async def forecast_revenue_endpoint(request: dict):
    """売上予測エンドポイント"""
    from app.services.gemini_service import GeminiService
    try:
        gemini = GeminiService()
        deals = request.get("deals", [])
        result = await gemini.forecast_revenue(deals)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/predict-churn-risk")
async def predict_churn_risk_endpoint(customer_data: dict):
    """チャーンリスク予測エンドポイント"""
    from app.services.gemini_service import GeminiService
    try:
        gemini = GeminiService()
        result = await gemini.predict_churn_risk(customer_data)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/detect-upsell-opportunities")
async def detect_upsell_opportunities_endpoint(customer_data: dict):
    """アップセル機会検知エンドポイント"""
    from app.services.gemini_service import GeminiService
    try:
        gemini = GeminiService()
        result = await gemini.detect_upsell_opportunities(customer_data)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/analyze-competitors")
async def analyze_competitors_endpoint(request: dict):
    """競合分析エンドポイント"""
    from app.services.gemini_service import GeminiService
    from supabase import create_client
    try:
        gemini = GeminiService()
        # company_idが指定されている場合はSupabaseから商談データを取得
        if "company_id" in request:
            supabase = create_client(
                os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
                os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            )
            deals_response = supabase.table("deals").select("*").eq("company_id", request["company_id"]).execute()
            deals = deals_response.data if deals_response.data else []
        else:
            deals = request.get("deals", [])
        result = await gemini.analyze_competitors(deals)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/analyze-sales-performance")
async def analyze_sales_performance_endpoint(request: dict):
    """営業パフォーマンス分析エンドポイント"""
    from app.services.gemini_service import GeminiService

    logger = logging.getLogger(__name__)

    try:
        gemini = GeminiService()
        # company_idが指定されている場合はSupabaseから営業担当者データを取得
        if "company_id" in request:
            company_id = request["company_id"]
            logger.info(f"[Sales Performance] Analyzing for company_id: {company_id}")

            supabase = create_client(
                os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
                os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            )

            # dealsテーブルから会社IDでフィルタリングしたデータを取得
            logger.info(f"[Sales Performance] Querying deals table for company: {company_id}")
            deals_response = supabase.table("deals").select("owner_name, stage").eq("company_id", company_id).execute()
            deals_data = deals_response.data if deals_response.data else []
            logger.info(f"[Sales Performance] Found {len(deals_data)} deals")

            # 営業担当者別にデータを集計
            from collections import defaultdict
            rep_stats = defaultdict(lambda: {"total_deals": 0, "won_deals": 0})

            for deal in deals_data:
                owner_name = deal.get("owner_name")
                stage = deal.get("stage", "")

                if owner_name:
                    rep_stats[owner_name]["total_deals"] += 1
                    # 成約条件: "Closed Won", "成約", "内定" のいずれか (大文字小文字区別なし)
                    if stage.lower() in ["closed won", "成約", "内定"]:
                        rep_stats[owner_name]["won_deals"] += 1

            # リスト形式に変換
            reps = [
                {
                    "name": name,
                    "total_deals": stats["total_deals"],
                    "won_deals": stats["won_deals"]
                }
                for name, stats in rep_stats.items()
            ]

            logger.info(f"[Sales Performance] Aggregated {len(reps)} salespersons")

            # データが空の場合はエラーを返す
            if not reps:
                return {"status": "error", "message": "指定された会社の営業担当者データが見つかりません"}
        else:
            reps = request.get("reps", [])

        result = await gemini.analyze_sales_performance(reps)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"[Sales Performance] Error: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}

@app.post("/api/summarize-meetings")
async def summarize_meetings_endpoint(request: dict):
    """ミーティング要約エンドポイント"""
    from app.services.gemini_service import GeminiService

    logger = logging.getLogger(__name__)
    try:
        gemini = GeminiService()
        # deal_idが指定されている場合はSupabaseからミーティングデータを取得
        if "deal_id" in request:
            supabase = create_client(
                os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
                os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            )
            meetings_response = supabase.table("meetings").select("*").eq("deal_id", request["deal_id"]).limit(5).execute()
            meetings = meetings_response.data if meetings_response.data else []
            logger.info(f"[Meeting Summary] Found {len(meetings)} meetings for deal_id: {request['deal_id']}")
        else:
            meetings = request.get("meetings", [])
            logger.info(f"[Meeting Summary] Using {len(meetings)} meetings from request")

        result = await gemini.summarize_meetings(meetings)
        logger.info(f"[Meeting Summary] Result structure: {list(result.keys())}")
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"[Meeting Summary] Error: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}

@app.post("/api/track-deal-progress")
async def track_deal_progress_endpoint(request: dict):
    """商談進捗トラッキングエンドポイント"""
    from app.services.gemini_service import GeminiService

    logger = logging.getLogger(__name__)
    try:
        gemini = GeminiService()
        # deal_idが指定されている場合はSupabaseからデータを取得
        if "deal_id" in request:
            supabase = create_client(
                os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
                os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            )
            deal_response = supabase.table("deals").select("*").eq("id", request["deal_id"]).execute()
            # responseが複数件返る可能性があるので、最初の要素を取得
            deal_data = deal_response.data[0] if deal_response.data and len(deal_response.data) > 0 else {}
            deal_id = request["deal_id"]
            logger.info(f"[Deal Progress] Found deal: {deal_data.get('customer_name', 'N/A')} - Stage: {deal_data.get('stage', 'N/A')}")
        else:
            deal_id = request.get("deal_id", "")
            deal_data = request.get("deal_data", {})
            logger.info(f"[Deal Progress] Using deal_data from request")

        result = await gemini.track_deal_progress(deal_id, deal_data)
        logger.info(f"[Deal Progress] Result: {result}")
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"[Deal Progress] Error: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}

# ========================================
# Day 2 Phase 1: Suggestion Engine (3エンドポイント)
# ========================================

@app.post("/api/suggest-next-best-action")
async def suggest_next_best_action_endpoint(deal_data: dict):
    """Next Best Action提案エンドポイント（優先度付き3つのアクション）"""
    from app.services.gemini_service import GeminiService
    try:
        gemini = GeminiService()
        result = await gemini.suggest_next_best_action(deal_data)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/detect-risk-alerts")
async def detect_risk_alerts_endpoint(request: dict):
    """Risk Detection（高リスク商談の自動検出＋アラート生成）"""
    from app.services.gemini_service import GeminiService
    try:
        gemini = GeminiService()
        deals_input = request.get("deals", [])

        # deal_idからSupabaseで商談情報を取得
        supabase = create_client(
            os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

        enriched_deals = []
        for deal_input in deals_input:
            deal_id = deal_input.get("deal_id")
            risk_score = deal_input.get("risk_score", 50)

            # Supabaseから商談情報を取得
            deal_response = supabase.table("deals").select("*").eq("id", deal_id).execute()

            if deal_response.data and len(deal_response.data) > 0:
                deal_data = deal_response.data[0]
                enriched_deals.append({
                    "id": deal_id,
                    "deal_name": deal_data.get("customer_name", "Unknown"),
                    "stage": deal_data.get("stage", "prospect"),
                    "amount": deal_data.get("amount", 0),
                    "risk_score": risk_score,
                    "last_contact_days": 0  # TODO: 計算ロジック追加
                })
            else:
                # データが見つからない場合はデフォルト値
                enriched_deals.append({
                    "id": deal_id,
                    "deal_name": "Unknown",
                    "stage": "prospect",
                    "amount": 0,
                    "risk_score": risk_score,
                    "last_contact_days": 0
                })

        result = await gemini.detect_risk_alerts(enriched_deals)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"[Risk Detection] Error: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}

@app.post("/api/generate-proposal-draft")
async def generate_proposal_draft_endpoint(proposal_data: dict):
    """Proposal Draft Generation（提案書ドラフト自動生成）"""
    from app.services.gemini_service import GeminiService
    try:
        gemini = GeminiService()
        result = await gemini.generate_proposal_draft(proposal_data)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ========================================
# Day 2 Phase 2: CrewAI Multi-Agent (4エンドポイント)
# ========================================

@app.post("/api/agents/email")
async def email_worker_endpoint(request: dict):
    """Email Worker: フォローアップメール自動生成"""
    from app.services.agent_service import EmailWorker
    try:
        worker = EmailWorker()
        context = request.get("context", {})
        result = await worker.generate_followup_email(context)
        return {"status": "success", "data": {"email": result}}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/agents/document")
async def document_worker_endpoint(request: dict):
    """Document Worker: ミーティング議事録分析"""
    from app.services.agent_service import DocumentWorker
    try:
        worker = DocumentWorker()
        transcript = request.get("transcript", "")
        result = await worker.summarize_meeting(transcript)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/agents/crm")
async def crm_worker_endpoint(request: dict):
    """CRM Worker: CRMデータ品質スコアリング"""
    from app.services.agent_service import CRMWorker
    try:
        worker = CRMWorker()
        deal_data = request.get("deal_data", {})
        result = await worker.suggest_crm_updates(deal_data)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/agents/workflow")
async def multi_agent_workflow_endpoint(request: dict):
    """Multi-Agent Orchestrator: 3つのWorkerの協調実行"""
    from app.services.agent_service import MultiAgentOrchestrator

    try:
        # deal_idを取得
        deal_id = request.get("deal_id")
        if not deal_id:
            return {"status": "error", "message": "deal_id is required"}

        # Supabaseから商談データとミーティングデータを取得
        supabase = create_client(
            os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

        # 商談データ取得
        deal_response = supabase.table("deals").select("*").eq("id", deal_id).single().execute()
        if not deal_response.data:
            return {"status": "error", "message": f"Deal not found: {deal_id}"}

        deal = deal_response.data

        # ミーティングデータ取得（最新のtranscriptを取得）
        meetings_response = supabase.table("meetings").select("transcript").eq("deal_id", deal_id).order("date", desc=True).limit(1).execute()

        last_meeting_transcript = ""
        if meetings_response.data and len(meetings_response.data) > 0:
            last_meeting_transcript = meetings_response.data[0].get("transcript", "")

        # deal_dataを構築
        deal_data = {
            "deal_name": f"{deal.get('customer_name', '商談')} - {deal.get('stage', '')}",
            "customer_name": deal.get("customer_name", "お客様"),
            "stage": deal.get("stage", ""),
            "amount": float(deal.get("amount", 0)),
            "last_meeting_transcript": last_meeting_transcript,
            "last_contact": deal.get("updated_at", ""),
        }

        # Multi-Agent Workflow実行
        orchestrator = MultiAgentOrchestrator()
        result = await orchestrator.process_deal_workflow(deal_data)
        return {"status": "success", "data": result}
    except Exception as e:
        import traceback
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}


# ============================================
# Day 2 Phase 3: LangGraph Workflow (1 endpoint)
# ============================================

@app.post("/api/workflow/execute")
async def execute_langgraph_workflow(request: dict):
    """
    LangGraph Workflow実行

    商談ワークフローを実行し、状態遷移を管理します。

    Request Body:
        {
            "deal_id": "deal-123",
            "stage": "proposal"  # prospect, qualification, proposal, negotiation, closed
        }

    Response:
        {
            "status": "success",
            "data": {
                "deal_id": "deal-123",
                "deal_name": "顧客企業1 - proposal",
                "stage": "proposal",
                "risk_score": 75,
                "next_actions": ["アクション1", "アクション2", "アクション3"],
                "email_sent": true,
                "crm_updated": true,
                "workflow_steps": ["assess_risk", "generate_actions", "send_email", "update_crm"],
                "execution_time": 2.3
            }
        }

    ワークフローフロー:
        1. assess_risk: リスク評価
        2. generate_actions: 次のアクション生成
        3. 条件分岐:
           - risk_score >= 70: send_email → update_crm
           - risk_score < 70: update_crm
        4. END
    """
    from app.services.workflow_service import LangGraphWorkflow, create_initial_state

    logger = logging.getLogger(__name__)

    try:
        # リクエストパラメータ取得
        deal_id = request.get("deal_id", "unknown-deal")
        stage = request.get("stage", "prospect")

        # Supabaseから商談データを取得してdeal_nameを取得
        supabase = create_client(
            os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

        deal_name = None
        try:
            deal_response = supabase.table("deals").select("customer_name, stage").eq("id", deal_id).execute()
            if deal_response.data and len(deal_response.data) > 0:
                deal_data = deal_response.data[0]
                customer_name = deal_data.get("customer_name", "Unknown")
                deal_stage = deal_data.get("stage", stage)
                deal_name = f"{customer_name} - {deal_stage}"
                logger.info(f"[LangGraph Workflow] Fetched deal_name: {deal_name}")
        except Exception as e:
            logger.warning(f"[LangGraph Workflow] Failed to fetch deal_name from Supabase: {str(e)}")

        # 初期状態作成（deal_nameを含める）
        initial_state = create_initial_state(deal_id=deal_id, stage=stage, deal_name=deal_name)

        # ワークフロー実行
        workflow = LangGraphWorkflow()
        final_state = await workflow.execute(initial_state)

        return {
            "status": "success",
            "data": final_state
        }
    except Exception as e:
        import traceback
        logger.error(f"[LangGraph Workflow] Error: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
