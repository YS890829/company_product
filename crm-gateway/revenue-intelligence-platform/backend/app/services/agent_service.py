"""
CrewAI Multi-Agent Service
3つのWorker（Email, Document, CRM）+ Multi-Agent Orchestrator実装
"""

import json
import os
from typing import Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel

# .envファイルを明示的にロード
load_dotenv()

# ========================================
# モックモード設定（Day 2 Phase 2）
# ========================================
USE_MOCK_CREWAI = os.getenv("USE_MOCK_CREWAI", "true").lower() == "true"
print(f"[DEBUG] USE_MOCK_CREWAI = {USE_MOCK_CREWAI} (from env: {os.getenv('USE_MOCK_CREWAI')})")


# ========================================
# Pydantic Models for Structured Outputs
# ========================================
class MeetingAnalysisOutput(BaseModel):
    """DocumentWorkerの出力構造"""
    summary: str
    key_points: List[str]
    action_items: List[str]
    sentiment: str


class CRMUpdateOutput(BaseModel):
    """CRMWorkerの出力構造"""
    field_updates: Dict[str, str]
    missing_info: List[str]
    data_quality_score: int


class EmailWorker:
    """
    Email Worker: フォローアップメール自動生成

    役割:
    - 商談情報から顧客向けフォローメールを生成
    - 丁寧で簡潔な日本語メール（250文字以内）
    - 次のアクションを明確に記載
    """

    def __init__(self):
        self.role = "Email Specialist"
        self.goal = "顧客へのフォローメールを生成する"
        self.backstory = "営業支援のメール作成エキスパート"

    async def generate_followup_email(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        フォローアップメール生成

        Args:
            context: 商談コンテキスト
                - deal_name: 商談名
                - last_meeting_summary: 最終ミーティング要約
                - next_action: 次のアクション

        Returns:
            dict: メール情報
                - email_subject: 件名
                - email_body: 本文
                - tone: トーン
                - word_count: 文字数
        """

        if USE_MOCK_CREWAI:
            # モックモード: テンプレートベースのメール生成
            deal_name = context.get("deal_name", "商談")
            last_meeting = context.get("last_meeting_summary", "前回のミーティング")
            next_action = context.get("next_action", "次のアクション")
            customer_name = context.get('customer_name', 'お客様')

            subject = f"{deal_name}の件について"
            body = f"""{customer_name}

いつもお世話になっております。

先日は貴重なお時間をいただき、誠にありがとうございました。
{last_meeting}

つきましては、{next_action}について、ご提案させていただきたく存じます。

ご不明点やご要望がございましたら、お気軽にお申し付けください。
何卒よろしくお願い申し上げます。

今後ともよろしくお願いいたします。"""

            return {
                "email_subject": subject,
                "email_body": body,
                "tone": "formal",
                "word_count": len(body)
            }

        else:
            # 本番モード: CrewAI実装（将来対応）
            from crewai import Agent, Task, Crew

            agent = Agent(
                role=self.role,
                goal=self.goal,
                backstory=self.backstory,
                llm="gemini/gemini-2.0-flash-exp"
            )

            # コンテキストから値を安全に取得
            deal_name = context.get('deal_name', '商談')
            last_meeting = context.get('last_meeting_summary', '前回のミーティング')
            next_action = context.get('next_action', '次のアクション')

            task = Task(
                description=f"""
                以下の商談情報から、顧客へのフォローメールを作成してください。

                商談名: {deal_name}
                最終ミーティング: {last_meeting}
                次のアクション: {next_action}

                メールは丁寧かつ簡潔に、250文字以内で作成してください。
                フォーマット:
                件名：〇〇

                本文内容
                """,
                expected_output="丁寧で簡潔なフォローメール本文（250文字以内）",
                agent=agent
            )

            crew = Crew(agents=[agent], tasks=[task])
            result = await crew.kickoff_async()
            # CrewOutput.raw で文字列を取得
            email_text = result.raw

            # メールを件名と本文に分割
            lines = email_text.split('\n')
            subject = ""
            body_lines = []

            for i, line in enumerate(lines):
                if line.startswith("件名：") or line.startswith("件名:"):
                    subject = line.replace("件名：", "").replace("件名:", "").strip()
                elif i > 0 and subject:  # 件名の後の行から本文開始
                    body_lines.append(line)

            # 件名が見つからない場合は最初の行を件名とする
            if not subject and lines:
                subject = lines[0].strip()
                body_lines = lines[1:]

            body = '\n'.join(body_lines).strip()

            return {
                "email_subject": subject,
                "email_body": body,
                "tone": "formal",
                "word_count": len(body)
            }


class DocumentWorker:
    """
    Document Worker: ミーティング議事録分析

    役割:
    - ミーティング文字起こしから要約を抽出
    - 重要ポイント3つを特定
    - アクションアイテム抽出
    - 顧客感情分析（positive/neutral/negative）
    """

    def __init__(self):
        self.role = "Document Analyst"
        self.goal = "ミーティング議事録や提案書を分析する"
        self.backstory = "ドキュメント分析のスペシャリスト"

    async def summarize_meeting(self, transcript: str) -> Dict[str, Any]:
        """
        ミーティング要約生成

        Args:
            transcript: ミーティング文字起こし

        Returns:
            dict: 要約結果
                - summary: 要約（100文字以内）
                - key_points: 重要ポイント3つ
                - action_items: アクションアイテムリスト
                - sentiment: 顧客の感情（positive/neutral/negative）
        """

        if USE_MOCK_CREWAI:
            # モックモード: シンプルな分析ロジック
            # 文字起こしの長さに基づいて感情を推定
            sentiment = "positive"
            if "課題" in transcript or "問題" in transcript:
                sentiment = "neutral"
            if "不満" in transcript or "懸念" in transcript:
                sentiment = "negative"

            # キーワード抽出（簡易版）
            key_points = []
            if "要件" in transcript or "システム" in transcript:
                key_points.append("システム要件についてヒアリング実施")
            if "料金" in transcript or "価格" in transcript or "費用" in transcript:
                key_points.append("料金プランについて議論")
            if "導入" in transcript or "スケジュール" in transcript:
                key_points.append("導入スケジュールについて確認")

            # デフォルトポイント
            if len(key_points) == 0:
                key_points = [
                    "顧客の現状課題をヒアリング",
                    "ソリューション提案内容を説明",
                    "次回ミーティング日程を調整"
                ]

            # アクションアイテム抽出
            action_items = []
            if "提案" in transcript:
                action_items.append("料金プラン3パターン提案資料作成")
            if "デモ" in transcript:
                action_items.append("デモ環境準備")
            if len(action_items) == 0:
                action_items.append("次回ミーティング日程調整")

            return {
                "summary": transcript[:100] + ("..." if len(transcript) > 100 else ""),
                "key_points": key_points[:3],
                "action_items": action_items,
                "sentiment": sentiment
            }

        else:
            # 本番モード: CrewAI実装（将来対応）
            from crewai import Agent, Task, Crew

            agent = Agent(
                role=self.role,
                goal=self.goal,
                backstory=self.backstory,
                llm="gemini/gemini-2.0-flash-exp"
            )

            task = Task(
                description=f"""
                以下のミーティング文字起こしを分析してください。

                文字起こし:
                {transcript}

                以下の形式で返してください:
                - summary: 要約（100文字以内）
                - key_points: 重要ポイント3つ（リスト形式）
                - action_items: アクションアイテム（リスト形式）
                - sentiment: 顧客の感情（positive/neutral/negative のいずれか）
                """,
                expected_output="ミーティング分析結果（summary, key_points, action_items, sentiment）",
                output_json=MeetingAnalysisOutput,
                agent=agent
            )

            crew = Crew(agents=[agent], tasks=[task])
            result = await crew.kickoff_async()
            # CrewOutput.json_dict でdict形式を取得
            return result.json_dict


class CRMWorker:
    """
    CRM Worker: CRMデータ品質スコアリング

    役割:
    - CRMデータから更新すべきフィールドを提案
    - 不足している情報を特定
    - データ品質スコア算出（0-100）
    """

    def __init__(self):
        self.role = "CRM Data Specialist"
        self.goal = "CRMデータを更新・最適化する"
        self.backstory = "CRM運用のエキスパート"

    async def suggest_crm_updates(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        CRM更新提案

        Args:
            deal_data: 商談データ
                - deal_name: 商談名
                - stage: ステージ
                - amount: 金額
                - last_contact: 最終接触日

        Returns:
            dict: CRM更新提案
                - field_updates: 更新すべきフィールドと値
                - missing_info: 不足している情報
                - data_quality_score: データ品質スコア（0-100）
        """

        if USE_MOCK_CREWAI:
            # モックモード: ルールベースのスコアリング
            quality_score = 100
            field_updates = {}
            missing_info = []

            # 必須フィールドチェック
            required_fields = ["deal_name", "stage", "amount", "last_contact"]
            for field in required_fields:
                if field not in deal_data or not deal_data[field]:
                    missing_info.append(field)
                    quality_score -= 20

            # last_contact が古い場合
            if "last_contact" in deal_data:
                try:
                    from datetime import datetime, timedelta
                    last_contact = datetime.fromisoformat(deal_data["last_contact"].replace("Z", "+00:00"))
                    days_since_contact = (datetime.now() - last_contact.replace(tzinfo=None)).days

                    if days_since_contact > 7:
                        field_updates["last_contact"] = "要更新（7日以上経過）"
                        quality_score -= 10

                    if days_since_contact > 14:
                        field_updates["status"] = "要フォローアップ（14日以上連絡なし）"
                        quality_score -= 10
                except:
                    pass

            # stage が "Proposal" なのに金額未設定の場合
            if deal_data.get("stage") == "Proposal" and not deal_data.get("amount"):
                missing_info.append("amount（提案金額）")
                quality_score -= 15

            # 最終スコア調整（0-100の範囲）
            quality_score = max(0, min(100, quality_score))

            return {
                "field_updates": field_updates if field_updates else {"status": "全フィールド最新"},
                "missing_info": missing_info if missing_info else ["なし"],
                "data_quality_score": quality_score
            }

        else:
            # 本番モード: CrewAI実装（将来対応）
            from crewai import Agent, Task, Crew

            agent = Agent(
                role=self.role,
                goal=self.goal,
                backstory=self.backstory,
                llm="gemini/gemini-2.0-flash-exp"
            )

            task = Task(
                description=f"""
                以下の商談データから、CRMに更新すべき情報を提案してください。

                現在のCRMデータ:
                {json.dumps(deal_data, ensure_ascii=False)}

                提案内容:
                - field_updates: 更新すべきフィールドと値（辞書形式）
                - missing_info: 不足している情報（リスト形式）
                - data_quality_score: データ品質スコア（0-100の整数）
                """,
                expected_output="CRM更新提案（field_updates, missing_info, data_quality_score）",
                output_json=CRMUpdateOutput,
                agent=agent
            )

            crew = Crew(agents=[agent], tasks=[task])
            result = await crew.kickoff_async()
            # CrewOutput.json_dict でdict形式を取得
            return result.json_dict


class MultiAgentOrchestrator:
    """
    Multi-Agent Orchestrator: 3つのWorkerの協調実行

    役割:
    - EmailWorker, DocumentWorker, CRMWorker を順次実行
    - 各Workerの結果を統合
    - 商談処理ワークフロー全体を管理
    """

    def __init__(self):
        self.email_worker = EmailWorker()
        self.document_worker = DocumentWorker()
        self.crm_worker = CRMWorker()

    async def process_deal_workflow(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        商談処理ワークフロー実行（3つのWorkerを協調実行）

        Args:
            deal_data: 商談データ
                - deal_name: 商談名
                - stage: ステージ
                - amount: 金額
                - last_meeting_transcript: 最終ミーティング文字起こし
                - last_contact: 最終接触日

        Returns:
            dict: ワークフロー実行結果
                - meeting_analysis: DocumentWorkerの分析結果
                - crm_updates: CRMWorkerの更新提案
                - followup_email: EmailWorkerのメール生成結果
                - workflow_summary: ワークフロー全体の要約
        """

        # 1. Document Worker: ミーティング分析
        meeting_analysis = await self.document_worker.summarize_meeting(
            deal_data.get("last_meeting_transcript", "ミーティング記録なし")
        )

        # 2. CRM Worker: CRM更新提案
        crm_updates = await self.crm_worker.suggest_crm_updates(deal_data)

        # 3. Email Worker: フォローメール生成
        # DocumentWorkerの結果を利用してメール生成
        followup_email = await self.email_worker.generate_followup_email({
            "deal_name": deal_data.get("deal_name", "商談"),
            "customer_name": deal_data.get("customer_name", "お客様"),
            "last_meeting_summary": meeting_analysis.get("summary", "前回ミーティング"),
            "next_action": meeting_analysis.get("action_items", ["次回打ち合わせ"])[0] if meeting_analysis.get("action_items") else "次回打ち合わせ"
        })

        # ワークフロー全体の要約
        workflow_summary = {
            "total_workers_executed": 3,
            "execution_order": ["DocumentWorker", "CRMWorker", "EmailWorker"],
            "data_quality_score": crm_updates.get("data_quality_score", 0),
            "sentiment": meeting_analysis.get("sentiment", "neutral"),
            "action_items_count": len(meeting_analysis.get("action_items", [])),
            "timestamp": datetime.now().isoformat()
        }

        return {
            "meeting_analysis": meeting_analysis,
            "crm_updates": crm_updates,
            "followup_email": followup_email,
            "workflow_summary": workflow_summary
        }
