# Project Brief - Revenue Intelligence Platform

**作成日**: 2025年10月27日
**実装期間**: 2025年10月28日〜31日（4日間96時間）
**最終更新**: 2025年10月28日

---

## プロジェクト名

**Revenue Intelligence Platform**（リベニューインテリジェンス・プラットフォーム）

プロトタイプ実装版 - 2025年10月完成

---

## プロジェクト概要

### 一行サマリー
AI Agents（Gemini 2.0 Flash）を活用した、セールステック向けRevenue Intelligence Platform のプロトタイプ実装。4日間96時間で、全23機能を実装し、Vercelにデプロイ完了する。

### 背景
- 日本のセールステックは「録音・文字起こし」中心（bellFace、RevComm等）
- グローバル市場では「予測・分析型」が主流（Gong: 評価額$72.5億、Clari等）
- **差別化の核**: Revenue Intelligence（予測・分析）+ AI Agents自律実行（日本初）

---

## 核心的な問題

### 問題1: セールステック市場の差別化不足
- 日本市場: 録音型SaaSが飽和（月額¥5,980-9,000/人）
- 予測・分析機能が弱い
- AI Agentsによる自律実行がない

### 問題2: 高価格・高複雑性
- グローバル製品: 月額¥12-22万/人（中小企業には高額）
- 導入が複雑、初期設定に数週間

### 問題3: API料金の高騰リスク
- 既存SaaSはOpenAI GPT-4使用（高額）
- スケールすると利益率低下

---

## ソリューション

### 1. Revenue Intelligence 10機能（差別化の核）
1. **Deal Risk Score**: 商談リスクスコア（0-100）
2. **Win Rate Analysis**: 成約率分析（ステージ別）
3. **Buyer Engagement Scoring**: 購買エンゲージメント測定
4. **Stakeholder Mapping**: 意思決定者マッピング
5. **Champion Identification**: 社内推進者特定
6. **Win-Loss Analysis**: 成約/失注パターン分析
7. **Competitive Intelligence**: 競合インテリジェンス
8. **Pipeline Velocity**: パイプライン速度分析
9. **Next Best Action Engine**: 次善アクション提案
10. **Revenue Forecasting**: 売上予測（精度89%目標）

### 2. AI Agents自律実行（日本初）
- **Suggestion Engine**: 次アクション提案、リスク検知、提案書生成
- **CrewAI Multi-Agent**: Email/Document/CRM Worker
- **LangGraph Orchestration**: State-based自律化ワークフロー

### 3. Gemini API無料枠完全活用（¥0運用）
- **無料枠**: 1,500 requests/day
- **アラート設定**: 1,200 requests/day（80%）で警告
- **最適化戦略**: キャッシュ・バッチ処理で必要に応じて削減
- **実装方針**: 無料枠内で自由に使用、アラート後最適化
- **API料金**: ¥0（Year 1-10で継続）

### 4. ハイブリッドアーキテクチャ（初学者でも理解可能）
- **フロントエンド**: Next.js 14（App Router）
- **ビジネスロジック**: Next.js API Routes（軽量）
- **AI/ML処理**: FastAPI（マイクロサービス）
- **データ層**: Supabase + SQLite + Redis

---

## プロジェクトの目標

### 最終目標（Day 4 24:00まで）
1. ✅ **全機能実装完了**: Revenue Intelligence 10機能 + AI Agents 3種
2. ✅ **モックデータ生成**: 6社分（SaaS 2社、不動産 2社、人材 2社）
3. ✅ **UI実装**: Next.js ダッシュボード、Suggestion Engine画面、AI Agents画面
4. ✅ **デプロイ完了**: Vercel（フロントエンド）+ Railway（FastAPI）+ Supabase（本番DB）
5. ✅ **Gemini API**: 無料枠（1,500 requests/day）内で運用
6. ✅ **デモ動画**: 5分間のデモ動画作成完了

### 成功の定義（定量）
- **機能実装**: 23機能全て動作（Revenue Intelligence 10 + Suggestion 3 + CrewAI 3 + LangGraph 1）
- **モックデータ**: 210商談、239ミーティング、545メール
- **Gemini API**: 無料枠内で運用（1,200 requests/dayでアラート）
- **デプロイ**: 本番環境稼働、デモ動画公開

### 成功の定義（定性）
- **初学者でも理解可能**: Single Responsibility、Extensive Comments
- **4日間で完成**: Day 1-4のスケジュール厳守
- **差別化明確**: 競合との違いが5秒で説明可能

---

## 技術スタック

### フロントエンド
- **フレームワーク**: Next.js 14（App Router）
- **言語**: TypeScript
- **スタイリング**: Tailwind CSS
- **状態管理**: React Query（@tanstack/react-query）
- **グラフ**: Recharts
- **日付**: date-fns

### バックエンド
- **API（軽量）**: Next.js API Routes
- **AI/MLサービス**: FastAPI + Python 3.11
- **バリデーション**: Zod（TypeScript）、Pydantic（Python）

### AI/ML
- **LLM**: Google Gemini 2.0 Flash Experimental（無料枠）
- **AI Agents**: CrewAI、LangGraph
- **Embedding**: Gemini text-embedding-004

### データベース
- **メイン**: Supabase（PostgreSQL）
- **個社データ**: SQLite
- **キャッシュ**: Redis

### デプロイ
- **フロントエンド**: Vercel
- **FastAPI**: Railway
- **DB**: Supabase Production

---

## 制約条件

### 1. Gemini API無料枠
- **上限**: 1,500 requests/day
- **目標**: 無料枠内（1,500 requests/day以内）
- **超過時**: 予算アラート発火（1,000/1,200/1,400 requests/day）
- **実装方針**: シンプル実装優先（キャッシュなし）、2025年11月以降に最適化

### 2. 実装期間
- **4日間96時間**: 2025年10月28日 0:00 〜 10月31日 24:00
- **実作業時間**: 80時間（休憩・食事4時間/日）

### 3. 初学者でも理解可能
- **コード原則**: Single Responsibility、Extensive Comments、Incremental Development
- **ファイルサイズ**: 各ファイル200行以内（可読性重視）
- **モジュール化**: 明確な責務分離

### 4. モックデータ
- **6社分のみ**: SaaS 2社、不動産 2社、人材 2社
- **本番CRM連携なし**: 全てfaker.jsで生成

---

## スコープ（実装する/しない）

### ✅ 実装する
- Revenue Intelligence 10機能（全て）
- Suggestion Engine 3機能（全て）
- CrewAI Multi-Agent 3 Workers（全て）
- LangGraph State Orchestration（1ワークフロー）
- 6社分モックデータ（210商談）
- Next.js UI（3画面）
- Vercel/Railway/Supabaseデプロイ

### ❌ 実装しない
- 実CRM連携（Salesforce、HubSpot等）
- ユーザー認証（Auth0、Clerk等）
- チーム機能（マルチテナント）
- Email送信機能（SendGrid等）
- 本番監視（Sentry、DataDog等）
- CI/CD（GitHub Actions等）
- プロダクション用エラー監視

---

## リスクと対策

### リスク1: Gemini API無料枠超過
**影響**: 中（追加コスト発生の可能性）
**対策**:
- 予算アラート設定（1,000/1,200/1,400 requests/day）
- 超過時は手動テストで補完
- **2025年11月以降**: キャッシュ実装でAPI呼び出し50%削減

### リスク2: 実装時間不足
**影響**: 大（機能未完成）
**対策**:
- Day 1-4の詳細スケジュール作成済み（04_開発スケジュール.md）
- チェックポイントを6時間ごとに設定
- 優先度明確化（Revenue Intelligence > AI Agents > UI）

### リスク3: デプロイ失敗
**影響**: 中（デモ不可）
**対策**:
- Day 4に8時間確保（デプロイ専用）
- Railway以外にRender.comも候補
- ローカル環境で完全動作確認済みであればOK

### リスク4: モックデータ生成時間超過
**影響**: 小（データ量削減可能）
**対策**:
- 並列処理（6社同時生成）
- データ量削減オプション（210商談 → 150商談）
- 手動テストで補完

---

## 関連ドキュメント

### Memory Bank
- [Active Context](activeContext.md) - 現在の作業状況
- [Progress](progress.md) - Day 1-4進捗管理
- [Tech Context](techContext.md) - 技術詳細
- [System Patterns](systemPatterns.md) - アーキテクチャパターン
- [Product Context](productContext.md) - プロダクト詳細

### 実装計画（初期版・アーカイブ）
- [00_実装計画.md](../docs/original_plan/00_実装計画.md) - 全体計画
- [01_モックデータ仕様.md](../docs/original_plan/01_モックデータ仕様.md) - データ構造
- [03_API仕様.md](../docs/original_plan/03_API仕様.md) - エンドポイント仕様
- [04_開発スケジュール.md](../docs/original_plan/04_開発スケジュール.md) - Day 1-4詳細

---

## プロジェクトの位置づけ

### 上位計画との関係
このプロトタイプは、`/Users/test/Desktop/fukugyo_plan/01_基本計画/`の一部です。

**親プロジェクト**: 10年副業ロードマップ（Year 1-10）
- **Year 1-2**: Revenue Intelligence基盤構築（← このプロトタイプ）
- **Year 3-4**: Suggestion Engine実装
- **Year 5-10**: AI Agents完全自律化（CrewAI → LangGraph）

**このプロトタイプの役割**:
- **技術検証**: Gemini API無料枠で全機能が実現可能か
- **差別化検証**: Revenue Intelligence + AI Agentsの価値検証
- **営業資料**: デモ動画（5分）で顧客獲得

---

## 次のステップ（プロトタイプ完成後）

### 2025年11月以降の最適化タスク
1. **キャッシュ実装の導入**
   - Redis統合（7日間TTL）
   - Gemini API呼び出し50%削減目標
   - バッチ処理との併用でさらに削減
   - 予想削減効果: API呼び出し70-80%削減

### Year 2以降の展開
1. **テンプレート化**: 3業界（SaaS/不動産/人材）のテンプレート抽出
2. **実CRM連携**: Salesforce/HubSpot APIとの連携
3. **プロダクション化**: エラー監視、ログ収集、セキュリティ強化
4. **パフォーマンス最適化**: バッチ処理の効率化、N+1問題解消
5. **スケール検証**: 100社、1,000商談での動作確認

---

**プロジェクト完成予定日**: 2025年10月31日 24:00 ✅
