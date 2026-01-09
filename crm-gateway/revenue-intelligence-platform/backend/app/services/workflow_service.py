"""
LangGraph Workflow Service

商談ワークフローの状態管理を行うLangGraphサービス。
リスクスコアに基づいた条件分岐を実装。

実装機能:
1. DealWorkflowState: ワークフロー状態の型定義
2. LangGraphWorkflow: LangGraph StateGraph実装
3. 4つのノード: assess_risk, generate_actions, send_email, update_crm
4. 条件分岐: risk_score >= 70 でメール送信フロー実行
"""

import os
import json
from typing import TypedDict, List, Annotated, Optional, NotRequired
from datetime import datetime
from dotenv import load_dotenv

# .envファイルを明示的にロード
load_dotenv()

# ============================================
# モックモード設定
# ============================================
USE_MOCK_LANGGRAPH = os.getenv("USE_MOCK_LANGGRAPH", "false").lower() == "true"
print(f"[DEBUG] USE_MOCK_LANGGRAPH = {USE_MOCK_LANGGRAPH} (from env: {os.getenv('USE_MOCK_LANGGRAPH')})")


# ============================================
# 状態定義（TypedDict）
# ============================================

class DealWorkflowState(TypedDict):
    """
    商談ワークフローの状態を管理する型定義

    属性:
        deal_id: 商談ID
        deal_name: 商談名（オプショナル）
        stage: 商談ステージ（prospect, qualification, proposal, negotiation, closed）
        risk_score: リスクスコア（0-100）
        next_actions: 次のアクション提案リスト
        email_sent: メール送信フラグ
        crm_updated: CRM更新フラグ
        workflow_steps: 実行されたステップの履歴
        execution_time: ワークフロー実行時間（秒）
    """
    deal_id: str
    deal_name: NotRequired[str]  # オプショナルフィールド（Python 3.11+）
    stage: str
    risk_score: int
    next_actions: List[str]
    email_sent: bool
    crm_updated: bool
    workflow_steps: List[str]
    execution_time: float


# ============================================
# LangGraph Workflow Service
# ============================================

class LangGraphWorkflow:
    """
    LangGraphを使用した商談ワークフローサービス

    ワークフローの流れ:
    1. assess_risk: リスク評価
    2. generate_actions: アクション生成
    3. 条件分岐:
       - risk_score >= 70: send_email → update_crm
       - risk_score < 70: update_crm
    4. END

    モックモード:
        環境変数 USE_MOCK_LANGGRAPH=true でモックモード実行
        Gemini APIを使わず、ルールベースで動作
    """

    def __init__(self):
        """
        LangGraphWorkflow初期化

        環境変数:
            USE_MOCK_LANGGRAPH: モックモードフラグ（true/false）
        """
        self.use_mock = os.getenv("USE_MOCK_LANGGRAPH", "true").lower() == "true"
        self.start_time = None

        if not self.use_mock:
            # 本番モード: LangGraph実装（Day 4で統合予定）
            try:
                from langgraph.graph import StateGraph, END
                self.workflow = StateGraph(DealWorkflowState)
                self._build_graph()
            except ImportError:
                print("Warning: langgraph not installed. Falling back to mock mode.")
                self.use_mock = True

    def _build_graph(self):
        """
        LangGraph StateGraph構築

        ノード:
            - assess_risk: リスク評価
            - generate_actions: アクション生成
            - send_email: メール送信
            - update_crm: CRM更新

        エッジ:
            - assess_risk → generate_actions
            - generate_actions → [条件分岐]
            - send_email → update_crm
            - update_crm → END
        """
        from langgraph.graph import END

        # ノード追加
        self.workflow.add_node("assess_risk", self._assess_risk)
        self.workflow.add_node("generate_actions", self._generate_actions)
        self.workflow.add_node("send_email", self._send_email)
        self.workflow.add_node("update_crm", self._update_crm)

        # エントリーポイント設定
        self.workflow.set_entry_point("assess_risk")

        # 固定エッジ
        self.workflow.add_edge("assess_risk", "generate_actions")

        # 条件分岐エッジ
        self.workflow.add_conditional_edges(
            "generate_actions",
            self._should_send_email,
            {
                "send_email": "send_email",
                "update_crm": "update_crm"
            }
        )

        # 終了エッジ
        self.workflow.add_edge("send_email", "update_crm")
        self.workflow.add_edge("update_crm", END)

    # ============================================
    # ノード実装（4つ）
    # ============================================

    async def _assess_risk(self, state: DealWorkflowState) -> DealWorkflowState:
        """
        ノード1: リスク評価

        処理内容:
            - 商談データからリスクスコアを算出
            - モックモード: ステージとdeal_idから算出
            - 本番モード: Gemini APIでリスク分析

        Args:
            state: 現在のワークフロー状態

        Returns:
            更新された状態（risk_scoreが設定される）
        """
        # ワークフローステップを記録
        state["workflow_steps"].append("assess_risk")

        if self.use_mock:
            # モックモード: ルールベースでリスクスコア算出
            # ステージが初期段階ほどリスクが高い
            stage_risk_map = {
                "prospect": 85,
                "qualification": 70,
                "proposal": 50,
                "negotiation": 30,
                "closed won": 10,
                "closed lost": 95
            }

            base_risk = stage_risk_map.get(state["stage"].lower(), 60)

            # deal_idの長さで微調整（デモ用）
            deal_id_factor = len(state["deal_id"]) % 20 - 10

            state["risk_score"] = max(0, min(100, base_risk + deal_id_factor))

            print(f"[assess_risk] Deal {state['deal_id']}: Risk Score = {state['risk_score']}")
        else:
            # 本番モード: Gemini API呼び出し（Day 4で実装予定）
            from app.services.gemini_service import GeminiService
            gemini = GeminiService()

            risk_result = await gemini.analyze_deal_risk({
                "id": state["deal_id"],
                "deal_name": state.get("deal_name", f"Deal-{state['deal_id'][:8]}"),
                "stage": state["stage"]
            })

            state["risk_score"] = risk_result.get("risk_score", 60)

        return state

    async def _generate_actions(self, state: DealWorkflowState) -> DealWorkflowState:
        """
        ノード2: 次のアクション生成

        処理内容:
            - リスクスコアとステージから次のアクションを提案
            - モックモード: ルールベース
            - 本番モード: Gemini APIでアクション提案

        Args:
            state: 現在のワークフロー状態

        Returns:
            更新された状態（next_actionsが設定される）
        """
        # ワークフローステップを記録
        state["workflow_steps"].append("generate_actions")

        if self.use_mock:
            # モックモード: リスクスコアとステージに基づくアクション提案
            actions = []

            if state["risk_score"] >= 70:
                actions = [
                    "緊急: 決裁者との直接ミーティングを設定してください",
                    "競合状況を確認し、差別化ポイントを明確化してください",
                    "提案書を再レビューし、顧客の懸念点に対応してください"
                ]
            elif state["risk_score"] >= 50:
                actions = [
                    "次回ミーティングの日程を確定してください",
                    "ステークホルダー分析を更新してください",
                    "デモ環境を準備してください"
                ]
            else:
                actions = [
                    "定期的なフォローアップメールを送信してください",
                    "導入スケジュールを確認してください",
                    "契約書のドラフトを準備してください"
                ]

            state["next_actions"] = actions

            print(f"[generate_actions] Generated {len(actions)} actions for Risk Score {state['risk_score']}")
        else:
            # 本番モード: Gemini API呼び出し（Day 4で実装予定）
            from app.services.gemini_service import GeminiService
            gemini = GeminiService()

            actions_result = await gemini.generate_next_actions({
                "deal_id": state["deal_id"],
                "deal_name": state.get("deal_name", f"Deal-{state['deal_id'][:8]}"),
                "stage": state["stage"],
                "risk_score": state["risk_score"]
            })

            state["next_actions"] = actions_result.get("actions", [])

        return state

    async def _send_email(self, state: DealWorkflowState) -> DealWorkflowState:
        """
        ノード3: メール送信

        処理内容:
            - 高リスク商談の場合にフォローメールを送信
            - モックモード: メール送信フラグを設定
            - 本番モード: CrewAI EmailWorkerでメール生成

        Args:
            state: 現在のワークフロー状態

        Returns:
            更新された状態（email_sentがTrueになる）
        """
        # ワークフローステップを記録
        state["workflow_steps"].append("send_email")

        if self.use_mock:
            # モックモード: メール送信フラグを設定
            state["email_sent"] = True

            print(f"[send_email] High-risk deal detected (Risk Score: {state['risk_score']}). Email sent to stakeholders.")
        else:
            # 本番モード: CrewAI EmailWorker呼び出し
            from app.services.agent_service import EmailWorker

            email_worker = EmailWorker()

            # コンテキストを構築（deal_nameがあれば含める）
            email_context = {
                "deal_id": state["deal_id"],
                "risk_score": state["risk_score"],
                "last_meeting_summary": f"リスクスコア{state['risk_score']}の商談です。",
                "next_action": state["next_actions"][0] if state["next_actions"] else "フォローアップを実施してください"
            }

            # deal_nameが存在する場合のみ追加
            if "deal_name" in state:
                email_context["deal_name"] = state["deal_name"]

            email_result = await email_worker.generate_followup_email(email_context)

            state["email_sent"] = True
            # email_resultはメール本文（実際には送信しない、CRMに記録のみ）

        return state

    async def _update_crm(self, state: DealWorkflowState) -> DealWorkflowState:
        """
        ノード4: CRM更新

        処理内容:
            - 商談情報をCRMに更新
            - リスクスコア、次のアクション、メール送信状況を記録
            - モックモード: 更新フラグを設定
            - 本番モード: Supabaseに実際に更新

        Args:
            state: 現在のワークフロー状態

        Returns:
            更新された状態（crm_updatedがTrueになる）
        """
        # ワークフローステップを記録
        state["workflow_steps"].append("update_crm")

        if self.use_mock:
            # モックモード: CRM更新フラグを設定
            state["crm_updated"] = True

            print(f"[update_crm] CRM updated for Deal {state['deal_id']}")
            print(f"  - Risk Score: {state['risk_score']}")
            print(f"  - Next Actions: {len(state['next_actions'])} items")
            print(f"  - Email Sent: {state['email_sent']}")
        else:
            # 本番モード: Supabase CRM更新（Day 4で実装予定）
            # SupabaseクライアントでCRM更新
            # await supabase.from('deals').update({
            #     'risk_score': state['risk_score'],
            #     'next_actions': state['next_actions'],
            #     'last_updated': datetime.now()
            # }).eq('id', state['deal_id']).execute()

            state["crm_updated"] = True

        return state

    # ============================================
    # 条件分岐ロジック
    # ============================================

    def _should_send_email(self, state: DealWorkflowState) -> str:
        """
        条件分岐: メール送信判定

        判定基準:
            - risk_score >= 70: メール送信フローへ
            - risk_score < 70: CRM更新のみ

        Args:
            state: 現在のワークフロー状態

        Returns:
            次のノード名（"send_email" または "update_crm"）
        """
        if state["risk_score"] >= 70:
            print(f"[condition] High risk detected ({state['risk_score']}). Triggering email workflow.")
            return "send_email"
        else:
            print(f"[condition] Normal risk ({state['risk_score']}). Skipping email, updating CRM only.")
            return "update_crm"

    # ============================================
    # ワークフロー実行
    # ============================================

    async def execute(self, initial_state: DealWorkflowState) -> DealWorkflowState:
        """
        ワークフロー実行

        処理フロー:
            1. assess_risk: リスク評価
            2. generate_actions: アクション生成
            3. 条件分岐:
               - risk_score >= 70: send_email → update_crm
               - risk_score < 70: update_crm
            4. END

        Args:
            initial_state: 初期状態（deal_id, stageが必須）

        Returns:
            最終状態（全フィールドが設定される）
        """
        self.start_time = datetime.now()

        print(f"\n{'='*60}")
        print(f"[LangGraph Workflow] Starting workflow for Deal: {initial_state['deal_id']}")
        print(f"[LangGraph Workflow] Stage: {initial_state['stage']}")
        print(f"{'='*60}\n")

        if self.use_mock:
            # モックモード: 各ノードを順番に実行
            state = initial_state.copy()

            # ステップ1: assess_risk
            state = await self._assess_risk(state)

            # ステップ2: generate_actions
            state = await self._generate_actions(state)

            # ステップ3: 条件分岐
            next_node = self._should_send_email(state)

            if next_node == "send_email":
                # 高リスク: メール送信 → CRM更新
                state = await self._send_email(state)
                state = await self._update_crm(state)
            else:
                # 通常リスク: CRM更新のみ
                state = await self._update_crm(state)

            # 実行時間を計算
            execution_time = (datetime.now() - self.start_time).total_seconds()
            state["execution_time"] = round(execution_time, 2)

            print(f"\n{'='*60}")
            print(f"[LangGraph Workflow] Completed in {state['execution_time']}s")
            print(f"[LangGraph Workflow] Steps executed: {' → '.join(state['workflow_steps'])}")
            print(f"{'='*60}\n")

            return state
        else:
            # 本番モード: LangGraph実行
            app = self.workflow.compile()
            final_state = await app.ainvoke(initial_state)

            # 実行時間を計算
            execution_time = (datetime.now() - self.start_time).total_seconds()
            final_state["execution_time"] = round(execution_time, 2)

            return final_state


# ============================================
# ユーティリティ関数
# ============================================

def create_initial_state(deal_id: str, stage: str, deal_name: str = None) -> DealWorkflowState:
    """
    初期状態を作成

    Args:
        deal_id: 商談ID
        stage: 商談ステージ
        deal_name: 商談名（オプショナル）

    Returns:
        初期化されたDealWorkflowState
    """
    # 必須フィールドのみで初期化
    state: DealWorkflowState = {
        "deal_id": deal_id,
        "stage": stage,
        "risk_score": 0,
        "next_actions": [],
        "email_sent": False,
        "crm_updated": False,
        "workflow_steps": [],
        "execution_time": 0.0
    }

    # deal_nameが提供されている場合のみ追加
    if deal_name is not None:
        state["deal_name"] = deal_name

    return state
