# サーバー移行計画

## 調査日
2026-01-09

## 調査目的

現在Mac（ローカル）で動作しているstructured_transcriberをクラウドに移行する方法を調査

---

## 現行システム分析

### structured_transcriber 構成

```
structured_transcriber/
├── src/
│   ├── api/          # FastAPI エンドポイント
│   ├── core/         # コアモジュール
│   ├── services/     # 外部サービス連携
│   ├── models/       # データモデル
│   └── utils/        # ユーティリティ
├── chroma_db/        # ベクトルDB（ローカル）
├── data/             # データディレクトリ
├── logs/             # ログファイル
└── config/           # 設定ファイル
```

### 依存パッケージ (requirements.txt)

| パッケージ | 用途 |
|-----------|------|
| openai | OpenAI API連携 |
| google-generativeai | Gemini API（文字起こし） |
| google-api-python-client | Google Drive連携 |
| fastapi + uvicorn | Web API |
| streamlit | Web UI |
| pydantic | データバリデーション |
| watchdog | ファイル監視 |
| prometheus-client | メトリクス |

### 主要機能

- 音声文字起こし（Gemini Audio API）
- Google Drive/iCloud Drive連携
- 参加者管理・話者推論
- ChromaDBによるセマンティック検索
- Web UI（FastAPI + Streamlit）

---

## 調査結果

### 1. クラウドプラットフォーム比較

| 比較項目 | Google Cloud | AWS | Azure |
|---------|--------------|-----|-------|
| **サーバーレス** | Cloud Run | Lambda + Fargate | Container Apps |
| **コンテナ対応** | 優秀 | 優秀 | 優秀 |
| **Python対応** | ネイティブ | ネイティブ | ネイティブ |
| **Gemini連携** | 最適（同一ベンダー） | API経由 | API経由 |
| **無料枠** | 恒久無料枠あり | 12ヶ月限定 | 12ヶ月限定 |
| **新規$300クレジット** | あり | なし | $200 |
| **日本リージョン** | 東京/大阪 | 東京/大阪 | 東京/大阪 |

**推奨: Google Cloud**
- Gemini APIとの親和性
- Cloud Runの使いやすさ
- 恒久無料枠と$300クレジット

### 2. Google Cloud Run 詳細

#### メリット

| 項目 | 詳細 |
|------|------|
| **デプロイ簡易性** | ソースコードから自動ビルド（Dockerfile不要可） |
| **スケーリング** | 0→N自動スケール、リクエストベース課金 |
| **コスト** | 使った分だけ（アイドル時0円） |
| **Buildpacks** | requirements.txt検出で自動Python環境構築 |

#### 設定のベストプラクティス

```yaml
# Cloud Run 推奨設定
リソース:
  CPU: 1 vCPU（開始、負荷に応じて調整）
  メモリ: 512MiB〜1GiB

スケーリング:
  最小インスタンス: 0（コスト優先）or 1（レイテンシ優先）
  最大インスタンス: 10（初期値）

コールドスタート対策:
  - python:3.13-slim イメージ使用
  - 依存関係の軽量化
  - 最小インスタンス=1設定（ユーザー向けAPI）
```

#### FastAPI デプロイ要件

```python
# main.py
import os
from fastapi import FastAPI

app = FastAPI()

# PORT環境変数の取得（Cloud Run必須）
port = int(os.environ.get("PORT", 8080))

# uvicorn起動時
# uvicorn main:app --host 0.0.0.0 --port $PORT
```

```dockerfile
# Dockerfile（オプション - Buildpacksでも可）
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# バッファリング無効化
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 3. ChromaDB 移行オプション

| オプション | 概要 | コスト | 推奨度 |
|-----------|------|--------|--------|
| **Chroma Cloud** | 公式マネージド | 従量課金（$5無料枠） | ★★★ |
| **Cloud Run + 永続ディスク** | 自己ホスト | Cloud Run料金 | ★★☆ |
| **Elestio** | サードパーティマネージド | $5-10/月〜 | ★★☆ |
| **Railway** | サードパーティマネージド | $5-10/月 | ★★☆ |

**推奨: Chroma Cloud**
- AWS/GCP/Azure対応
- 30秒でセットアップ
- 開発フェーズは$5無料枠で十分

**代替案: Cloud Run自己ホスト**
- ChromaDBをCloud Runにデプロイ
- Cloud Storage または Persistent Disk でデータ永続化

### 4. ファイルストレージ

| ストレージ | 用途 | 特徴 |
|-----------|------|------|
| **Google Cloud Storage (GCS)** | 音声ファイル保存 | 高耐久性、低コスト |
| **Firestore** | メタデータ | リアルタイム同期 |
| **Cloud SQL** | リレーショナルデータ | PostgreSQL互換 |

**推奨構成:**
- 音声ファイル → GCS
- 録音メタデータ → Firestore（NoSQL）または Cloud SQL
- ベクトル検索 → Chroma Cloud

### 5. コスト試算（月間）

#### 想定利用量
- ユーザー数: 10人
- 録音: 100件/月
- 平均録音時間: 30分
- 合計音声: 50時間/月

#### 料金見積もり

| サービス | 用途 | 月額目安 |
|---------|------|---------|
| **Cloud Run** | API + 文字起こし処理 | $5-20 |
| **Cloud Storage** | 音声ファイル (50GB) | $1-2 |
| **Chroma Cloud** | ベクトル検索 | $0-5 |
| **Gemini API** | 文字起こし | $10-30 |
| **Secret Manager** | APIキー管理 | $0-1 |
| **合計** | - | **$16-58/月** |

※ 初期は$300無料クレジットで約6-18ヶ月運用可能

---

## 技術選定肢

### Option A: Cloud Run フルマネージド

```
Cloud Run (FastAPI) + GCS + Chroma Cloud + Firestore
```

**メリット:**
- 運用コスト最小
- 自動スケーリング
- インフラ管理不要

**デメリット:**
- コールドスタート（数秒の遅延）
- 実行時間制限（最大60分）

### Option B: GKE (Kubernetes)

```
GKE + Cloud SQL + GCS + ChromaDB (自己ホスト)
```

**メリット:**
- 完全な制御
- 常時起動でコールドスタートなし

**デメリット:**
- 運用コスト高（$50+/月〜）
- Kubernetes習熟が必要

### Option C: Compute Engine (VM)

```
GCE VM + Docker Compose + ローカルChromaDB + GCS
```

**メリット:**
- 現行環境と同等
- シンプルな移行

**デメリット:**
- 24時間課金
- スケーリング手動

---

## 推奨案

### **Option A: Cloud Run フルマネージド**

**理由:**
1. **コスト効率**: 使用時のみ課金、小規模で$20/月以下
2. **運用負荷**: インフラ管理不要
3. **スケーラビリティ**: 需要に応じて自動スケール
4. **移行容易性**: FastAPI → Cloud Runは直接デプロイ可能

### 推奨アーキテクチャ

```
                    ┌─────────────────────────────────────────┐
                    │              Google Cloud               │
                    │                                         │
┌─────────┐         │  ┌─────────────────────────────────┐   │
│ iPhone  │────────▶│  │         Cloud Run               │   │
│   App   │  HTTPS  │  │   ┌─────────────────────────┐   │   │
└─────────┘         │  │   │   FastAPI Application   │   │   │
                    │  │   │   - 録音アップロード     │   │   │
┌─────────┐         │  │   │   - 文字起こしAPI       │   │   │
│   Web   │────────▶│  │   │   - 検索API             │   │   │
│   App   │  HTTPS  │  │   └───────────┬─────────────┘   │   │
└─────────┘         │  └───────────────┼─────────────────┘   │
                    │                  │                     │
                    │     ┌────────────┼────────────┐       │
                    │     │            │            │       │
                    │     ▼            ▼            ▼       │
                    │  ┌──────┐   ┌────────┐   ┌────────┐  │
                    │  │ GCS  │   │Firestore│   │Chroma  │  │
                    │  │音声  │   │メタデータ│   │Cloud  │  │
                    │  └──────┘   └────────┘   └────────┘  │
                    │                                       │
                    │              │                        │
                    │              ▼                        │
                    │     ┌────────────────┐               │
                    │     │   Gemini API   │               │
                    │     │   文字起こし    │               │
                    │     └────────────────┘               │
                    └───────────────────────────────────────┘
```

### 移行手順（概要）

| Phase | 作業内容 | 期間目安 |
|-------|---------|---------|
| **1. 準備** | GCPプロジェクト作成、APIキー設定 | 1日 |
| **2. ストレージ** | GCS バケット作成、Firestore設定 | 1日 |
| **3. アプリ修正** | ローカルパス→GCS、ChromaDB→Chroma Cloud | 2-3日 |
| **4. デプロイ** | Cloud Run初期デプロイ、動作確認 | 1日 |
| **5. 最適化** | コールドスタート対策、監視設定 | 1-2日 |
| **6. 本番切替** | DNS設定、本番運用開始 | 1日 |

---

## 参考資料

- [Deploy Python FastAPI to Cloud Run - Google Cloud](https://docs.cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-fastapi-service)
- [FastAPI Performance Tuning on Cloud Run](https://davidmuraya.com/blog/fastapi-performance-tuning-on-google-cloud-run/)
- [Optimize Python for Cloud Run - Google Cloud](https://docs.cloud.google.com/run/docs/tips/python)
- [Chroma Cloud](https://www.trychroma.com/)
- [ChromaDB Docker Deployment](https://www.quantlabsnet.com/post/chromadb-docker-complete-guide-to-vector-database-implementation-and-container-deployment)
- [ChromaDB on GCP - Medium](https://medium.com/@balzs.bence/two-ways-to-build-a-vector-store-on-gcp-in-no-time-605be03e67ce)
- [AWS Lambda vs Cloud Run Cost 2025 - SparkCo](https://sparkco.ai/blog/aws-lambda-vs-google-cloud-run-cost-analysis-deep-dive)
- [Cloud Run vs Lambda Free Tier 2025](https://www.freetiers.com/blog/aws-lambda-vs-google-cloud-run-comparison)

---

## 結論・決定事項

| 項目 | 決定 |
|------|------|
| **クラウドプラットフォーム** | Google Cloud |
| **コンピューティング** | Cloud Run |
| **音声ストレージ** | Google Cloud Storage (GCS) |
| **メタデータDB** | Firestore |
| **ベクトルDB** | Chroma Cloud（初期）、将来的に自己ホスト検討 |
| **認証** | Firebase Auth または Cloud Identity |

---

## 残課題

1. **Gemini API料金の詳細試算**: 音声時間あたりの実コスト検証
2. **コールドスタート許容度**: ユーザー体験への影響評価
3. **データ移行計画**: 既存ローカルデータのクラウド移行手順
4. **セキュリティ設計**: IAM設定、APIキー管理、ネットワーク構成
5. **CI/CD パイプライン**: Cloud Build + Cloud Run の自動デプロイ設定
6. **監視・アラート**: Cloud Monitoring 設定、エラー通知
