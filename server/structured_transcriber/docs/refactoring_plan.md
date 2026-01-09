# リファクタリング計画

**作成日**: 2025-10-22
**目的**: archive_old_structure内の実装を新構造に移植し、完全に動作するアプリケーションを再構築

## 旧構造 → 新構造 マッピング

### 1. 共通ユーティリティ・モデル層

| 旧パス | 新パス | 説明 |
|--------|--------|------|
| `archive_old_structure/src/shared/` | `src/utils/` | 共通ユーティリティ関数 |
| `archive_old_structure/src/sqlite_db/` | `src/models/database.py` | データベースモデル |

### 2. コア機能層

| 旧パス | 新パス | 説明 |
|--------|--------|------|
| `archive_old_structure/src/transcription/` | `src/core/transcription.py` | 文字起こし（Gemini Audio API） |
| `archive_old_structure/src/pipeline/` | `src/core/pipeline.py` | 統合パイプライン（10ステップ） |
| `archive_old_structure/src/participants/` | `src/core/participants.py` | 参加者管理・話者推論 |
| `archive_old_structure/src/topics/` | `src/core/topics.py` | トピック/エンティティ抽出 |
| `archive_old_structure/src/vector_db/` | `src/core/vector_db.py` | Vector DB構築・管理 |
| `archive_old_structure/src/search/` | `src/core/search.py` | セマンティック検索・RAG |

### 3. 外部サービス連携層

| 旧パス | 新パス | 説明 |
|--------|--------|------|
| `archive_old_structure/src/monitoring/webhook_server.py` | `src/services/google_drive.py` | Google Drive Webhook |
| `archive_old_structure/src/monitoring/icloud_monitor.py` | `src/services/icloud.py` | iCloud Drive監視 |
| `archive_old_structure/src/shared/calendar_integration.py` | `src/services/calendar.py` | Google Calendar統合 |
| `archive_old_structure/src/file_management/` | `src/services/file_manager.py` | ファイル管理・リネーム |

### 4. API・Webアプリ層

| 旧パス | 新パス | 説明 |
|--------|--------|------|
| `archive_old_structure/src/webapp/api_server.py` | `src/api/server.py` | FastAPI バックエンド |
| `archive_old_structure/src/webapp/dashboard.py` | `src/api/dashboard.py` | Streamlit フロントエンド |

### 5. バッチ処理・スクリプト

| 旧パス | 新パス | 説明 |
|--------|--------|------|
| `archive_old_structure/src/batch/` | `scripts/batch/` | バッチ処理スクリプト |
| `archive_old_structure/scripts/` | `scripts/` | その他実行スクリプト |

## 移植順序

### Phase 1: 基盤層（共通機能）
1. ✅ プロジェクト構造作成
2. 共通ユーティリティ移植（`src/utils/`）
3. データベースモデル移植（`src/models/`）
4. 設定ファイル整備（`config/`）

### Phase 2: コア機能層
5. 文字起こし機能移植（`src/core/transcription.py`）
6. パイプライン機能移植（`src/core/pipeline.py`）
7. Vector DB機能移植（`src/core/vector_db.py`）
8. 検索機能移植（`src/core/search.py`）

### Phase 3: サービス連携層
9. Google Drive/Calendar連携移植（`src/services/`）
10. iCloud Drive監視移植（`src/services/`）
11. ファイル管理機能移植（`src/services/`）

### Phase 4: API・Webアプリ層
12. FastAPI サーバー移植（`src/api/server.py`）
13. Streamlit ダッシュボード移植（`src/api/dashboard.py`）

### Phase 5: スクリプト・テスト
14. スクリプト類の移植と更新（`scripts/`）
15. テストコード作成（`tests/`）

### Phase 6: 検証・ドキュメント
16. 動作テスト
17. ドキュメント更新

## 主要ファイル一覧（移植対象：41ファイル）

### 優先度: 高（コア機能）
- `src/transcription/structured_transcribe.py` (262行)
- `src/pipeline/integrated_pipeline.py` (主要パイプライン)
- `src/vector_db/build_unified_vector_index.py`
- `src/search/semantic_search.py`
- `src/search/rag_qa.py`

### 優先度: 中（サービス連携）
- `src/monitoring/webhook_server.py`
- `src/monitoring/icloud_monitor.py`
- `src/shared/calendar_integration.py`
- `src/file_management/cloud_file_manager.py`

### 優先度: 低（補助機能）
- `src/batch/` 配下のスクリプト
- `src/webapp/` 配下のWebアプリ

## 依存関係

### Python パッケージ
- `google-generativeai` (Gemini API)
- `google-auth`, `google-api-python-client` (Google OAuth)
- `chromadb` (Vector DB)
- `fastapi`, `uvicorn` (API Server)
- `streamlit` (Dashboard)
- `watchdog` (iCloud監視)

### 外部サービス
- Gemini API (文字起こし・LLM処理)
- Google Drive API (Webhook)
- Google Calendar API (参加者情報)
- ChromaDB (Vector Database)

## 注意事項

1. **インポートパスの変更**: 全てのインポート文を新構造に合わせて修正
2. **環境変数の継承**: `.env`ファイルの設定を確認
3. **データベースパス**: SQLite/ChromaDBのパスを新構造に合わせて変更
4. **相対パス問題**: スクリプト実行時のパス解決を確認

## 成功基準

- [ ] 音声ファイルアップロード → 文字起こし → Enhanced JSON生成が動作
- [ ] Vector DB自動構築が動作
- [ ] セマンティック検索・RAG Q&Aが動作
- [ ] Web UIからの検索・閲覧が動作
- [ ] Google Drive/iCloud Drive監視が動作
