"""
Gemini API Service
Google Gemini を使用したAI処理サービス
シンプル実装版（プロトタイプ期間）
"""

import os
import json
import logging
from typing import Dict, Any, Optional
import google.generativeai as genai

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiService:
    """Gemini API を使用したAI処理サービス（シンプル実装版）"""

    def __init__(self, use_mock: bool = None):
        """
        初期化: Gemini APIの設定

        Args:
            use_mock: Trueの場合モックデータを返す。Noneの場合は環境変数USE_MOCK_GEMINIで判定
        """
        api_key = os.getenv("GEMINI_API_KEY")

        # モード判定: 環境変数または引数で決定
        if use_mock is None:
            self.use_mock = os.getenv("USE_MOCK_GEMINI", "true").lower() == "true"
        else:
            self.use_mock = use_mock

        if self.use_mock:
            logger.warning("⚠️ GeminiService initialized in MOCK MODE (using dummy data)")
            self.model_name = "mock-model"
        else:
            if not api_key:
                raise ValueError("GEMINI_API_KEY is not set in environment variables")

            genai.configure(api_key=api_key)
            self.model_name = "models/text-bison-001"  # 古いSDK (0.1.0rc1) 対応モデル（フルパス指定）
            logger.info(f"GeminiService initialized with {self.model_name} model (using generate_text API)")

    def _extract_json_from_response(self, text: str) -> str:
        """Extract JSON from Gemini response, handling markdown code blocks"""
        text = text.strip()
        if text.startswith("```json"):
            text = text.split("```json")[1].split("```")[0].strip()
        elif text.startswith("```"):
            text = text.split("```")[1].split("```")[0].strip()
        return text

    def test_connection(self) -> bool:
        """Gemini API接続テスト"""
        if self.use_mock:
            logger.info("MOCK MODE: Connection test skipped")
            return True

        try:
            response = genai.generate_text(
                model=self.model_name,
                prompt="Hello, can you respond with 'OK'?"
            )
            logger.info("Gemini API connection successful")
            return True
        except Exception as e:
            logger.error(f"Gemini API connection failed: {e}")
            return False

    async def analyze_deal_risk(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        商談リスクスコアを計算

        Args:
            deal_data: 商談データ（stage, amount, last_updated等）

        Returns:
            {"risk_score": 0-100, "risk_factors": ["要因1", "要因2"]}
        """
        if self.use_mock:
            # モックモード: ステージに応じたリアルなリスクスコアを返す
            stage = deal_data.get('stage', 'prospect').lower()
            stage_risk_map = {
                'prospect': (70, 'high', ['初期段階で進捗不明', '顧客エンゲージメント低い']),
                'meeting': (55, 'medium', ['ヒアリング不十分', '予算確認必要']),
                'proposal': (40, 'medium', ['提案書送付後のフォロー必要', '競合状況不明']),
                'negotiation': (25, 'low', ['価格交渉中', '契約書確認中']),
                'closed won': (0, 'low', []),
                'closed lost': (100, 'high', ['失注確定'])
            }

            risk_score, risk_level, risk_factors = stage_risk_map.get(stage, (50, 'medium', ['ステージ不明']))

            result = {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "risk_factors": risk_factors
            }

            logger.info(f"[MOCK] Deal risk analyzed: {deal_data.get('deal_name')} -> Risk Score: {result['risk_score']}")
            return result

        # 実際のGemini API呼び出し
        try:
            prompt = f"""
以下の商談データからリスクスコアを0-100で算出してください。
スコアが高いほど失注リスクが高いことを意味します。

商談データ:
- 商談名: {deal_data.get('deal_name', 'N/A')}
- ステージ: {deal_data.get('stage', 'N/A')}
- 金額: ¥{deal_data.get('amount', 0):,}
- 最終更新: {deal_data.get('last_updated', 'N/A')}
- 確度: {deal_data.get('probability', 0) * 100}%

リスク要因を分析し、JSON形式で返してください:
{{
  "risk_score": 0-100の整数,
  "risk_level": "low" | "medium" | "high",
  "risk_factors": ["要因1", "要因2", "要因3"]
}}
"""

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=500,
                )
            )

            # Extract JSON from markdown code blocks if present
            text = self._extract_json_from_response(response.text)
            result = json.loads(text)
            logger.info(f"Deal risk analyzed: {deal_data.get('deal_name')} -> Risk Score: {result['risk_score']}")
            return result

        except Exception as e:
            logger.error(f"Error analyzing deal risk: {e}")
            return {
                "risk_score": 50,
                "risk_level": "medium",
                "risk_factors": ["分析エラー"]
            }

    async def analyze_win_rate(self, deals: list) -> Dict[str, Any]:
        """
        成約率分析（ステージ別、担当者別）

        Args:
            deals: 商談リストデータ

        Returns:
            {"overall_win_rate": 0.28, "by_stage": {...}, "by_rep": [...]}
        """
        if self.use_mock:
            # モックモード: リアルな成約率データを返す（営業時間軸順）
            result = {
                "overall_win_rate": 28.0,
                "total_deals": 360,
                "won_deals": 100,
                "lost_deals": 260,
                "by_stage": [
                    # 営業の時間軸順（開始から受注まで）
                    {"stage": "Prospect", "total": 80, "won": 10, "win_rate": 12.5, "count": 80},
                    {"stage": "Meeting", "total": 70, "won": 18, "win_rate": 25.7, "count": 70},
                    {"stage": "Qualification", "total": 60, "won": 22, "win_rate": 36.7, "count": 60},
                    {"stage": "Proposal", "total": 50, "won": 25, "win_rate": 50.0, "count": 50},
                    {"stage": "Negotiation", "total": 40, "won": 30, "win_rate": 75.0, "count": 40},
                    {"stage": "Closed Won", "total": 35, "won": 35, "win_rate": 100.0, "count": 35},
                    {"stage": "Closed Lost", "total": 25, "won": 0, "win_rate": 0.0, "count": 25}
                ],
                "by_rep": [
                    {"name": "山田太郎", "total_deals": 25, "won": 8, "win_rate": 32.0},
                    {"name": "佐藤花子", "total_deals": 30, "won": 12, "win_rate": 40.0},
                    {"name": "鈴木一郎", "total_deals": 20, "won": 5, "win_rate": 25.0}
                ]
            }

            logger.info(f"[MOCK] Win rate analyzed: Overall {result['overall_win_rate']:.2f}% (7 stages)")
            return result

        # 実際のGemini API呼び出し
        try:
            # 商談データを要約
            total_deals = len(deals)
            stages_summary = {}
            for deal in deals:
                stage = deal.get('stage', 'unknown')
                if stage not in stages_summary:
                    stages_summary[stage] = {'total': 0, 'won': 0}
                stages_summary[stage]['total'] += 1
                if stage.lower() == 'closed won':
                    stages_summary[stage]['won'] += 1

            prompt = f"""
以下の商談データから成約率を分析してください。

商談総数: {total_deals}件
ステージ別内訳: {json.dumps(stages_summary, ensure_ascii=False)}

JSON形式で返してください:
{{
  "overall_win_rate": 全体成約率（0-100の小数）,
  "total_deals": 総商談数,
  "won_deals": 成約数,
  "lost_deals": 失注数,
  "by_stage": [
    {{"stage": "ステージ名", "total": 件数, "won": 成約数, "win_rate": 成約率, "count": 件数}}
  ]
}}
"""

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=800,
                )
            )

            text = self._extract_json_from_response(response.text)
            result = json.loads(text)
            logger.info(f"Win rate analyzed: Overall {result.get('overall_win_rate', 0):.2f}%")
            return result

        except Exception as e:
            logger.error(f"Error analyzing win rate: {e}")
            return {
                "overall_win_rate": 0.0,
                "total_deals": 0,
                "won_deals": 0,
                "lost_deals": 0,
                "by_stage": []
            }

    async def generate_next_actions(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        次にすべきアクションを提案（3つ）

        Args:
            deal_data: 商談データ

        Returns:
            {"actions": [{"action": "...", "priority": "high", "rationale": "..."}]}
        """
        if self.use_mock:
            # モックモード: リアルなアクション提案を返す
            stage = deal_data.get('stage', 'prospect').lower()

            stage_actions_map = {
                'prospect': [
                    {"action": "ヒアリングミーティング設定", "priority": "high", "rationale": "顧客の課題を深掘りする"},
                    {"action": "事例紹介資料送付", "priority": "medium", "rationale": "導入事例で信頼性を高める"},
                    {"action": "決裁者へのアプローチ", "priority": "low", "rationale": "キーパーソンを特定する"}
                ],
                'meeting': [
                    {"action": "提案書ドラフト作成", "priority": "high", "rationale": "次回ミーティングで提示"},
                    {"action": "予算確認のフォローメール", "priority": "high", "rationale": "商談進行の確度を高める"},
                    {"action": "競合比較表作成", "priority": "medium", "rationale": "差別化ポイントを明確にする"}
                ],
                'proposal': [
                    {"action": "提案書フォローアップ", "priority": "high", "rationale": "提案書送付後48時間以内に連絡"},
                    {"action": "Q&A資料準備", "priority": "medium", "rationale": "想定質問への回答を準備"},
                    {"action": "デモ/PoC提案", "priority": "medium", "rationale": "実機能を体験してもらう"}
                ],
                'negotiation': [
                    {"action": "契約書ドラフト送付", "priority": "high", "rationale": "法務確認プロセス開始"},
                    {"action": "価格交渉の決裁確認", "priority": "high", "rationale": "最終価格での合意形成"},
                    {"action": "導入スケジュール提示", "priority": "medium", "rationale": "契約後の進行を明確化"}
                ]
            }

            actions = stage_actions_map.get(stage, [
                {"action": "商談状況確認", "priority": "high", "rationale": "現在のステージを明確化"},
                {"action": "次回ミーティング設定", "priority": "medium", "rationale": "商談を前進させる"},
                {"action": "社内レビュー実施", "priority": "low", "rationale": "戦略見直しの検討"}
            ])

            result = {"actions": actions}
            logger.info(f"[MOCK] Next actions generated for: {deal_data.get('deal_name')}")
            return result

        # 実際のGemini API呼び出し
        try:
            prompt = f"""
以下の商談データから、営業担当者が次に取るべきアクションを3つ提案してください。

商談データ:
- 商談名: {deal_data.get('deal_name', 'N/A')}
- ステージ: {deal_data.get('stage', 'N/A')}
- リスクスコア: {deal_data.get('risk_score', 50)}
- 最終接触: {deal_data.get('last_contact_days', 'N/A')}日前

JSON形式で返してください:
{{
  "actions": [
    {{"action": "アクション1", "priority": "high", "rationale": "理由"}},
    {{"action": "アクション2", "priority": "medium", "rationale": "理由"}},
    {{"action": "アクション3", "priority": "low", "rationale": "理由"}}
  ]
}}
"""

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=600,
                )
            )

            # Extract JSON from markdown code blocks if present
            text = self._extract_json_from_response(response.text)
            result = json.loads(text)
            logger.info(f"Next actions generated for: {deal_data.get('deal_name')}")
            return result

        except Exception as e:
            logger.error(f"Error generating next actions: {e}")
            return {
                "actions": [
                    {"action": "商談状況確認", "priority": "high", "rationale": "分析エラーのため基本アクション"}
                ]
            }

    async def forecast_revenue(self, deals_data: list) -> Dict[str, Any]:
        """売上予測（折れ線グラフ用の指数関数的成長データ）"""
        if self.use_mock:
            import datetime
            import random
            current_month = datetime.datetime.now()
            forecasts = []

            # ✅ 実データから base_amount を計算
            total_amount = sum(d.get('amount', 0) for d in deals_data) if deals_data else 0
            avg_probability = sum(d.get('probability', 0) for d in deals_data) / len(deals_data) if deals_data else 0.5

            # 実データに基づくベース金額（成約確度を考慮）
            base_amount = int(total_amount * avg_probability) if total_amount > 0 else 5000000

            # 折れ線グラフ用：指数関数的成長 + 月次変動
            for i in range(6):
                month_date = current_month + datetime.timedelta(days=30 * i)

                # 指数関数的成長：base * (1.15)^i （月次15%成長）
                growth_factor = 1.15 ** i

                # 月次変動：0-15%の成長変動（横ばい回避）
                monthly_variance = random.uniform(1.00, 1.15)

                predicted_revenue = int(base_amount * growth_factor * monthly_variance)

                forecasts.append({
                    "month": month_date.strftime("%Y-%m"),
                    "predicted_revenue": predicted_revenue,
                    "confidence_score": round(0.90 - (i * 0.05), 2)
                })

            total_revenue = sum(f["predicted_revenue"] for f in forecasts)
            avg_confidence = round(sum(f["confidence_score"] for f in forecasts) / len(forecasts), 2)

            logger.info(f"[MOCK] Revenue forecast: {len(deals_data)} deals (¥{total_amount:,}, {avg_probability:.0%} avg probability) -> base ¥{base_amount:,}, 6-month growth forecast")
            return {
                "forecasts": forecasts,
                "total_predicted_revenue": total_revenue,
                "average_confidence": avg_confidence,
                "growth_rate": 15.0  # 月次15%成長率
            }

        # 実際のGemini API呼び出し（古いSDK 0.1.0rc1対応）
        try:
            total_amount = sum(d.get('amount', 0) for d in deals_data)
            avg_probability = sum(d.get('probability', 0) for d in deals_data) / len(deals_data) if deals_data else 0

            prompt = f"""
商談データ{len(deals_data)}件（総額¥{total_amount:,}、平均確度{avg_probability:.0%}）から、今後6ヶ月の売上予測を算出してください。

JSON形式で返してください:
{{
  "forecasts": [
    {{"month": "2025-11", "predicted_revenue": 金額, "confidence_score": 0.90}}
  ],
  "total_predicted_revenue": 合計予測売上,
  "average_confidence": 平均信頼度,
  "growth_rate": 成長率（%）
}}
"""

            response = genai.generate_text(
                model=self.model_name,
                prompt=prompt,
                temperature=0.1,
                max_output_tokens=800
            )

            text = self._extract_json_from_response(response.result)
            result = json.loads(text)
            logger.info(f"Revenue forecast: {len(deals_data)} deals -> 6-month forecast")
            return result

        except Exception as e:
            logger.error(f"Error forecasting revenue: {e}", exc_info=True)
            return {"forecasts": [], "total_predicted_revenue": 0, "average_confidence": 0, "growth_rate": 0}

    async def predict_churn_risk(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """チャーンリスク予測（会社別に異なる予測を返す）"""
        if self.use_mock:
            customer_id = customer_data.get('customer_id', '')
            engagement_score = customer_data.get('engagement_score', 50)

            # 会社IDに基づいて異なるチャーンリスク予測を返す
            # クラウドテック（company_id: 3daa4a74-88ae-46aa-b0af-2280f11e5dc5）
            if '3daa4a74' in customer_id or 'クラウドテック' in customer_id:
                risk_score, risk_level = 28, "low"
                risk_factors = [
                    "エンゲージメントスコア良好（72点）",
                    "月次アクティブユーザー増加傾向",
                    "機能利用率80%以上"
                ]
                recommended_actions = [
                    "アップセル機会の検討（Enterprise Plan提案）",
                    "成功事例インタビュー依頼"
                ]
            # レント東京（company_id: 06ee52bd-a1cc-4ed4-b384-78894188510a）
            elif '06ee52bd' in customer_id or 'レント東京' in customer_id:
                risk_score, risk_level = 65, "medium"
                risk_factors = [
                    "エンゲージメントスコア低下傾向（42点→38点）",
                    "過去30日間のログイン回数減少",
                    "サポート問い合わせ増加"
                ]
                recommended_actions = [
                    "CSマネージャーによる定期フォロー設定",
                    "オンボーディング再実施の提案",
                    "ユーザートレーニングセッション実施"
                ]
            # その他の会社（デフォルト）
            else:
                if engagement_score >= 70:
                    risk_score, risk_level = 15, "low"
                    risk_factors = ["高いエンゲージメント", "定期的なログイン"]
                    recommended_actions = ["CSチーム接触", "アカウントヘルスチェック"]
                elif engagement_score >= 40:
                    risk_score, risk_level = 50, "medium"
                    risk_factors = ["エンゲージメント低下傾向"]
                    recommended_actions = ["フォローアップミーティング設定", "利用状況レビュー"]
                else:
                    risk_score, risk_level = 85, "high"
                    risk_factors = ["長期ログインなし", "機能利用率極端に低い"]
                    recommended_actions = ["緊急CSコール実施", "チャーン防止施策検討"]

            logger.info(f"[MOCK] Churn risk: Customer {customer_id} -> {risk_level} (score: {risk_score})")
            return {
                "churn_risk_score": risk_score,
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "recommended_actions": recommended_actions
            }

        # 実際のGemini API呼び出し
        try:
            prompt = f"""
Analyze customer churn risk based on the following data:

Customer ID: {customer_data.get('customer_id', 'N/A')}
Engagement Score: {customer_data.get('engagement_score', 50)} (0-100)

Return ONLY valid JSON with this exact structure:
{{
  "churn_risk_score": <integer 0-100>,
  "risk_level": "<string: low or medium or high>",
  "risk_factors": ["<string>", "<string>"],
  "recommended_actions": ["<string>", "<string>"]
}}

Do NOT include any explanation. Return ONLY the JSON object.
"""

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=500,
                    response_mime_type="application/json",
                )
            )

            # デバッグ: Gemini APIレスポンスをログ出力
            logger.info(f"[DEBUG] Gemini API response.text: {response.text[:200] if response.text else 'EMPTY'}")

            text = self._extract_json_from_response(response.text)
            result = json.loads(text)
            logger.info(f"Churn risk analyzed: Customer {customer_data.get('customer_id')}")
            return result

        except Exception as e:
            logger.error(f"Error predicting churn risk: {e}")
            logger.error(f"[DEBUG] response object: {response if 'response' in locals() else 'N/A'}")
            return {"churn_risk_score": 0, "risk_level": "unknown", "risk_factors": [], "recommended_actions": []}

    async def detect_upsell_opportunities(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """アップセル機会検知（モックモード実装済み）"""
        if self.use_mock:
            usage_rate = customer_data.get('usage_rate', 50)
            opportunities = []
            if usage_rate >= 80:
                opportunities.append({
                    "product": "Enterprise Plan",
                    "score": 90,
                    "timing": "今すぐ",
                    "rationale": "利用率80%超過",
                    "expected_revenue": 500000
                })
            elif usage_rate >= 50:
                opportunities.append({
                    "product": "Professional Plan",
                    "score": 60,
                    "timing": "3ヶ月以内",
                    "rationale": "利用率中程度",
                    "expected_revenue": 300000
                })
            logger.info(f"[MOCK] Upsell opportunities: {len(opportunities)} found")
            return {
                "opportunities": opportunities,
                "total_potential_revenue": sum(o["expected_revenue"] for o in opportunities)
            }

        # 実際のGemini API呼び出し
        try:
            prompt = f"""
顧客の利用状況からアップセル機会を検出してください。

顧客ID: {customer_data.get('customer_id', 'N/A')}
利用率: {customer_data.get('usage_rate', 50)}%

JSON形式で返してください:
{{
  "opportunities": [
    {{
      "product": "製品名",
      "score": 0-100のスコア,
      "timing": "提案タイミング",
      "rationale": "根拠",
      "expected_revenue": 期待収益
    }}
  ],
  "total_potential_revenue": 合計潜在収益
}}
"""

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=600,
                )
            )

            text = self._extract_json_from_response(response.text)
            result = json.loads(text)
            logger.info(f"Upsell opportunities detected: {len(result.get('opportunities', []))} found")
            return result

        except Exception as e:
            logger.error(f"Error detecting upsell opportunities: {e}")
            return {"opportunities": [], "total_potential_revenue": 0}

    async def analyze_competitors(self, deals_data: list) -> Dict[str, Any]:
        """競合分析（モックモード実装済み）"""
        if self.use_mock:
            competitors = [
                {
                    "name": "Salesforce",
                    "encounter_count": 15,
                    "win_rate": 0.40,
                    "market_share": 0.35,
                    "strengths": ["ブランド力", "豊富な機能"],
                    "weaknesses": ["価格が高い", "セットアップ複雑"]
                },
                {
                    "name": "HubSpot",
                    "encounter_count": 12,
                    "win_rate": 0.58,
                    "market_share": 0.25,
                    "strengths": ["使いやすいUI", "無料プランあり"],
                    "weaknesses": ["高度なカスタマイズ困難"]
                }
            ]
            logger.info(f"[MOCK] Competitor analysis: {len(competitors)} competitors")
            return {
                "competitors": competitors,
                "our_overall_win_rate": 0.58,
                "market_leader": competitors[0]["name"]
            }

        # 実際のGemini API呼び出し
        try:
            prompt = f"""
{len(deals_data)}件の商談データから競合分析を行ってください。

必ず以下のJSON形式で返してください（全てのテキストフィールドは日本語で記入）:
{{
  "competitors": [
    {{
      "name": "<日本語の競合企業名>",
      "encounter_count": <遭遇回数（整数）>,
      "win_rate": <勝率（0-1の小数）>,
      "market_share": <市場シェア（0-1の小数）>,
      "strengths": ["<日本語の強み1>", "<日本語の強み2>"],
      "weaknesses": ["<日本語の弱み1>", "<日本語の弱み2>"]
    }}
  ],
  "our_overall_win_rate": <自社全体勝率（0-1の小数）>,
  "market_leader": "<日本語の市場リーダー名>"
}}

説明は不要です。JSONオブジェクトのみを返してください。
全てのテキストは日本語で記入してください。
"""

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=800,
                    response_mime_type="application/json",
                )
            )

            text = self._extract_json_from_response(response.text)
            result = json.loads(text)
            logger.info(f"Competitor analysis: {len(result.get('competitors', []))} competitors analyzed")
            return result

        except Exception as e:
            logger.error(f"Error analyzing competitors: {e}")
            return {"competitors": [], "our_overall_win_rate": 0, "market_leader": "N/A"}

    async def analyze_sales_performance(self, reps_data: list) -> Dict[str, Any]:
        """営業パフォーマンス分析（モックモード実装済み）"""
        if self.use_mock:
            reps_performance = [
                {"name": "山田太郎", "total_deals": 25, "won_deals": 18, "win_rate": 0.72, "rank": 1},
                {"name": "佐藤花子", "total_deals": 30, "won_deals": 20, "win_rate": 0.67, "rank": 2},
                {"name": "鈴木一郎", "total_deals": 22, "won_deals": 13, "win_rate": 0.59, "rank": 3}
            ]
            logger.info(f"[MOCK] Sales performance: {len(reps_performance)} reps analyzed")
            return {
                "rankings": reps_performance,
                "top_performer": reps_performance[0],
                "team_avg_win_rate": 0.66
            }

        # 実際のGemini API呼び出し
        try:
            # 営業担当者データをプロンプトに含める
            reps_summary = "\n".join([
                f"- {rep['name']}: 総商談数 {rep['total_deals']}件, 成約数 {rep['won_deals']}件"
                for rep in reps_data
            ])

            prompt = f"""
以下の{len(reps_data)}名の営業担当者のパフォーマンスを分析し、勝率でランキングを作成してください。

営業担当者データ:
{reps_summary}

必ず以下のJSON形式で返してください（全てのテキストフィールドは日本語で記入）:
{{
  "rankings": [
    {{
      "name": "<日本語の担当者名>",
      "total_deals": <総商談数（整数）>,
      "won_deals": <成約数（整数）>,
      "win_rate": <勝率（0-1の小数、won_deals/total_dealsで計算）>,
      "rank": <順位（整数、勝率順）>
    }}
  ],
  "top_performer": {{
    "name": "<日本語のトップパフォーマー名>",
    "total_deals": <総商談数（整数）>,
    "won_deals": <成約数（整数）>,
    "win_rate": <勝率（0-1の小数）>,
    "rank": 1
  }},
  "team_avg_win_rate": <チーム平均勝率（0-1の小数）>
}}

説明は不要です。JSONオブジェクトのみを返してください。
全てのテキストは日本語で記入してください。
"""

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=2000,  # 増やして14名分のデータを返せるように
                    response_mime_type="application/json",
                )
            )

            # デバッグ: Geminiレスポンス全文をログ出力
            logger.info(f"[DEBUG] Gemini raw response: {response.text[:500]}")

            text = self._extract_json_from_response(response.text)
            logger.info(f"[DEBUG] Extracted JSON text: {text[:500]}")

            result = json.loads(text)
            logger.info(f"Sales performance analyzed: {len(result.get('rankings', []))} reps")
            return result

        except Exception as e:
            logger.error(f"Error analyzing sales performance: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"rankings": [], "top_performer": {}, "team_avg_win_rate": 0}

    async def summarize_meetings(self, meetings_data: list) -> Dict[str, Any]:
        """ミーティング要約（モックモード実装済み）"""
        if self.use_mock:
            meetings = []
            for i, meeting in enumerate(meetings_data[:5]):
                # Supabaseから取得したミーティングデータを使って要約を生成
                meeting_type = meeting.get('meeting_type', '商談')
                summary_text = meeting.get('summary', f"{meeting_type}について議論。次のステップを合意。")

                # sentimentをaction_itemsから推定（ポジティブなワードが多ければpositive）
                action_items = meeting.get('action_items', [])
                sentiment = "positive" if action_items else "neutral"

                meetings.append({
                    "title": f"{meeting_type} - {meeting.get('date', '日付不明')[:10]}",
                    "summary": summary_text[:100] + "..." if len(summary_text) > 100 else summary_text,
                    "key_points": ["顧客の課題確認", "予算500-800万円", "導入時期: 今期中"],
                    "sentiment": sentiment
                })
            logger.info(f"[MOCK] Meetings summarized: {len(meetings)} meetings")
            return {"meetings": meetings, "total_meetings": len(meetings)}

        # 実際のGemini API呼び出し
        try:
            meetings_list = []
            for meeting in meetings_data[:5]:  # 最大5件
                meeting_type = meeting.get('meeting_type', '商談')
                meeting_date = meeting.get('date', '日付不明')
                summary = meeting.get('summary', 'サマリーなし')
                meetings_list.append(f"日付: {meeting_date}, タイプ: {meeting_type}, サマリー: {summary[:200]}")

            prompt = f"""
以下のミーティング（最大5件）を要約してください:

{chr(10).join(meetings_list)}

必ず以下のJSON形式で返してください（全てのテキストフィールドは日本語で記入）:
{{
  "meetings": [
    {{
      "title": "<日本語のタイトル（例: 商談 - 2025-10-28）>",
      "summary": "<日本語の要約（100文字以内）>",
      "key_points": ["<日本語のポイント1>", "<日本語のポイント2>"],
      "sentiment": "<positive/neutral/negative のいずれか>"
    }}
  ],
  "total_meetings": <件数（整数）>
}}

説明は不要です。JSONオブジェクトのみを返してください。
全てのテキストは日本語で記入してください。
"""

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=1500,
                    response_mime_type="application/json",
                )
            )

            text = self._extract_json_from_response(response.text)
            result = json.loads(text)
            logger.info(f"Meetings summarized: {len(result.get('meetings', []))} meetings")
            return result

        except Exception as e:
            logger.error(f"Error summarizing meetings: {e}")
            return {"meetings": [], "total_meetings": 0}

    async def track_deal_progress(self, deal_id: str, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """商談進捗トラッキング（モックモード実装済み）"""
        if self.use_mock:
            stage = deal_data.get('stage', 'prospect').lower()
            stage_progress = {
                'prospect': (10, 'ミーティング設定'),
                'meeting': (30, '要件ヒアリング完了'),
                'proposal': (70, '提案書承認'),
                'negotiation': (85, '契約書締結'),
                'closed won': (100, '完了')
            }
            progress_rate, next_milestone = stage_progress.get(stage, (50, 'ステージ確認'))
            logger.info(f"[MOCK] Deal progress: {deal_id} -> {progress_rate}%")
            return {
                "deal_id": deal_id,
                "progress_rate": progress_rate,
                "current_stage": stage,
                "next_milestone": next_milestone,
                "health_status": "high" if progress_rate >= 70 else "medium"
            }

        # 実際のGemini API呼び出し
        try:
            stage = deal_data.get('stage', 'Unknown')

            # ステージマッピング（大文字小文字を統一）
            stage_map = {
                'prospect': {'rate': 10, 'name': '見込み客', 'milestone': '初回コンタクト'},
                'meeting': {'rate': 30, 'name': 'ミーティング', 'milestone': '要件ヒアリング完了'},
                'proposal': {'rate': 70, 'name': '提案中', 'milestone': '提案書承認'},
                'negotiation': {'rate': 85, 'name': '交渉中', 'milestone': '契約書締結'},
                'closed won': {'rate': 100, 'name': '受注', 'milestone': '完了'},
                'closed lost': {'rate': 0, 'name': '失注', 'milestone': 'N/A'}
            }

            stage_lower = stage.lower()
            stage_info = stage_map.get(stage_lower, {'rate': 50, 'name': stage, 'milestone': 'ステージ確認'})

            prompt = f"""
以下の商談の進捗をトラッキングしてください:

商談ID: {deal_id}
ステージ: {stage}（{stage_info['name']}）
金額: ¥{deal_data.get('amount', 0):,}
進捗率目安: {stage_info['rate']}%

必ず以下のJSON形式で返してください:
{{
  "deal_id": "{deal_id}",
  "progress_rate": {stage_info['rate']},
  "current_stage": "{stage_info['name']}",
  "next_milestone": "{stage_info['milestone']}",
  "health_status": "{"high" if stage_info['rate'] >= 70 else "medium" if stage_info['rate'] >= 30 else "low"}"
}}

説明は不要です。上記のJSONをそのまま返してください。
"""

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=400,
                    response_mime_type="application/json",
                )
            )

            text = self._extract_json_from_response(response.text)
            result = json.loads(text)
            logger.info(f"Deal progress tracked: {deal_id} -> {result.get('progress_rate', 0)}%")
            return result

        except Exception as e:
            logger.error(f"Error tracking deal progress: {e}")
            return {"deal_id": deal_id, "progress_rate": 0, "current_stage": "unknown", "next_milestone": "N/A", "health_status": "low"}

    # ========================================
    # Day 2 Phase 1: Suggestion Engine (3機能)
    # ========================================

    async def suggest_next_best_action(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Next Best Action提案（優先度付き3つのアクション）

        Args:
            deal_data: 商談データ（stage, risk_score, last_contact_days等）

        Returns:
            {"actions": [{"action": "...", "priority": "high/medium/low", "rationale": "..."}]}
        """
        if self.use_mock:
            stage = deal_data.get('stage', 'prospect').lower()
            risk_score = deal_data.get('risk_score', 50)
            last_contact_days = deal_data.get('last_contact_days', 0)

            # ステージ別のアクションテンプレート
            stage_actions_map = {
                'prospect': [
                    {"action": "初回ヒアリングミーティング設定", "priority": "high", "rationale": "顧客の課題を深掘りし、ニーズを明確化する"},
                    {"action": "業界別導入事例資料送付", "priority": "medium", "rationale": "同業他社の成功事例で信頼性を高める"},
                    {"action": "決裁者情報の確認と接点構築", "priority": "medium", "rationale": "キーパーソンを早期に特定し関係性を構築"}
                ],
                'meeting': [
                    {"action": "提案書ドラフト作成・社内レビュー", "priority": "high", "rationale": "次回ミーティングで具体的な提案を提示"},
                    {"action": "予算確認のフォローメール送付", "priority": "high", "rationale": "商談進行の確度を高め、適切な提案内容を設計"},
                    {"action": "競合比較表・差別化資料作成", "priority": "medium", "rationale": "競合との差別化ポイントを明確に訴求"}
                ],
                'proposal': [
                    {"action": "提案書送付後48時間以内のフォローアップ", "priority": "high", "rationale": "提案内容の理解度確認と質問対応"},
                    {"action": "想定Q&A資料・FAQ準備", "priority": "medium", "rationale": "社内検討時の疑問点に迅速対応できる体制構築"},
                    {"action": "デモ環境・PoC提案の準備", "priority": "medium", "rationale": "実機能を体験してもらい導入イメージを具体化"}
                ],
                'negotiation': [
                    {"action": "契約書ドラフト送付・法務確認依頼", "priority": "high", "rationale": "法務確認プロセスを開始し、契約締結を加速"},
                    {"action": "最終価格交渉・決裁確認", "priority": "high", "rationale": "双方が納得できる価格での合意形成"},
                    {"action": "導入スケジュール・体制の明確化", "priority": "medium", "rationale": "契約後のスムーズな導入プロセスを保証"}
                ]
            }

            # デフォルトアクション
            default_actions = [
                {"action": "商談状況の再確認・ステージ見直し", "priority": "high", "rationale": "現在のステージを明確化し、適切な戦略立案"},
                {"action": "次回ミーティング日程調整", "priority": "medium", "rationale": "商談を前進させるための定期接触"},
                {"action": "社内レビュー・戦略会議実施", "priority": "low", "rationale": "チーム全体で商談戦略を見直し最適化"}
            ]

            actions = stage_actions_map.get(stage, default_actions)

            # リスクスコアが高い場合、優先度を調整
            if risk_score >= 70:
                actions[0]["priority"] = "urgent"
                actions[0]["rationale"] += "【高リスク商談のため早急対応必要】"

            # 最終接触から7日以上経過している場合、フォローアップを最優先
            if last_contact_days >= 7:
                actions.insert(0, {
                    "action": "緊急フォローアップ連絡",
                    "priority": "urgent",
                    "rationale": f"最終接触から{last_contact_days}日経過。関係性維持のため即時連絡必要"
                })

            logger.info(f"[MOCK] Next Best Action suggested for: {deal_data.get('deal_name', 'Unknown')} (stage: {stage}, risk: {risk_score})")
            return {"actions": actions}

        # 実際のGemini API呼び出し
        try:
            stage = deal_data.get('stage', 'prospect')
            risk_score = deal_data.get('risk_score', 50)
            last_contact_days = deal_data.get('last_contact_days', 0)

            prompt = f"""
商談データから、営業担当者が次に取るべきアクションを3つ提案してください。優先度も含めて提案してください。

商談データ:
- ステージ: {stage}
- リスクスコア: {risk_score} (0-100、高いほど失注リスク大)
- 最終接触: {last_contact_days}日前

JSON形式で返してください:
{{
  "actions": [
    {{"action": "アクション1", "priority": "urgent/high/medium/low", "rationale": "理由"}},
    {{"action": "アクション2", "priority": "urgent/high/medium/low", "rationale": "理由"}},
    {{"action": "アクション3", "priority": "urgent/high/medium/low", "rationale": "理由"}}
  ]
}}
"""

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=600,
                )
            )

            text = self._extract_json_from_response(response.text)
            result = json.loads(text)
            logger.info(f"Next Best Action suggested: {len(result.get('actions', []))} actions")
            return result

        except Exception as e:
            logger.error(f"Error suggesting next best action: {e}")
            return {"actions": [{"action": "商談状況確認", "priority": "high", "rationale": "分析エラーのため基本アクション"}]}

    async def detect_risk_alerts(self, deals: list) -> Dict[str, Any]:
        """
        Risk Detection（高リスク商談の自動検出＋アラート生成）

        Args:
            deals: 商談リストデータ

        Returns:
            {"alerts": [{"deal_id": "...", "risk_factors": [...], "recommended_actions": [...], "urgency": "high/medium/low"}]}
        """
        if self.use_mock:
            alerts = []

            # 高リスク商談を抽出（risk_score >= 60）
            high_risk_deals = [d for d in deals if d.get('risk_score', 0) >= 60]

            if not high_risk_deals:
                logger.info(f"[MOCK] Risk Detection: No high-risk deals found ({len(deals)} deals analyzed)")
                return {
                    "alerts": [],
                    "total_deals_analyzed": len(deals),
                    "high_risk_count": 0
                }

            # 各高リスク商談についてアラート生成
            for deal in high_risk_deals:
                deal_id = deal.get('id', 'unknown')
                deal_name = deal.get('deal_name', 'Unknown Deal')
                stage = deal.get('stage', 'prospect').lower()
                risk_score = deal.get('risk_score', 60)
                last_contact_days = deal.get('last_contact_days', 0)
                amount = deal.get('amount', 0)

                # リスク要因分析
                risk_factors = []
                recommended_actions = []

                if risk_score >= 80:
                    urgency = "critical"
                    risk_factors.append("極めて高いリスクスコア（80+）")
                    recommended_actions.append("経営層・マネージャーへのエスカレーション")
                elif risk_score >= 70:
                    urgency = "high"
                    risk_factors.append("高リスクスコア（70-79）")
                    recommended_actions.append("週次フォローアップの徹底")
                else:
                    urgency = "medium"
                    risk_factors.append("中程度のリスクスコア（60-69）")
                    recommended_actions.append("定期的なステータス確認")

                if last_contact_days >= 14:
                    risk_factors.append(f"長期接触なし（{last_contact_days}日間）")
                    recommended_actions.append("即時連絡・関係性再構築")
                elif last_contact_days >= 7:
                    risk_factors.append(f"接触不足（{last_contact_days}日間）")
                    recommended_actions.append("フォローメール送付")

                if stage == 'proposal' and last_contact_days >= 5:
                    risk_factors.append("提案書送付後のフォロー不足")
                    recommended_actions.append("提案内容の理解度確認・Q&A対応")

                if stage == 'negotiation' and risk_score >= 60:
                    risk_factors.append("交渉ステージでの高リスク")
                    recommended_actions.append("価格・条件の再調整検討")

                if amount >= 5000000:
                    risk_factors.append(f"高額商談（¥{amount:,}）")
                    recommended_actions.append("重点商談としてチーム全体でサポート")

                alerts.append({
                    "deal_id": deal_id,
                    "deal_name": deal_name,
                    "risk_score": risk_score,
                    "stage": stage,
                    "amount": amount,
                    "last_contact_days": last_contact_days,
                    "risk_factors": risk_factors,
                    "recommended_actions": recommended_actions,
                    "urgency": urgency
                })

            # 緊急度順にソート
            urgency_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            alerts.sort(key=lambda x: urgency_order.get(x["urgency"], 3))

            logger.info(f"[MOCK] Risk Detection: {len(alerts)} high-risk deals detected (analyzed {len(deals)} deals)")
            return {
                "alerts": alerts,
                "total_deals_analyzed": len(deals),
                "high_risk_count": len(high_risk_deals),
                "critical_count": len([a for a in alerts if a["urgency"] == "critical"]),
                "summary": f"{len(alerts)}件の高リスク商談を検出（Critical: {len([a for a in alerts if a['urgency'] == 'critical'])}件）"
            }

        # 実際のGemini API呼び出し
        try:
            # 高リスク商談のみフィルタリング（risk_score >= 60）
            high_risk_deals = [d for d in deals if d.get('risk_score', 0) >= 60]

            if not high_risk_deals:
                return {
                    "alerts": [],
                    "total_deals_analyzed": len(deals),
                    "high_risk_count": 0
                }

            # 簡易版：基本的なルールベースアラート生成
            alerts = []
            for deal in high_risk_deals[:5]:  # 最大5件
                risk_score = deal.get('risk_score', 60)

                if risk_score >= 80:
                    urgency = "critical"
                elif risk_score >= 70:
                    urgency = "high"
                else:
                    urgency = "medium"

                alert = {
                    "deal_id": deal.get('id', 'unknown'),
                    "deal_name": deal.get('deal_name', 'Unknown'),
                    "risk_score": risk_score,
                    "urgency": urgency,
                    "risk_factors": [f"リスクスコア: {risk_score}"],
                    "recommended_actions": ["即時フォローアップ"]
                }
                alerts.append(alert)

            logger.info(f"Risk alerts detected: {len(alerts)} high-risk deals")
            return {
                "alerts": sorted(alerts, key=lambda x: x['risk_score'], reverse=True),
                "total_deals_analyzed": len(deals),
                "high_risk_count": len(high_risk_deals)
            }

        except Exception as e:
            logger.error(f"Error detecting risk alerts: {e}")
            return {"alerts": [], "total_deals_analyzed": 0, "high_risk_count": 0}

    async def generate_proposal_draft(self, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Proposal Draft Generation（提案書ドラフト自動生成）

        Args:
            proposal_data: 提案書生成に必要なデータ
                - company_name: 顧客企業名
                - industry: 業界
                - pain_points: 課題（リスト）
                - meeting_summaries: 過去の商談履歴
                - budget: 予算（オプション）

        Returns:
            {"proposal_draft": {"executive_summary": "...", "problem_analysis": "...", ...}}
        """
        if self.use_mock:
            company_name = proposal_data.get('company_name', '株式会社サンプル')
            industry = proposal_data.get('industry', 'SaaS')
            pain_points = proposal_data.get('pain_points', ['業務効率化', 'コスト削減'])
            budget = proposal_data.get('budget', 5000000)

            # 業界別のテンプレート
            industry_templates = {
                'saas': {
                    "executive_summary": f"{company_name}様における営業業務のDX推進をご提案します。本プラットフォームにより、営業生産性30%向上、商談成約率40%改善を実現します。",
                    "problem_analysis": f"現状、{company_name}様では{', '.join(pain_points[:3])}といった課題が見られます。特に、営業プロセスの属人化により、組織全体での知見共有が困難となっています。",
                    "solution": "Revenue Intelligence Platformは、AI/MLを活用し、商談リスク分析、成約率予測、Next Best Action提案を自動化します。営業担当者は戦略的活動に集中でき、マネージャーは的確な意思決定が可能になります。",
                    "expected_benefits": "導入効果として、①営業生産性30%向上、②商談成約率40%改善、③売上予測精度85%達成、④営業サイクル25%短縮を見込んでいます。",
                    "pricing": f"初期費用: ¥1,000,000、月額費用: ¥{int(budget * 0.15):,}（ユーザー数無制限）。6ヶ月間のサポート付き。",
                    "implementation_schedule": "キックオフ（Week 1）→ データ連携（Week 2-3）→ トレーニング（Week 4）→ 本番稼働（Week 5）。導入後3ヶ月間の伴走支援を実施。"
                },
                '不動産賃貸': {
                    "executive_summary": f"{company_name}様の賃貸仲介業務における商談管理の高度化をご提案します。AI分析により、成約率30%向上、契約締結までの期間20%短縮を実現します。",
                    "problem_analysis": f"{company_name}様では、{', '.join(pain_points[:3])}といった課題が見られます。特に、物件案内後のフォローアップが属人的で、追客漏れが発生しています。",
                    "solution": "Revenue Intelligence Platformにより、顧客の物件閲覧履歴・問い合わせ内容をAI分析し、最適な物件提案・フォローアップタイミングを自動提示します。",
                    "expected_benefits": "導入効果として、①成約率30%向上、②契約締結期間20%短縮、③追客漏れゼロ、④顧客満足度向上を実現します。",
                    "pricing": f"初期費用: ¥800,000、月額費用: ¥{int(budget * 0.12):,}（店舗数に応じた従量課金）。不動産業界特化機能を標準搭載。",
                    "implementation_schedule": "初期設定（Week 1）→ 物件データ連携（Week 2）→ スタッフトレーニング（Week 3）→ 段階的稼働（Week 4-5）。"
                },
                '人材紹介': {
                    "executive_summary": f"{company_name}様の人材紹介ビジネスにおける、マッチング精度向上・成約率改善をご提案します。AI活用により、内定承諾率25%向上を実現します。",
                    "problem_analysis": f"{company_name}様では、{', '.join(pain_points[:3])}といった課題が見られます。求職者と企業のマッチング精度向上が急務です。",
                    "solution": "Revenue Intelligence Platformは、求職者の志向性・企業の採用傾向をAI分析し、最適なマッチング・選考フォローを自動提案します。",
                    "expected_benefits": "①内定承諾率25%向上、②選考辞退率30%削減、③コンサルタント稼働効率40%改善、④売上30%増加を実現します。",
                    "pricing": f"初期費用: ¥1,200,000、月額費用: ¥{int(budget * 0.18):,}（成功報酬型オプションあり）。人材業界特化機能標準搭載。",
                    "implementation_schedule": "要件定義（Week 1-2）→ システム連携（Week 3-4）→ データ移行（Week 5）→ トレーニング（Week 6）→ 本番稼働（Week 7）。"
                }
            }

            # 業界キーを正規化
            industry_key = industry.lower().replace('saas', 'saas')
            template = industry_templates.get(industry_key, industry_templates['saas'])

            proposal_draft = {
                "company_name": company_name,
                "industry": industry,
                "generated_at": "2025-10-28",
                "sections": {
                    "1_executive_summary": {
                        "title": "1. エグゼクティブサマリー",
                        "content": template["executive_summary"]
                    },
                    "2_problem_analysis": {
                        "title": "2. 課題分析",
                        "content": template["problem_analysis"]
                    },
                    "3_solution": {
                        "title": "3. ソリューション提案",
                        "content": template["solution"]
                    },
                    "4_expected_benefits": {
                        "title": "4. 期待効果",
                        "content": template["expected_benefits"]
                    },
                    "5_pricing": {
                        "title": "5. 料金プラン",
                        "content": template["pricing"]
                    },
                    "6_implementation_schedule": {
                        "title": "6. 導入スケジュール",
                        "content": template["implementation_schedule"]
                    }
                },
                "metadata": {
                    "total_sections": 6,
                    "estimated_reading_time": "5分",
                    "format": "markdown"
                }
            }

            logger.info(f"[MOCK] Proposal Draft generated for: {company_name} ({industry})")
            return {"proposal_draft": proposal_draft}

        # 実際のGemini API呼び出し
        try:
            company_name = proposal_data.get('company_name', '御社')
            industry = proposal_data.get('industry', 'SaaS')
            amount = proposal_data.get('deal_amount', 0)

            prompt = f"""
{company_name}様向けの提案書ドラフトを作成してください。

【基本情報】
- 会社名: {company_name}
- 業界: {industry}
- 提案金額: ¥{amount:,}

以下のセクションで提案書を作成し、JSON形式で返してください:
{{
  "sections": [
    {{"title": "エグゼクティブサマリー", "content": "概要..."}},
    {{"title": "課題分析", "content": "現状の課題..."}},
    {{"title": "ソリューション提案", "content": "解決策..."}},
    {{"title": "期待効果", "content": "導入メリット..."}},
    {{"title": "料金プラン", "content": "価格..."}},
    {{"title": "導入スケジュール", "content": "スケジュール..."}}
  ],
  "metadata": {{
    "estimated_reading_time": "5分",
    "format": "markdown"
  }}
}}
"""

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=1500,
                )
            )

            text = self._extract_json_from_response(response.text)
            result = json.loads(text)
            logger.info(f"Proposal draft generated for: {company_name}")
            return result

        except Exception as e:
            logger.error(f"Error generating proposal draft: {e}")
            return {
                "sections": [{"title": "エラー", "content": "提案書生成に失敗しました"}],
                "metadata": {"estimated_reading_time": "0分", "format": "text"}
            }
