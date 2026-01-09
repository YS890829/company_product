# System Architecture - Realtime Transcriber

**最終更新**: 2025-10-23
**バージョン**: Phase 22完了版
**ステータス**: ✅ 本番稼働中

---

## 📋 目次

1. [システム概要](#システム概要)
2. [アーキテクチャ全体図](#アーキテクチャ全体図)
3. [ディレクトリ構造](#ディレクトリ構造)
4. [主要コンポーネント](#主要コンポーネント)
5. [データフロー](#データフロー)
6. [外部サービス連携](#外部サービス連携)
7. [データストレージ](#データストレージ)
8. [セキュリティ](#セキュリティ)
9. [スケーラビリティ](#スケーラビリティ)

---

## システム概要

### 目的
音声ファイル（ボイスメモ）を自動的に文字起こしし、話者識別、トピック抽出、セマンティック検索を可能にするシステム

### 主要機能
- ✅ **自動文字起こし**: Gemini Audio APIによる高精度文字起こし + 話者識別
- ✅ **クラウド連携**: iCloud Drive / Google Drive監視・自動処理
- ✅ **カレンダー統合**: Google Calendar連携による会議・イベント自動マッチング
- ✅ **話者推論**: LLMによる話者名推論（"Speaker 1" → "杉本"）
- ✅ **セマンティック検索**: ChromaDB + Embeddingによる意味検索
- ✅ **ドキュメント生成**: Google Docs自動作成（モバイル対応）
- ✅ **統合パイプライン**: トピック抽出、参加者管理、Enhanced JSON生成

### 技術スタック
- **言語**: Python 3.11
- **主要フレームワーク**: FastAPI, Uvicorn
- **AI/ML**: Google Gemini (1.5 Flash / 1.5 Pro), ChromaDB
- **データベース**: SQLite (会議・参加者データ), ChromaDB (ベクトルDB)
- **クラウドAPI**: Google Drive API, Google Calendar API, Google Docs API
- **監視**: watchdog (ファイルシステム), FastAPI Webhook

---

## アーキテクチャ全体図

```
┌─────────────────────────────────────────────────────────────────┐
│                     Input Sources (音声入力)                      │
├─────────────────────────────────────────────────────────────────┤
│  iCloud Drive          │  Google Drive       │  Manual Upload   │
│  (ボイスメモ自動同期)    │  (Webhook通知)      │  (直接アップロード) │
└──────────┬──────────────┴──────────┬──────────┴──────────┬──────┘
           │                         │                      │
           ▼                         ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Monitoring Layer (監視層)                      │
├─────────────────────────────────────────────────────────────────┤
│  iCloud Monitor        │  Webhook Server     │  Manual Trigger  │
│  (watchdog監視)        │  (FastAPI/Uvicorn)  │  (CLI実行)        │
│  - ファイル検知         │  - Push通知受信      │  - 直接実行       │
│  - .qta → .m4a変換    │  - ファイルダウンロード│                  │
│  - 重複チェック         │  - 重複チェック       │                  │
└──────────┬──────────────┴──────────┬──────────┴──────────┬──────┘
           │                         │                      │
           └─────────────────────────┴──────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Processing Layer (処理層)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Transcription Service (文字起こしサービス)                │  │
│  │  - Gemini Audio API呼び出し                               │  │
│  │  - Speaker diarization (話者識別)                         │  │
│  │  - 要約生成                                                │  │
│  │  - タイムスタンプ付与                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Filename Optimization (ファイル名最適化)                  │  │
│  │  - LLMによる内容ベースの命名                              │  │
│  │  - タイムスタンプ + 説明的ファイル名生成                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Calendar Integration (カレンダー統合)                     │  │
│  │  - Google Calendar API連携                                │  │
│  │  - イベント時刻マッチング                                  │  │
│  │  - 会議情報抽出                                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Integrated Pipeline (統合パイプライン - Phase 11-3)       │  │
│  │  - トピック抽出                                            │  │
│  │  - 参加者管理                                              │  │
│  │  - Speaker推論 (LLM)                                       │  │
│  │  - Enhanced JSON生成                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Google Docs Export (ドキュメント生成)                     │  │
│  │  - Google Docs API呼び出し                                │  │
│  │  - 構造化フォーマット                                       │  │
│  │  - モバイル最適化                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Storage Layer (ストレージ層)                    │
├─────────────────────────────────────────────────────────────────┤
│  SQLite DB            │  ChromaDB           │  Local Files      │
│  - meetings           │  - Embeddings       │  - downloads/     │
│  - participants       │  - Metadata         │  - logs/          │
│  - participant_       │  - Collections      │  - .jsonl (logs)  │
│    meetings           │                     │                   │
└─────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Output Services (出力サービス)                   │
├─────────────────────────────────────────────────────────────────┤
│  Search API           │  Web UI             │  Export Tools     │
│  - セマンティック検索   │  - 会議一覧         │  - CSV/JSON出力   │
│  - キーワード検索      │  - 検索インターフェース│  - Google Docs連携│
└─────────────────────────────────────────────────────────────────┘
```

---

## ディレクトリ構造

```
realtime_transcriber_benchmark_research/
│
├── src/                           # ソースコード
│   ├── core/                      # コア機能（9ファイル）
│   │   ├── config.py              # 環境変数・設定管理
│   │   ├── logging_config.py      # ロギング設定
│   │   ├── gemini_client.py       # Gemini API クライアント
│   │   ├── gemini_cost_manager.py # コスト管理・予算制御
│   │   ├── gemini_helpers.py      # Gemini ヘルパー関数
│   │   ├── error_handlers.py      # エラーハンドリング・リトライ
│   │   ├── calendar_integration.py # Google Calendar連携
│   │   └── summary_generator.py   # 要約生成
│   │
│   ├── models/                    # データモデル（1ファイル）
│   │   └── db_manager.py          # SQLite DB管理
│   │
│   ├── services/                  # サービス層（30ファイル）
│   │   ├── transcription/         # 文字起こしサービス
│   │   │   └── structured_transcribe.py  # メイン文字起こし処理
│   │   │
│   │   ├── participants/          # 参加者管理
│   │   │   ├── participant_manager.py
│   │   │   └── participant_inference.py  # LLM話者推論
│   │   │
│   │   ├── topics/                # トピック抽出
│   │   │   └── topic_extractor.py
│   │   │
│   │   ├── pipeline/              # 統合パイプライン
│   │   │   └── integrated_pipeline.py  # Phase 11-3統合処理
│   │   │
│   │   ├── search/                # セマンティック検索
│   │   │   ├── semantic_search.py
│   │   │   └── search_api.py
│   │   │
│   │   ├── vector_db/             # ChromaDB管理
│   │   │   ├── chroma_manager.py
│   │   │   ├── build_unified_vector_index.py
│   │   │   └── embedding_generator.py
│   │   │
│   │   ├── monitoring/            # ファイル監視
│   │   │   ├── icloud_monitor.py  # iCloud Drive監視
│   │   │   └── webhook_server.py  # Google Drive Webhook
│   │   │
│   │   └── webapp/                # Web UI
│   │       └── api_server.py
│   │
│   └── utils/                     # ユーティリティ（5ファイル）
│       └── file_management/
│           ├── cloud_file_manager.py      # クラウドファイル自動削除
│           ├── unified_registry.py        # 統合ファイルレジストリ
│           └── generate_smart_filename.py # LLMファイル名生成
│
├── config/                        # 設定ファイル
│   └── settings.py
│
├── data/                          # データディレクトリ
│   └── participants.db            # SQLite DB（会議・参加者）
│
├── chroma_db/                     # ChromaDB（ベクトルDB）
│   └── (7,655 embeddings)
│
├── downloads/                     # 処理済み音声ファイル
│   ├── *.m4a                      # 音声ファイル
│   ├── *_structured.json          # 基本JSON
│   └── *_structured_enhanced.json # Enhanced JSON (speaker_inference含む)
│
├── logs/                          # ログファイル
│   ├── icloud_monitor.log
│   ├── webhook_server.log
│   └── transcription_*.log
│
├── tools/                         # ツール（9ファイル）
│   ├── drive_docs_export.py
│   ├── drive_upload.py
│   └── ...
│
├── scripts/                       # スクリプト（7ファイル）
│   ├── gemini_cost_monitor.py
│   └── ...
│
├── tests/                         # テストドキュメント
│   ├── MANUAL_TEST_PLAN.md        # 手動テスト計画・結果
│   ├── TEST_EXECUTION_REPORT.md   # Phase 19-20実行記録
│   ├── TEST_SUMMARY.md            # テスト概要
│   └── test_strategy.md           # テスト戦略
│
├── docs/                          # ドキュメント
│   ├── architecture.md            # このファイル
│   └── refactoring_plan.md
│
├── memory-bank/                   # Memory Bank
│   └── progress.md                # 進捗管理
│
└── archive_old_structure/         # 旧実装アーカイブ
    └── (Phase 0-21の旧実装)
```

---

## 主要コンポーネント

### 1. Core Module (`src/core/`)

#### Config (`config.py`)
- 環境変数管理（Gemini API Key, Google API credentials）
- パス設定（ダウンロードディレクトリ、DB、ChromaDB）
- API設定（Free tier / Paid tier切り替え）

#### Gemini Client (`gemini_client.py`)
- Gemini API ラッパー
- モデル選択（Flash / Pro）
- 音声・テキスト処理統合

#### Cost Manager (`gemini_cost_manager.py`)
- API使用量追跡
- コスト計算
- 予算制御（日次上限）

#### Error Handlers (`error_handlers.py`)
- Exponential backoffリトライ
- レート制限対応
- API エラーハンドリング

#### Calendar Integration (`calendar_integration.py`)
- Google Calendar API認証
- イベント取得・マッチング
- 時刻ベース検索

### 2. Models Module (`src/models/`)

#### Database Manager (`db_manager.py`)
- SQLite接続管理
- スキーマ定義:
  - `meetings`: 会議メタデータ
  - `participants`: 参加者マスター
  - `participant_meetings`: 多対多関係
- CRUD操作

**Schema**:
```sql
meetings (
    meeting_id TEXT PRIMARY KEY,
    file_name TEXT,
    date TEXT,
    duration_seconds REAL,
    summary TEXT,
    calendar_event_id TEXT,
    google_docs_url TEXT,
    created_at TEXT
)

participants (
    participant_id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    email TEXT,
    role TEXT
)

participant_meetings (
    participant_id INTEGER,
    meeting_id TEXT,
    FOREIGN KEY (participant_id) REFERENCES participants(participant_id),
    FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id)
)
```

### 3. Services Module (`src/services/`)

#### Transcription Service (`transcription/structured_transcribe.py`)

**処理フロー**:
1. 音声ファイル読み込み
2. Gemini Audio API呼び出し（文字起こし + Speaker diarization）
3. 要約生成（Gemini Flash）
4. JSON構造化
5. ファイル名最適化（LLM生成）
6. Calendar統合
7. Google Docs作成
8. 統合パイプライン実行
9. DB格納（SQLite + ChromaDB）

**出力形式**:
- `*_structured.json`: 基本構造化データ
- `*_structured_enhanced.json`: Enhanced版（speaker_inference含む）

#### Integrated Pipeline (`pipeline/integrated_pipeline.py`)

**Phase 11-3 統合処理**:
1. トピック抽出
2. 参加者推論（LLM）
3. Enhanced JSON生成
4. Vector DB格納

**Speaker推論例**:
```json
{
  "speaker_inference": {
    "sugimoto_speaker": "Speaker 1",
    "confidence": "high",
    "participants_mapping": {
      "Speaker 1": "杉本"
    }
  }
}
```

#### Monitoring Services

**iCloud Monitor (`monitoring/icloud_monitor.py`)**:
- watchdogによるファイルシステム監視
- `.qta` → `.m4a` 自動変換
- 重複検出（統合レジストリ）
- 自動文字起こしトリガー

**Webhook Server (`monitoring/webhook_server.py`)**:
- FastAPI/Uvicorn実装
- Google Drive Push Notifications受信
- ファイル自動ダウンロード
- 重複検出
- 処理後のクラウドファイル自動削除

#### Vector DB Service (`vector_db/`)

**ChromaDB管理**:
- Embedding生成（Gemini Embedding API）
- セマンティック検索
- メタデータ付きインデックス
- コレクション管理

**検索クエリ例**:
```python
results = search_meetings(
    query="病院での会話",
    n_results=5
)
```

### 4. Utils Module (`src/utils/`)

#### Cloud File Manager (`file_management/cloud_file_manager.py`)
- Google Drive ファイル削除
- 安全性バリデーション:
  - ローカルファイル存在確認
  - DB格納確認
  - Vector DB格納確認
- 削除ログ記録（`.deletion_log.jsonl`）

#### Unified Registry (`file_management/unified_registry.py`)
- iCloud/Google Drive統合管理
- 重複検出
- 処理履歴追跡（`.processed_files_registry.jsonl`）

---

## データフロー

### E2E処理フロー（iCloud経由）

```
1. ユーザー: ボイスメモ録音
   ↓
2. iCloud: 自動同期 → iCloud Drive
   ↓
3. iCloud Monitor: ファイル検知 (watchdog)
   ↓
4. 変換: .qta → .m4a
   ↓
5. downloads/にコピー
   ↓
6. 統合レジストリ: 重複チェック
   ↓
7. Gemini API: 文字起こし + Speaker diarization
   ↓
8. 要約生成: Gemini Flash
   ↓
9. JSON生成: *_structured.json
   ↓
10. ファイル名最適化: LLM生成
   ↓
11. Calendar統合: イベントマッチング
   ↓
12. Google Docs作成
   ↓
13. 統合パイプライン:
    - トピック抽出
    - Speaker推論
    - Enhanced JSON生成
   ↓
14. DB格納: SQLite (meetings, participants)
   ↓
15. Vector DB格納: ChromaDB (embeddings)
   ↓
16. 完了通知
```

### E2E処理フロー（Google Drive経由）

```
1. ユーザー: Google Driveにアップロード
   ↓
2. Google Drive: Push通知送信
   ↓
3. Webhook Server: 通知受信 (FastAPI)
   ↓
4. ファイルダウンロード → downloads/
   ↓
5. 統合レジストリ: 重複チェック
   ↓
6-15. (上記iCloudフローの7-15と同じ)
   ↓
16. クラウドファイル自動削除:
    - 安全性バリデーション
    - Google Drive削除
    - 削除ログ記録
   ↓
17. 完了通知
```

---

## 外部サービス連携

### Google Cloud Services

#### 1. Gemini API
- **モデル**:
  - `gemini-1.5-flash-002` (Free tier): 文字起こし、要約、ファイル名生成
  - `gemini-1.5-pro-002` (Paid tier): 高精度処理（オプション）
- **機能**:
  - Audio transcription with speaker diarization
  - Text generation (要約、推論)
  - Embedding generation (ベクトル検索)
- **コスト管理**:
  - 日次予算制御
  - Free tier / Paid tier 自動切り替え
  - 使用量追跡

#### 2. Google Calendar API
- **機能**:
  - イベント取得（日付範囲）
  - イベントマッチング（時刻ベース）
  - 会議情報抽出
- **認証**: OAuth 2.0 (`token.json`)

#### 3. Google Drive API
- **機能**:
  - Push Notifications (Webhook)
  - ファイルダウンロード
  - ファイル削除（処理後）
  - メタデータ取得
- **認証**: OAuth 2.0 (`token.json`)

#### 4. Google Docs API
- **機能**:
  - ドキュメント作成
  - 構造化フォーマット挿入
  - モバイル最適化表示
- **認証**: OAuth 2.0 (`token.json`)

### 外部ツール

#### ChromaDB
- **用途**: ベクトルデータベース
- **ストレージ**: ローカル (`chroma_db/`)
- **機能**:
  - Embedding保存（7,655件）
  - セマンティック検索
  - メタデータフィルタリング

---

## データストレージ

### 1. SQLite Database (`data/participants.db`)

**テーブル構成**:
- `meetings`: 会議メタデータ（9件）
- `participants`: 参加者マスター（72名）
- `participant_meetings`: 関連付けテーブル

**サイズ**: 204KB

### 2. ChromaDB (`chroma_db/`)

**コレクション**:
- `unified_meetings`: 統合会議インデックス

**データ**:
- Embeddings: 7,655件
- サイズ: 71.46MB

### 3. ローカルファイル

**downloads/**:
- 音声ファイル (`.m4a`)
- 構造化JSON (`*_structured.json`)
- Enhanced JSON (`*_structured_enhanced.json`)

**logs/**:
- `icloud_monitor.log`
- `webhook_server.log`
- `transcription_*.log`

**レジストリファイル**:
- `.processed_files_registry.jsonl`: 処理済みファイル記録
- `.deletion_log.jsonl`: クラウド削除ログ
- `.processed_drive_files.txt`: Google Drive処理履歴

---

## セキュリティ

### 認証・認可

#### API Key管理
- 環境変数（`.env`）で管理
- `GEMINI_API_KEY_FREE`: Free tier
- `GEMINI_API_KEY_PAID`: Paid tier
- Git管理対象外（`.gitignore`）

#### OAuth 2.0
- Google APIs認証
- `token.json`: アクセストークン保存
- `credentials.json`: クライアント認証情報
- 自動トークンリフレッシュ

### データ保護

#### ローカルストレージ
- 音声ファイル: ローカル専用
- DB: ローカル専用（暗号化なし）
- ログ: ローカル専用

#### クラウドストレージ
- Google Drive: OAuth認証
- Google Docs: 作成者のみアクセス可能
- 処理後の自動削除: 安全性バリデーション実施

### セキュリティベストプラクティス

✅ **実施済み**:
- API Key環境変数化
- OAuth 2.0認証
- Git管理からの機密情報除外
- 処理ロック（重複防止）

⚠️ **今後の改善**:
- DB暗号化
- ログローテーション
- アクセス監査ログ

---

## スケーラビリティ

### 現在の制約

#### パフォーマンス
- **ボトルネック**: Gemini API呼び出し（ネットワークI/O）
- **処理時間**: 平均30-60秒/ファイル
- **並列処理**: 制限あり（API レート制限）

#### ストレージ
- **ChromaDB**: ローカルストレージ（サーバー移行可能）
- **SQLite**: 単一ファイル（PostgreSQL移行推奨）
- **音声ファイル**: ローカル保存（クラウドストレージ推奨）

### スケーラビリティ戦略

#### 短期（Phase 23-25）
- [ ] ChromaDBサーバーモード移行
- [ ] 処理キュー実装（Celery/RQ）
- [ ] API レート制限対応強化

#### 中期（Phase 26-30）
- [ ] PostgreSQL移行
- [ ] Redis キャッシュ導入
- [ ] 水平スケーリング（複数ワーカー）

#### 長期（Phase 31+）
- [ ] クラウドストレージ統合（S3/GCS）
- [ ] Kubernetes デプロイ
- [ ] マルチリージョン対応

---

## パフォーマンスメトリクス

### Phase 22ベンチマーク

**TEST-C1 (iCloud E2E)**:
- 音声長: 7.6秒
- 処理時間: 約30秒
- 文字起こし: 157文字、7セグメント
- Vector DB更新: 7639→7640 (+1)

**TEST-C2 (Google Drive Webhook)**:
- 音声長: 28.8秒
- ファイルサイズ: 471KB
- 処理時間: 約45秒
- 文字起こし: 88文字、3セグメント
- Vector DB更新: 7652→7655 (+3)
- クラウド削除: 正常完了

---

## トラブルシューティング

### よくある問題

#### 1. `ModuleNotFoundError: No module named 'tenacity'`
**原因**: Python 3.8環境で実行
**解決**: Python 3.11を使用
```bash
python3.11 -m pip install tenacity
```

#### 2. Gemini API エラー
**原因**: API Key未設定/無効
**解決**: `.env`ファイル確認
```bash
GEMINI_API_KEY_FREE=your_api_key_here
```

#### 3. Google OAuth エラー
**原因**: `token.json`期限切れ
**解決**: 再認証
```bash
rm token.json
# 次回実行時に再認証フロー開始
```

#### 4. ChromaDB エラー
**原因**: DB破損
**解決**: ChromaDB再構築
```bash
rm -rf chroma_db/
python3.11 -m src.services.vector_db.build_unified_vector_index
```

---

## 関連ドキュメント

- [README.md](../README.md) - プロジェクト概要
- [refactoring_plan.md](./refactoring_plan.md) - リファクタリング計画
- [progress.md](../memory-bank/progress.md) - Phase進捗管理
- [MANUAL_TEST_PLAN.md](../tests/MANUAL_TEST_PLAN.md) - Phase 22テスト結果

---

## 変更履歴

| Date | Version | Description |
|------|---------|-------------|
| 2025-10-23 | 1.0 | Phase 22完了版 - 初版作成 |

---

**Maintained by**: Claude Code
**Last Review**: 2025-10-23
