# 中長期アーキテクチャ調査プラン

**作成日**: 2026-01-09
**目的**: 各テーマを順次調査し、統合アーキテクチャを決定する

---

## 調査フロー

```
┌─────────────────────────────────────────────────────────────────┐
│                        調査フロー                                │
│                                                                 │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│   │ 01_multi     │   │ 02_server    │   │ 03_sfa_crm   │       │
│   │ platform     │──▶│ migration    │──▶│ integration  │       │
│   └──────────────┘   └──────────────┘   └──────────────┘       │
│                                                │                │
│                                                ▼                │
│                      ┌──────────────┐   ┌──────────────┐       │
│                      │ 05_integrated│◀──│ 04_micro     │       │
│                      │ architecture │   │ services     │       │
│                      └──────────────┘   └──────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

---

## テーマ1: マルチプラットフォーム対応

**ファイル**: `01_multiplatform.md`

### 調査目的

iPhoneアプリに加え、Mac/Windows対応のWebブラウザ版を実現する方法を調査

### 調査観点

| 観点 | 調査内容 |
|-----|---------|
| **技術選定** | Web録音技術（MediaRecorder API, WebRTC等） |
| **フレームワーク** | React, Vue, Svelte, Next.js 等の比較 |
| **PWA対応** | オフライン録音、インストール可能性 |
| **音声品質** | ブラウザでの録音品質、フォーマット対応 |
| **クロスブラウザ** | Chrome, Safari, Firefox, Edge対応状況 |
| **デスクトップアプリ** | Electron, Tauri の選択肢 |

### 調査クエリ例

- "web audio recording 2025 best practices"
- "MediaRecorder API browser support 2025"
- "PWA audio recording offline 2025"
- "Tauri vs Electron 2025 comparison"

### 期待成果

- Web録音技術の最適解
- フレームワーク選定
- PWA vs ネイティブアプリの判断
- 実装難易度・工数見積もり

---

## テーマ2: サーバー移行計画

**ファイル**: `02_server_migration.md`

### 調査目的

現在Mac（ローカル）で動作しているstructured_transcriberをクラウドに移行する方法を調査

### 調査観点

| 観点 | 調査内容 |
|-----|---------|
| **クラウド選定** | Google Cloud vs AWS vs Azure |
| **サービス形態** | Cloud Run, Cloud Functions, App Engine, EC2等 |
| **コスト** | 月間利用料金の試算 |
| **ChromaDB移行** | Vector DBのクラウドホスティング |
| **ファイルストレージ** | 音声ファイルの保存先（GCS, S3等） |
| **コールドスタート** | サーバーレスの起動時間問題 |
| **GPU対応** | Whisper等を使う場合のGPU必要性 |

### 調査クエリ例

- "Google Cloud Run Python deployment 2025"
- "ChromaDB cloud hosting options 2025"
- "serverless audio processing latency 2025"
- "Google Cloud vs AWS cost comparison 2025"

### 既存リソース確認

```bash
# structured_transcriberの構成確認
ls -la /Users/test/Desktop/fukugyo_plan/SaaS候補アプリ/structured_transcriber/
cat /Users/test/Desktop/fukugyo_plan/SaaS候補アプリ/structured_transcriber/requirements.txt
```

### 期待成果

- クラウドプラットフォーム選定
- デプロイアーキテクチャ設計
- コスト試算
- 移行手順の概要

---

## テーマ3: SFA/CRM連携

**ファイル**: `03_sfa_crm_integration.md`

### 調査目的

revenue-intelligence-platformとの連携方式を調査・決定

### 調査観点

| 観点 | 調査内容 |
|-----|---------|
| **連携方式** | REST API, GraphQL, Webhook, 共有DB |
| **データ形式** | 文字起こしデータのスキーマ定義 |
| **認証** | OAuth2, API Key, JWT等 |
| **リアルタイム性** | 同期 vs 非同期連携 |
| **エラーハンドリング** | リトライ戦略、データ整合性 |

### 既存リソース確認

```bash
# revenue-intelligence-platformの構成確認
ls -la /Users/test/Desktop/fukugyo_plan/revenue-intelligence-platform/
# API定義があれば確認
find /Users/test/Desktop/fukugyo_plan/revenue-intelligence-platform/ -name "*.yaml" -o -name "openapi*"
```

### 調査クエリ例

- "microservices API design best practices 2025"
- "event-driven architecture patterns 2025"
- "API gateway patterns 2025"

### 期待成果

- 連携方式の決定
- APIスキーマ設計（案）
- データフロー図
- 認証方式の決定

---

## テーマ4: マイクロサービス設計

**ファイル**: `04_microservices.md`

### 調査目的

全体システムをマイクロサービスとして設計し、各サービスの責務と境界を明確化

### 調査観点

| 観点 | 調査内容 |
|-----|---------|
| **サービス分割** | ドメイン駆動設計（DDD）に基づく境界 |
| **通信方式** | 同期（REST/gRPC） vs 非同期（メッセージキュー） |
| **サービスメッシュ** | Istio, Linkerd の必要性 |
| **オーケストレーション** | Kubernetes, Cloud Run, ECS等 |
| **モニタリング** | 分散トレーシング、ログ集約 |
| **CI/CD** | デプロイパイプライン設計 |

### サービス候補

| サービス | 責務 |
|---------|------|
| **Recording Frontend** | iPhone / Web からの録音・アップロード |
| **Transcription Service** | 文字起こし・構造化処理 |
| **Storage Service** | 音声ファイル・メタデータ管理 |
| **Search Service** | Vector DB によるセマンティック検索 |
| **CRM Gateway** | SFA/CRM連携のゲートウェイ |

### 調査クエリ例

- "microservices architecture patterns 2025"
- "event sourcing CQRS 2025"
- "kubernetes vs cloud run 2025"
- "distributed tracing best practices 2025"

### 期待成果

- サービス境界の定義
- 通信方式の決定
- インフラ構成図
- 技術スタック選定

---

## テーマ5: 統合アーキテクチャ

**ファイル**: `05_integrated_architecture.md`

### 目的

テーマ1〜4の調査結果を統合し、全体アーキテクチャを決定

### 作成内容

1. **全体アーキテクチャ図**
2. **技術スタック一覧**
3. **データフロー図**
4. **実装ロードマップ**
5. **コスト見積もり**
6. **リスクと対策**

### 統合時の検討事項

- 各テーマの決定事項間の整合性
- 段階的移行計画（Big Bang vs 漸進的）
- MVP（最小実行可能製品）の定義
- 技術的負債の管理方針

---

## 調査スケジュール（目安）

| 順序 | テーマ | 作業内容 |
|-----|--------|---------|
| 1 | マルチプラットフォーム | Web検索 + 技術検証 |
| 2 | サーバー移行 | 既存コード確認 + クラウド調査 |
| 3 | SFA/CRM連携 | 既存コード確認 + API設計検討 |
| 4 | マイクロサービス | 全体設計検討 |
| 5 | 統合 | 全テーマ統合 + 最終決定 |

---

## 次のアクション

**テーマ1から調査を開始する場合:**

```
「01_multiplatformの調査を開始して」
```

**特定のテーマから開始する場合:**

```
「02_server_migrationの調査を開始して」
```

**全テーマを順次実行する場合:**

```
「調査プランに従って、テーマ1から順に調査を実行して」
```
