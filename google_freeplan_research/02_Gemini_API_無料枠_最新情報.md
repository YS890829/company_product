# Gemini API 無料枠 最新情報（2026年1月時点）

**調査日**: 2026年1月2日
**重要**: 2025年12月7日にGoogleが予告なく無料枠を大幅削減

---

## 重要な変更点（2025年12月7日）

Googleが**予告なく**無料枠を大幅削減。多くの開発者が突然429エラー（quota exceeded）に遭遇。

### 削減の規模

| モデル | 変更前（〜12/6） | 変更後（12/7〜） | 削減率 |
|--------|-----------------|-----------------|--------|
| Gemini 2.5 Flash | 約250 RPD | **約20 RPD** | **92%減** |
| Gemini 2.5 Pro | 25 RPD | **0 RPD（無料枠廃止）** | 100%減 |

---

## 現在利用可能なモデルと無料枠

| モデル | RPM | TPM | RPD | リリース日 | 備考 |
|--------|-----|-----|-----|-----------|------|
| **Gemini 2.5 Pro** | 5 | 250,000 | 25-100 | 2025年前半 | 複雑な推論向け |
| **Gemini 2.5 Flash** | 2-10 | 250,000 | **20-250** | 2025年前半 | 12月に92%削減の報告あり |
| **Gemini 2.5 Flash-Lite** | 15-30 | 250,000 | **1,000-1,500** | 2025年 | **無料枠で最も実用的** |
| **Gemini 3 Pro Preview** | 10-50 | - | 100+ | 2025年11月18日 | 変動制、API無料枠なしの報告も |
| **Gemini 3 Flash Preview** | - | - | - | 2025年12月17日 | API無料枠の詳細は未公開 |

※RPM=リクエスト/分、TPM=トークン/分、RPD=リクエスト/日

---

## Gemini 3 シリーズの概要

### リリース履歴

| モデル | リリース日 | 特徴 |
|--------|-----------|------|
| **Gemini 3 Pro** | 2025年11月18日 | 20ベンチマーク中19で最高性能、GPT-5 Proを上回る |
| **Gemini 3 Deep Think** | 2025年12月4日 | 複雑な数学・科学・論理問題向けの反復推論 |
| **Gemini 3 Flash** | 2025年12月17日 | Pro級性能を1/4以下のコストで、速度重視 |

### ベンチマーク結果（Gemini 3 Pro）

- LMArena Leaderboard: **1501 Elo**（トップ）
- Humanity's Last Exam: **37.5%**（ツールなし）、41%（ツールあり） ※GPT-5 Proは31.64%
- GPQA Diamond: **91.9%**
- SWE-bench Verified（Gemini 3 Flash）: **78%**

---

## 無料枠で現実的にできること

### 推奨：Gemini 2.5 Flash-Lite

- **1,000〜1,500 RPD**: 1日に十分なリクエスト数
- **15-30 RPM**: バースト的な利用も可能
- プロトタイピング・学習用途に最適

### 制限あり：Gemini 2.5 Flash

- **約20 RPD**（12月の削減後）
- 30秒に1リクエストのペース
- 本番利用には不向き

### 実質使えない：Gemini 2.5 Pro / 3 Pro

- 無料枠が極めて限定的、または無し
- テスト用途のみ

---

## Billing Tier構造

| Tier | 条件 | 特徴 |
|------|------|------|
| **Free** | 登録のみ | RPM: 2-15、RPD: 20-1,500（モデルによる） |
| **Tier 1** | Cloud Billing有効化 | 大幅に緩和、従量課金開始 |
| **Tier 2** | 累計支出$250+ & 30日経過 | さらに緩和 |
| **Tier 3** | 累計支出$1,000+ & 30日経過 | 最大限度 |

---

## 有料版の価格

| モデル | 入力 | 出力 |
|--------|------|------|
| Gemini 2.5 Flash | $0.075/1Mトークン | $0.30/1Mトークン |
| Gemini 3 Flash | $0.50/1Mトークン | $3.00/1Mトークン |
| Gemini 3 Pro | $2.00/1Mトークン（≤200K） | $12.00/1Mトークン |
| Gemini 3 Pro | $4.00/1Mトークン（>200K） | $18.00/1Mトークン |

---

## 重要な注意点

### WorkspaceプランとAPI無料枠は別枠

- Google Workspace Business Standardを契約しても**API無料枠は増えない**
- APIの制限は**プロジェクト単位**で決まる
- Workspaceで得られるGemini機能は**ユーザー向け**（サイドパネル等）

### 制限の独立性

4つのレート制限（RPM, TPM, RPD, コンテキストウィンドウ）は**独立してチェック**される。RPMに余裕があっても、TPMやRPDを超過すると429エラーが発生。

### リセットタイミング

- RPD（1日あたりリクエスト）: **太平洋時間の深夜0時**にリセット

---

## 代替手段

### Gemini CLI

- 通常APIより大幅に緩和された制限（60 RPM, 1,000 RPD）
- OAuth認証で利用

### Google AI Studio

- ブラウザ上で無料テスト可能
- すべての地域で無料

---

## 参考リンク

- [Gemini API Rate Limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini 3 Introduction](https://blog.google/products/gemini/gemini-3/)
- [Gemini 3 Flash Launch](https://9to5google.com/2025/12/17/gemini-3-flash-launch/)
