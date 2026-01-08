# マイクロサービス設計

## 調査日
2026-01-09

## 調査目的

全体システムをマイクロサービスとして設計し、各サービスの責務と境界を明確化する。

### 明らかにしたいこと
1. サービス分割の基準（ドメイン駆動設計に基づく境界）
2. 通信方式の選定（REST / gRPC / メッセージキュー）
3. オーケストレーション基盤の選択（Kubernetes / Cloud Run）
4. モニタリング・分散トレーシングの設計
5. CI/CDパイプラインの構成

---

## 調査結果

### 1. サービス分割パターン（DDD: Domain-Driven Design）

#### 1.1 境界付けられたコンテキスト（Bounded Context）

| 概念 | 説明 |
|------|------|
| **Bounded Context** | 特定のビジネス機能をカプセル化し、独自のドメインモデル・ビジネスルールを持つ |
| **サービス境界の原則** | マイクロサービスは「アグリゲートより小さくせず、Bounded Contextより大きくしない」 |
| **共通閉鎖原則** | 一緒に変更されるものは一緒にパッケージ化する |

#### 1.2 サービス分割の設計

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        ボイスメモ マイクロサービス構成                          │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        API Gateway                                   │  │
│  │              (認証・ルーティング・レート制限)                           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                       │
│         ┌──────────────────────────┼──────────────────────────┐           │
│         │                          │                          │           │
│         ▼                          ▼                          ▼           │
│  ┌─────────────┐           ┌─────────────┐           ┌─────────────┐      │
│  │  Recording  │           │Transcription│           │   Storage   │      │
│  │  Frontend   │──────────▶│  Service    │──────────▶│   Service   │      │
│  │  Service    │           │             │           │             │      │
│  └─────────────┘           └─────────────┘           └─────────────┘      │
│         │                          │                          │           │
│         │                          │                          │           │
│         │                          ▼                          │           │
│         │                  ┌─────────────┐                    │           │
│         │                  │   Search    │◀───────────────────┘           │
│         │                  │   Service   │                                │
│         │                  └─────────────┘                                │
│         │                          │                                      │
│         │                          ▼                                      │
│         │                  ┌─────────────┐                                │
│         └─────────────────▶│    CRM      │                                │
│                            │   Gateway   │                                │
│                            └─────────────┘                                │
└────────────────────────────────────────────────────────────────────────────┘
```

#### 1.3 各サービスの責務

| サービス | 責務 | データストア | 技術スタック |
|---------|------|-------------|-------------|
| **Recording Frontend** | iPhone/Webからの録音・アップロード受付 | - | Swift (iOS) / React (Web) |
| **Transcription Service** | 音声文字起こし・構造化処理 | 処理キュー | Python + Gemini API |
| **Storage Service** | 音声ファイル・メタデータ管理 | GCS + Firestore | Python / Go |
| **Search Service** | セマンティック検索・全文検索 | Chroma Cloud | Python + ChromaDB |
| **CRM Gateway** | revenue-intelligence-platformとの連携 | - | Python / FastAPI |

#### 1.4 Database Per Service パターン

```
┌─────────────────────────────────────────────────────────────────┐
│                    Database Per Service                          │
│                                                                 │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │Transcription│   │   Storage   │   │   Search    │           │
│  │  Service    │   │   Service   │   │   Service   │           │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘           │
│         │                 │                 │                   │
│         ▼                 ▼                 ▼                   │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │   Redis     │   │  Firestore  │   │   Chroma    │           │
│  │ (Job Queue) │   │ + GCS       │   │   Cloud     │           │
│  └─────────────┘   └─────────────┘   └─────────────┘           │
│                                                                 │
│  ※ 各サービスは自身のデータストアのみアクセス                      │
│  ※ データ共有はAPI経由でのみ実施                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### 2. 通信方式の比較

#### 2.1 REST vs gRPC vs メッセージキュー

| 比較項目 | REST | gRPC | メッセージキュー |
|---------|------|------|----------------|
| **パフォーマンス** | 基準 | RESTの最大7倍高速 | 非同期処理に最適 |
| **プロトコル** | HTTP/1.1, JSON | HTTP/2, Protocol Buffers | AMQP, Kafka Protocol |
| **ストリーミング** | 不可 | 双方向対応 | N/A |
| **型安全性** | なし | 強い型付け | スキーマ依存 |
| **学習コスト** | 低 | 中〜高 | 中 |
| **ブラウザ対応** | 完全 | gRPC-Web必要 | WebSocket経由 |
| **デバッグ容易性** | 高 | 中 | 中〜低 |

#### 2.2 gRPC 詳細

```
┌─────────────────────────────────────────────────────────────────┐
│                      gRPC パフォーマンス                          │
│                                                                 │
│  ベンチマーク結果（2025年調査）:                                  │
│  ・スループット: ~8,700 req/sec (REST比 2.5倍)                   │
│  ・レイテンシ: 99パーセンタイルでREST比 40-400% 削減              │
│  ・ペイロードサイズ増加時: RESTより大幅に有利                      │
│                                                                 │
│  推奨用途:                                                       │
│  ・内部サービス間の高頻度通信                                     │
│  ・リアルタイム性が求められる処理                                  │
│  ・大量データ転送                                                │
└─────────────────────────────────────────────────────────────────┘
```

#### 2.3 メッセージキュー比較（Kafka vs RabbitMQ）

| 比較項目 | Apache Kafka | RabbitMQ |
|---------|-------------|----------|
| **スループット** | 数百万 msg/sec | 数万 msg/sec |
| **アーキテクチャ** | 分散ログ | ブローカー型 |
| **メッセージ保持** | 長期保持可能（リプレイ可） | 消費後削除 |
| **ルーティング** | パーティション | Exchange + Routing Key |
| **2025アップデート** | KRaft (ZooKeeper廃止) | Khepri + Raft |
| **推奨用途** | イベントソーシング、高スループット | タスクキュー、複雑なルーティング |

#### 2.4 推奨通信方式

```
┌─────────────────────────────────────────────────────────────────┐
│                    通信方式マッピング                              │
│                                                                 │
│  [外部 → API Gateway]                                           │
│      └── REST (JSON) : 互換性・可読性重視                        │
│                                                                 │
│  [API Gateway → 内部サービス]                                    │
│      └── REST (初期) → gRPC (将来): 段階的移行                   │
│                                                                 │
│  [サービス間非同期通信]                                          │
│      └── Cloud Pub/Sub または RabbitMQ                          │
│          ・文字起こし完了通知                                    │
│          ・AI分析完了通知                                        │
│          ・CRM連携イベント                                       │
│                                                                 │
│  [高スループット要件発生時]                                       │
│      └── Kafka 導入検討                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

### 3. オーケストレーション（Cloud Run vs Kubernetes）

#### 3.1 比較表

| 比較項目 | Cloud Run | GKE (Kubernetes) |
|---------|-----------|------------------|
| **管理負荷** | ほぼゼロ | 高（クラスタ管理必要）|
| **スケーリング** | 自動（0→N） | 自動（設定必要）|
| **コスト** | 使用量課金 | 24時間稼働課金 |
| **コールドスタート** | あり（数秒）| なし（常時起動）|
| **ステートフル** | 不可 | 対応 |
| **カスタマイズ** | 制限あり | 完全制御 |
| **学習コスト** | 低 | 高 |

#### 3.2 ワークロード別推奨

| ワークロード | 推奨 | 理由 |
|------------|------|------|
| **Recording Frontend (API)** | Cloud Run | ステートレス、リクエスト駆動 |
| **Transcription Service** | Cloud Run | 非同期処理、スケール可能 |
| **Storage Service** | Cloud Run | シンプルなCRUD操作 |
| **Search Service** | Cloud Run | クエリベース |
| **CRM Gateway** | Cloud Run | イベント駆動 |
| **Vector DB (ChromaDB)** | Chroma Cloud or GKE | ステートフル、永続化必要 |

#### 3.3 推奨: Cloud Run First アプローチ

```
┌─────────────────────────────────────────────────────────────────┐
│                  Cloud Run First 戦略                            │
│                                                                 │
│  Phase 1: 全サービス Cloud Run でスタート                        │
│           ├── 低コスト・低運用負荷                               │
│           ├── スケール to ゼロ                                  │
│           └── 素早いイテレーション                               │
│                                                                 │
│  Phase 2: 必要に応じてGKE移行を検討                              │
│           ├── ステートフル要件                                   │
│           ├── コールドスタートが許容できない                      │
│           └── 複雑なネットワーク要件                             │
│                                                                 │
│  判断基準:                                                       │
│  ・月間コスト $100+ かつ常時稼働必要 → GKE検討                   │
│  ・99.9%以上の可用性要件 → GKE検討                               │
│  ・複雑なサービスメッシュ必要 → GKE検討                          │
└─────────────────────────────────────────────────────────────────┘
```

---

### 4. サービスメッシュ（Istio vs Linkerd）

#### 4.1 比較表

| 比較項目 | Linkerd | Istio |
|---------|---------|-------|
| **開発元** | Buoyant | Google, IBM, Lyft |
| **複雑さ** | 低 | 高 |
| **パフォーマンス** | 優秀（Istio比 40-400% 低レイテンシ）| 機能豊富だが重い |
| **リソース消費** | 低（Rust製micro-proxy）| 高 |
| **mTLS** | デフォルトON | 設定必要 |
| **学習コスト** | 低 | 高 |
| **L7ルーティング** | 基本的 | 高度 |
| **マルチクラスタ** | 対応 | 高度に対応 |

#### 4.2 2025年ベンチマーク結果

```
Linkerd vs Istio Ambient (2025年4月):
・99パーセンタイル: Linkerd が 163ms 高速
・平均レイテンシ: Linkerd が 11.2ms 低い
・CPU使用量: Linkerd が桁違いに少ない
・メモリ使用量: Linkerd が桁違いに少ない
```

#### 4.3 推奨

**初期段階: サービスメッシュなし**
- Cloud Run は内蔵でmTLS、ロードバランシング提供
- サービス数が少ない間は不要

**スケール時: Linkerd 優先検討**
- シンプルさとパフォーマンス重視
- チームのKubernetes習熟度が低い場合に最適

**高度な要件時: Istio**
- 複雑なL7ルーティング必要時
- マルチクラウド・ハイブリッド環境

---

### 5. モニタリング・分散トレーシング

#### 5.1 OpenTelemetry + Jaeger

```
┌─────────────────────────────────────────────────────────────────┐
│                  Observability Stack                             │
│                                                                 │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │  Service A  │   │  Service B  │   │  Service C  │           │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘           │
│         │                 │                 │                   │
│         └────────────┬────┴────────────┬────┘                   │
│                      │                 │                        │
│                      ▼                 ▼                        │
│            ┌─────────────────────────────────┐                  │
│            │    OpenTelemetry Collector      │                  │
│            │   (Traces + Metrics + Logs)     │                  │
│            └─────────────────────────────────┘                  │
│                      │                 │                        │
│         ┌────────────┴─────┬───────────┴─────┐                  │
│         ▼                  ▼                 ▼                  │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │   Jaeger    │   │ Prometheus  │   │   Loki      │           │
│  │  (Traces)   │   │  (Metrics)  │   │   (Logs)    │           │
│  └─────────────┘   └─────────────┘   └─────────────┘           │
│                            │                                    │
│                            ▼                                    │
│                    ┌─────────────┐                              │
│                    │   Grafana   │                              │
│                    │(Dashboards) │                              │
│                    └─────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

#### 5.2 2025年のトレンド

| トレンド | 説明 |
|---------|------|
| **OpenTelemetry標準化** | CNCF標準、ベンダーロックイン78%削減 |
| **自動計装** | OTel auto-instrumentationで80%のサービスをカバー |
| **相関分析** | Traces + Metrics + Logs の統合分析 |
| **デバッグ効率化** | 分散トレーシング導入で40-60%のデバッグ時間短縮 |

#### 5.3 Google Cloud での実装

```
┌─────────────────────────────────────────────────────────────────┐
│              Google Cloud Observability                          │
│                                                                 │
│  Cloud Run サービス                                              │
│       │                                                         │
│       ├── Cloud Trace (分散トレーシング)                         │
│       │      └── OpenTelemetry SDK で送信                       │
│       │                                                         │
│       ├── Cloud Monitoring (メトリクス)                          │
│       │      └── 自動収集 + カスタムメトリクス                    │
│       │                                                         │
│       └── Cloud Logging (ログ)                                  │
│              └── 構造化ログ (JSON)                               │
│                                                                 │
│  メリット:                                                       │
│  ・Cloud Run と自動統合                                          │
│  ・追加インフラ不要                                              │
│  ・Google Cloud コンソールで統合表示                             │
└─────────────────────────────────────────────────────────────────┘
```

#### 5.4 アラート設計

| アラートレベル | 条件 | 通知先 |
|--------------|------|--------|
| **Critical** | エラー率 > 5%, レイテンシ P99 > 10秒 | Slack + PagerDuty |
| **Warning** | エラー率 > 1%, レイテンシ P99 > 5秒 | Slack |
| **Info** | デプロイ完了、スケールイベント | Slack |

---

### 6. CI/CD パイプライン設計

#### 6.1 GitOps アーキテクチャ

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitOps CI/CD Pipeline                         │
│                                                                 │
│  ┌─────────────┐                                                │
│  │  Developer  │                                                │
│  └──────┬──────┘                                                │
│         │ git push                                              │
│         ▼                                                       │
│  ┌─────────────────────────────────────────┐                    │
│  │            GitHub Repository            │                    │
│  │  ├── /services/transcription/           │                    │
│  │  ├── /services/storage/                 │                    │
│  │  ├── /services/search/                  │                    │
│  │  └── /manifests/                        │                    │
│  └──────────────────┬──────────────────────┘                    │
│                     │                                           │
│         ┌───────────┴───────────┐                               │
│         │                       │                               │
│         ▼                       ▼                               │
│  ┌─────────────┐         ┌─────────────┐                        │
│  │   GitHub    │         │   Argo CD   │                        │
│  │   Actions   │         │  (GitOps)   │                        │
│  │    (CI)     │         │    (CD)     │                        │
│  └──────┬──────┘         └──────┬──────┘                        │
│         │                       │                               │
│         │ Build & Test          │ Sync                          │
│         │ Push Image            │                               │
│         ▼                       ▼                               │
│  ┌─────────────┐         ┌─────────────┐                        │
│  │  Artifact   │         │  Cloud Run  │                        │
│  │  Registry   │────────▶│  Services   │                        │
│  └─────────────┘         └─────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

#### 6.2 CI パイプライン（GitHub Actions）

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # 静的解析
      - name: Lint
        run: |
          ruff check .
          mypy .

      # ユニットテスト
      - name: Unit Tests
        run: pytest tests/unit --cov

      # セキュリティスキャン (Shift-Left)
      - name: Security Scan
        run: |
          trivy fs --security-checks vuln,config .
          bandit -r src/

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      # コンテナイメージビルド
      - name: Build Image
        run: |
          docker build -t $IMAGE_NAME:${{ github.sha }} .

      # イメージスキャン
      - name: Scan Image
        run: trivy image $IMAGE_NAME:${{ github.sha }}

      # Artifact Registry にプッシュ
      - name: Push Image
        run: docker push $IMAGE_NAME:${{ github.sha }}

  deploy-staging:
    needs: build
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Staging
        run: |
          gcloud run deploy $SERVICE_NAME-staging \
            --image $IMAGE_NAME:${{ github.sha }} \
            --region asia-northeast1
```

#### 6.3 CD パイプライン（Cloud Build + Cloud Run）

```yaml
# cloudbuild.yaml
steps:
  # 1. ビルド
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', '${_IMAGE}:${SHORT_SHA}', '.']

  # 2. プッシュ
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', '${_IMAGE}:${SHORT_SHA}']

  # 3. デプロイ（Canary）
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - '${_SERVICE_NAME}'
      - '--image=${_IMAGE}:${SHORT_SHA}'
      - '--region=asia-northeast1'
      - '--tag=canary'
      - '--no-traffic'

  # 4. トラフィック段階移行
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'services'
      - 'update-traffic'
      - '${_SERVICE_NAME}'
      - '--to-tags=canary=10'
      - '--region=asia-northeast1'

substitutions:
  _IMAGE: asia-northeast1-docker.pkg.dev/${PROJECT_ID}/voicememo
  _SERVICE_NAME: transcription-service
```

#### 6.4 デプロイ戦略

| 戦略 | 説明 | リスク | 推奨用途 |
|-----|------|-------|---------|
| **Canary** | 一部トラフィックで検証 | 低 | 本番リリース |
| **Blue/Green** | 新旧環境切り替え | 中 | 大規模変更 |
| **Rolling** | 段階的インスタンス更新 | 低 | デフォルト |

---

## 技術選定肢

### Option A: Cloud Run シンプル構成（推奨）

```
Cloud Run (全サービス) + Cloud Pub/Sub + GCS + Firestore + Chroma Cloud
```

**メリット:**
- 運用負荷最小
- コスト効率（スケール to ゼロ）
- 素早いイテレーション

**デメリット:**
- コールドスタート（数秒）
- 高度なサービスメッシュ機能なし

### Option B: Cloud Run + GKE ハイブリッド

```
Cloud Run (ステートレス) + GKE Autopilot (ステートフル/高可用性)
```

**メリット:**
- 柔軟性
- ステートフルワークロード対応

**デメリット:**
- 運用複雑化
- コスト増

### Option C: GKE フル構成

```
GKE Standard + Linkerd + 自己ホスト ChromaDB
```

**メリット:**
- 完全制御
- 高度なトラフィック制御

**デメリット:**
- 高コスト（$100+/月〜）
- Kubernetes習熟必要

---

## 推奨案

### **Option A: Cloud Run シンプル構成**

**理由:**
1. **現在のフェーズに最適**: 小規模チーム、素早いイテレーション重視
2. **コスト効率**: 使用量課金、初期コスト最小
3. **運用負荷**: インフラ管理ほぼ不要
4. **将来の拡張性**: 必要時にGKE移行可能

### 推奨アーキテクチャ

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        推奨マイクロサービス構成                               │
│                                                                            │
│                         ┌─────────────────────┐                            │
│                         │    Cloud Load       │                            │
│                         │    Balancer         │                            │
│                         └──────────┬──────────┘                            │
│                                    │                                       │
│                         ┌──────────▼──────────┐                            │
│                         │    API Gateway      │                            │
│                         │   (Cloud Run)       │                            │
│                         │   ・認証 (JWT)      │                            │
│                         │   ・レート制限      │                            │
│                         └──────────┬──────────┘                            │
│                                    │                                       │
│         ┌──────────────────────────┼──────────────────────────┐           │
│         │                          │                          │           │
│         ▼                          ▼                          ▼           │
│  ┌─────────────┐           ┌─────────────┐           ┌─────────────┐      │
│  │ Recording   │           │Transcription│           │   Search    │      │
│  │ Service     │           │  Service    │           │   Service   │      │
│  │ (Cloud Run) │           │ (Cloud Run) │           │ (Cloud Run) │      │
│  └──────┬──────┘           └──────┬──────┘           └──────┬──────┘      │
│         │                         │                         │             │
│         │                         │                         │             │
│         ▼                         ▼                         ▼             │
│  ┌─────────────┐           ┌─────────────┐           ┌─────────────┐      │
│  │    GCS      │           │   Gemini    │           │   Chroma    │      │
│  │  (音声)     │           │    API      │           │   Cloud     │      │
│  └─────────────┘           └─────────────┘           └─────────────┘      │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                         Cloud Pub/Sub                                │  │
│  │            (イベント駆動: 文字起こし完了、AI分析完了)                   │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                       │
│                                    ▼                                       │
│                         ┌─────────────────────┐                            │
│                         │    CRM Gateway      │                            │
│                         │    (Cloud Run)      │                            │
│                         └──────────┬──────────┘                            │
│                                    │                                       │
│                                    ▼                                       │
│                         ┌─────────────────────┐                            │
│                         │ Revenue Intelligence│                            │
│                         │     Platform        │                            │
│                         └─────────────────────┘                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 技術スタック一覧

| カテゴリ | 技術 | 理由 |
|---------|-----|------|
| **コンピューティング** | Cloud Run | サーバーレス、自動スケール |
| **API Gateway** | Cloud Run + Firebase Auth | シンプル、統合認証 |
| **メッセージング** | Cloud Pub/Sub | GCP統合、低コスト |
| **音声ストレージ** | Cloud Storage (GCS) | 高耐久性、低コスト |
| **メタデータDB** | Firestore | リアルタイム同期、スケーラブル |
| **ベクトルDB** | Chroma Cloud | マネージド、セットアップ容易 |
| **モニタリング** | Cloud Trace + Cloud Monitoring | GCP統合、追加設定不要 |
| **CI/CD** | GitHub Actions + Cloud Build | GitOps対応 |
| **コンテナレジストリ** | Artifact Registry | GCP統合、脆弱性スキャン |

---

## 参考資料

### マイクロサービスパターン
- [10 Best Practices for Microservices Architecture in 2025 - GeeksforGeeks](https://www.geeksforgeeks.org/blogs/best-practices-for-microservices-architecture/)
- [7 Essential Microservices Architecture Patterns for 2025 - DocuWriter](https://www.docuwriter.ai/posts/microservices-architecture-patterns)
- [Microservices Architecture Guide - ByteByteGo](https://blog.bytebytego.com/p/a-guide-to-microservices-architecture)
- [Microservices Pattern - microservices.io](https://microservices.io/patterns/microservices.html)

### Domain-Driven Design
- [Domain analysis for microservices - Azure Architecture](https://learn.microsoft.com/en-us/azure/architecture/microservices/model/domain-analysis)
- [Domain Driven Design for Microservices: Complete Guide 2025 - SayOneTech](https://www.sayonetech.com/blog/domain-driven-design-microservices/)
- [Using tactical DDD to design microservices - Azure](https://learn.microsoft.com/en-us/azure/architecture/microservices/model/tactical-ddd)

### 通信方式
- [gRPC vs REST: Detailed Comparison 2025 - Wallarm](https://www.wallarm.com/what/grpc-vs-rest-comparing-key-api-designs-and-deciding-which-one-is-best)
- [REST vs gRPC vs Message Queues - Platform Engineers](https://medium.com/@platform.engineers/a-deep-dive-into-communication-styles-for-microservices-rest-vs-grpc-vs-message-queues-ea72011173b3)
- [Kafka vs RabbitMQ 2025 - Medium](https://medium.com/@nikhithsomasani/kafka-vs-rabbitmq-the-best-message-queue-explained-for-full-stack-developers-6ab580f2a69d)
- [Message Queues & Async Processing 2025 - VabTech](https://vabtech.wordpress.com/2025/06/16/message-queues-async-processing-rabbitmq-kafka-azure-service-bus/)

### Event Sourcing / CQRS
- [CQRS, Event Sourcing and Axon Framework 2025 - Intre](https://www.intre.it/en/2025/04/14/microservices-cqrs-event-sourcing-axon-framework/)
- [Event Sourcing pattern - Azure Architecture](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)

### オーケストレーション
- [GKE vs Cloud Run - Google Cloud Blog](https://cloud.google.com/blog/products/containers-kubernetes/when-to-use-google-kubernetes-engine-vs-cloud-run-for-containers)
- [Cloud Run vs GKE - Happtiq](https://www.happtiq.com/blog/cloud-run-vs-gke)
- [Serverless vs Kubernetes - Lumigo](https://lumigo.io/serverless-monitoring/serverless-and-kubernetes-key-differences-and-using-them-together/)

### サービスメッシュ
- [Linkerd vs Istio - Buoyant](https://www.buoyant.io/linkerd-vs-istio)
- [Linkerd vs Ambient Mesh 2025 Benchmarks - Linkerd](https://linkerd.io/2025/04/24/linkerd-vs-ambient-mesh-2025-benchmarks/)
- [Service Mesh in 2025: Istio vs Linkerd - Elysiate](https://www.elysiate.com/blog/service-mesh-istio-linkerd-comparison-guide-2025)

### モニタリング
- [OpenTelemetry and Jaeger 2025 - DEV Community](https://dev.to/signoz/opentelemetry-and-jaeger-key-features-differences-2025-349g)
- [Distributed Tracing with OpenTelemetry 2025 - Kubernetes Advanced](https://www.johal.in/kubernetes-advanced-observability-implementing-opentelemetry-jaeger-and-tempo-for-distributed-tracing-2025/)
- [Backend Observability 2025 - Medium](https://medium.com/@shbhggrwl/backend-observability-in-2025-distributed-tracing-with-opentelemetry-af338a987abb)

### CI/CD
- [CI/CD Best Practices for Microservices - Devtron](https://devtron.ai/blog/microservices-ci-cd-best-practices/)
- [Building CI/CD Pipeline for Microservices on Kubernetes 2025 - Atmosly](https://medium.com/atmosly/https-atmosly-com-blog-building-a-complete-cicd-pipeline-for-microservices-on-kubernetes-2025-38d5bb27d7ee)
- [CI/CD for microservices - Azure Architecture](https://learn.microsoft.com/en-us/azure/architecture/microservices/ci-cd)
- [CI/CD Best Practices 2025 - Kellton](https://www.kellton.com/kellton-tech-blog/continuous-integration-deployment-best-practices-2025)

---

## 結論・決定事項

### サービス分割

| サービス | 責務 | 初期実装 |
|---------|-----|---------|
| **API Gateway** | 認証・ルーティング | Cloud Run |
| **Transcription Service** | 文字起こし | Cloud Run |
| **Storage Service** | ファイル・メタデータ管理 | Cloud Run + GCS + Firestore |
| **Search Service** | セマンティック検索 | Cloud Run + Chroma Cloud |
| **CRM Gateway** | SFA/CRM連携 | Cloud Run |

### 通信方式

| 通信 | 方式 |
|-----|------|
| **外部→内部** | REST (JSON) |
| **内部サービス間（同期）** | REST → gRPC (将来) |
| **内部サービス間（非同期）** | Cloud Pub/Sub |

### インフラ

| カテゴリ | 選定 |
|---------|-----|
| **オーケストレーション** | Cloud Run (サーバーレス) |
| **サービスメッシュ** | 初期は不要、将来Linkerd検討 |
| **モニタリング** | Cloud Trace + Cloud Monitoring + Cloud Logging |
| **CI/CD** | GitHub Actions + Cloud Build |

---

## 残課題

1. **API Gateway実装方式**
   - Cloud Run 単独 vs Firebase Hosting + Cloud Functions
   - Kong / Apigee の必要性評価

2. **サービス間認証**
   - サービスアカウントベース vs JWT伝播
   - IAM設定の詳細設計

3. **データ整合性**
   - 結果整合性の許容範囲
   - Sagaパターンの必要性評価

4. **コールドスタート対策**
   - 最小インスタンス設定の費用対効果
   - ウォームアップ戦略

5. **テスト戦略**
   - Contract Test (Pact等) の導入
   - E2Eテストの自動化

6. **セキュリティ**
   - VPC Service Controls の設定
   - Secret Manager の活用

---

**作成日**: 2026-01-09
**次回レビュー**: 統合アーキテクチャ策定時（テーマ5）
