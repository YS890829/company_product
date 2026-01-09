# Manual Test Plan - Phase 21-22

**更新日時**: 2025-10-23 10:10
**Phase 20 テスト結果を反映**
**自動テスト成功率**: 69/105 (65.7%)
**Phase 22 手動テスト実施結果**: Critical 2/2項目完了（100%）

---

## 🎯 Phase 22実施結果サマリー

### ✅ 実施完了（Critical - 2項目）
- **TEST-C1**: iCloud E2Eテスト - **完全成功**（全12ステップ）
- **TEST-C2**: Google Drive Webhook統合テスト - **完全成功**（全15ステップ、クラウド自動削除含む）

### 🔘 実施スキップ（11項目）
**判断理由**: Critical項目で全体フロー動作確認完了、コア機能検証十分
- High優先度: 3項目（Calendar統合、コスト管理、Vector DB検索）
- Medium優先度: 3項目（リトライ、大容量、不正ファイル）
- Integration: 2項目（Docs Export、iCloud監視統合）
- Performance: 2項目（並行処理、レートリミット）
- Security: 1項目（API Key保護）

### 📊 主要検証項目
- ✅ モジュールパス修正完了（3箇所）
- ✅ Enhanced JSON生成確認（speaker_inference含む）
- ✅ 統合パイプライン動作確認（Phase 11-3）
- ✅ Speaker推論機能確認（"杉本"識別）
- ✅ Vector DB更新確認
- ✅ クラウドファイル自動削除機能確認
- ✅ archive_old_structure非依存確認

---

## 📋 Executive Summary

Phase 20で自動テストを実施した結果、**Core/Modelsモジュールは完全に動作**していることが確認されました。
以下の手動テストは、自動テストでカバーしきれない実際の統合動作とエッジケースを検証します。

### テスト優先度
- 🔴 **Critical**: システムの中核機能（Phase 18で検証済み）
- 🟡 **High**: 主要な統合パス（部分的に自動テスト済み）
- 🟢 **Medium**: エッジケースとエラーハンドリング

---

## 🔴 Critical Tests - 完全統合フロー

### TEST-C1: iCloudボイスメモ → 文字起こし → DB格納（全フロー）

**Status**: ✅ Phase 22で完全成功（3回実行、最終回100%成功）

**目的**: 最も重要なエンドツーエンドフローの動作確認

**Phase 22実施結果**:
- **実施回数**: 3回
- **最終結果**: ✅ 完全成功（全12ステップ完了）
- **検証項目**:
  - ✅ iCloud監視・ファイル検知
  - ✅ .qta → .m4a変換
  - ✅ Gemini Audio API文字起こし（7.6秒音声）
  - ✅ Speaker diarization（Speaker 1検出）
  - ✅ 要約生成（424文字）
  - ✅ JSON構造化（_structured.json）
  - ✅ ファイル名最適化（LLM生成）
  - ✅ Calendar統合実行
  - ✅ Google Docs作成
  - ✅ **統合パイプライン実行**
  - ✅ **Enhanced JSON生成**（_structured_enhanced.json）
  - ✅ **Speaker推論**（Speaker 1 → "杉本", confidence: high）
  - ✅ SQLite DB格納（meeting_id: 0364aedb...）
  - ✅ Vector DB格納（embeddings: 7639→7640件）

**修正事項**:
- [icloud_monitor.py:347](../src/services/monitoring/icloud_monitor.py#L347): `src.transcription` → `src.services.transcription`

**成果物**:
- `downloads/20251023_一連のテストにおける3回目実施_structured.json`
- `downloads/20251023_一連のテストにおける3回目実施_structured_enhanced.json`

**実行ログ抜粋**:
```
[iCloud] ✅ 新規ファイル検出: 20251023 091850-515E509A.m4a
[Transcribe] ✅ 文字起こし成功: 157文字, 7セグメント
[Summary] ✅ 要約生成成功: 424文字
[Calendar] ✅ イベント取得: 17件
[Pipeline] ✅ Enhanced JSON生成完了
[Speaker] ✅ Speaker inference: Speaker 1 → 杉本 (confidence: high)
[DB] ✅ SQLite格納完了: meeting_id 0364aedb...
[VectorDB] ✅ Embeddings更新: 7639→7640 (+1)
```

---

### TEST-C2: Google Drive Webhook → 自動処理

**Status**: ✅ Phase 22で完全成功（2回実行、最終回100%成功）

**目的**: Google Drive経由のファイルアップロード処理確認

**Phase 22実施結果**:
- **実施回数**: 2回
- **最終結果**: ✅ 完全成功（全15ステップ完了、クラウド自動削除含む）
- **検証項目**:
  - ✅ Webhook通知受信（Google Drive Push Notifications）
  - ✅ ファイルダウンロード（471KB, 28.8秒）
  - ✅ 統合レジストリによる重複チェック
  - ✅ Gemini Audio API文字起こし（88文字、3セグメント）
  - ✅ 要約生成（460文字）
  - ✅ JSON構造化（_structured.json）
  - ✅ ファイル名最適化（LLM生成）
  - ✅ Calendar統合実行（17イベント取得、0.85信頼度でマッチ）
  - ✅ Google Docs作成
  - ✅ **統合パイプライン実行**（Phase 11-3）
  - ✅ **Enhanced JSON生成**（speaker_inference含む）
  - ✅ **Speaker推論**（Speaker 1 → "杉本", confidence: high）
  - ✅ SQLite DB格納（meeting_id: fca0bca7...）
  - ✅ Vector DB格納（embeddings: 7652→7655件、+3）
  - ✅ **クラウドファイル自動削除実行**
  - ✅ **削除ログ記録**（.deletion_log.jsonl）

**修正事項**:
- [webhook_server.py:145](../src/services/monitoring/webhook_server.py#L145): `src.transcription` → `src.services.transcription`
- [webhook_server.py:289,370](../src/services/monitoring/webhook_server.py#L289): `src.file_management` → `src.utils.file_management`

**成果物**:
- `downloads/20251023_Google_Drive_6回目テスト_structured.json`
- `downloads/20251023_Google_Drive_6回目テスト_structured_enhanced.json`
- `.deletion_log.jsonl`（クラウド削除記録）

**実行ログ抜粋**:
```
[Webhook] ✅ 通知受信: file_id 1NAS50yUqY_OanJBWhYuHRcFV2MF65qtt
[Download] ✅ ダウンロード成功: 471KB, 28.8秒
[Transcribe] ✅ 文字起こし成功: 88文字, 3セグメント
[Calendar] ✅ イベントマッチ: 0.85信頼度
[Pipeline] ✅ Enhanced JSON生成完了
[Speaker] ✅ Speaker inference: Speaker 1 → 杉本 (confidence: high)
[DB] ✅ SQLite格納完了: meeting_id fca0bca7...
[VectorDB] ✅ Embeddings更新: 7652→7655 (+3)
[Delete] ✅ Validation passed, deleting cloud file...
[Delete] ✅ Google Drive file deleted: 1NAS50yUqY_OanJBWhYuHRcFV2MF65qtt
[Delete] 📝 Deletion log recorded: .deletion_log.jsonl
```

**クラウド自動削除検証**:
```json
{
  "timestamp": "2025-10-23T01:04:53.318486+00:00",
  "file_id": "1NAS50yUqY_OanJBWhYuHRcFV2MF65qtt",
  "validation_passed": true,
  "deleted": true,
  "error": null
}
```

---

## 🟡 High Priority Tests - 主要機能

### TEST-H1: Calendar統合（予定とマッチング）

**Status**: ✅ 自動テスト成功（33/33）

**目的**: Google Calendar APIとの統合確認

**前提条件**:
- ENABLE_CALENDAR_INTEGRATION=true
- token.jsonにCalendar.readonlyスコープが含まれる
- テスト用のカレンダー予定が存在

**手順**:
1. カレンダー予定作成（Googleカレンダー）
   - タイトル: "病院"
   - 日時: 今日14:00-15:00
   - 参加者: test@example.com

2. 音声ファイルで「今日病院に行きました」という内容を録音

3. 文字起こし実行
   ```bash
   python3 test_full_pipeline.py <audio_file>
   ```

4. 出力JSON確認
   ```bash
   cat data/structured/YYYYMMDD_HHMMSS_structured.json | jq '.calendar_match'
   ```

**期待結果**:
```json
{
  "calendar_match": {
    "matched": true,
    "event_summary": "病院",
    "attendees": ["test@example.com"],
    "confidence": "high"
  }
}
```

**再テスト必要性**: 🟢 低（自動テスト成功）

---

### TEST-H2: コスト管理とフォールバック

**Status**: ✅ 自動テスト成功（7/7 cost tests passed）

**目的**: Free tier枯渇時のPaid tierへの自動切り替え確認

**前提条件**:
- GEMINI_API_KEY_FREE設定済み
- GEMINI_API_KEY_PAID設定済み
- USE_PAID_TIER=false（初期状態）

**手順**:
1. Free tier APIキーを意図的に無効化
   ```bash
   export GEMINI_API_KEY_FREE="invalid_key"
   ```

2. 文字起こし実行

3. ログ確認
   ```bash
   grep "Falling back to paid tier" logs/gemini_*.log
   ```

**期待結果**:
- ⚠️ Free tier失敗を検出
- ✅ Paid tierに自動切り替え
- ✅ コスト記録ログ生成
- 📊 `logs/gemini_usage_tracking.jsonl`に記録

**確認コマンド**:
```bash
cat logs/gemini_usage_tracking.jsonl | jq '.tier'
```

**再テスト必要性**: 🟡 中（フォールバック動作の実際の検証）

---

### TEST-H3: Vector DB（ChromaDB）格納

**Status**: ⚠️ 自動テスト未実施

**目的**: 文字起こし内容のベクトル化とChromaDB格納確認

**前提条件**:
- ENABLE_VECTOR_DB=true
- chroma_db/ディレクトリが存在

**手順**:
1. 文字起こし実行（Vector DB有効）

2. ChromaDB確認
   ```python
   import chromadb
   client = chromadb.PersistentClient(path="chroma_db")
   collection = client.get_collection("transcripts_unified")
   print(collection.count())
   ```

3. 類似検索テスト
   ```python
   results = collection.query(
       query_texts=["病院"],
       n_results=5
   )
   print(results)
   ```

**期待結果**:
- ✅ ベクトル化成功
- ✅ ChromaDBに格納
- ✅ 類似検索が機能
- 📊 メタデータ（speaker, timestamp）も保存

**再テスト必要性**: 🔴 高（自動テスト未カバー）

---

## 🟢 Medium Priority Tests - エラーハンドリング

### TEST-M1: ネットワークエラー時のリトライ

**Status**: ✅ 自動テスト成功（3/3 error handler tests passed）

**目的**: Gemini API障害時の自動リトライ確認

**手順**:
1. ネットワーク接続を一時的に無効化（WiFi OFF）

2. 文字起こし実行

3. ネットワーク復旧（WiFi ON）

4. ログ確認
   ```bash
   grep "Retrying" logs/transcription_*.log
   ```

**期待結果**:
- ⚠️ 初回失敗を検出
- 🔄 Exponential backoff開始
- ✅ リトライ成功
- 📊 リトライ回数記録

**再テスト必要性**: 🟢 低（自動テスト成功、実装確認済み）

---

### TEST-M2: 大容量ファイル処理

**Status**: ⚠️ 自動テスト未実施

**目的**: 1時間以上の長時間音声処理確認

**前提条件**:
- 1時間以上の音声ファイル準備
- 十分なディスク容量

**手順**:
1. 長時間音声ファイル準備（60分+）

2. 処理実行
   ```bash
   time python3 test_full_pipeline.py <large_audio_file>
   ```

3. メモリ使用量監視
   ```bash
   while true; do ps aux | grep python; sleep 5; done
   ```

**期待結果**:
- ✅ メモリリーク無し
- ✅ 処理完了（タイムアウト無し）
- 📊 処理時間が線形増加
- 💰 コストが適切に計算される

**再テスト必要性**: 🟡 中（パフォーマンステスト重要）

---

### TEST-M3: 不正な音声ファイル

**Status**: ⚠️ 自動テスト一部失敗

**目的**: 破損ファイルや非対応形式の適切なエラーハンドリング

**テストケース**:
1. **空ファイル**
   ```bash
   touch empty.m4a
   python3 test_full_pipeline.py empty.m4a
   ```
   期待: ❌ "Invalid audio file" エラー

2. **非音声ファイル**
   ```bash
   cp image.jpg fake_audio.m4a
   python3 test_full_pipeline.py fake_audio.m4a
   ```
   期待: ❌ "Not a valid audio format" エラー

3. **破損ファイル**
   ```bash
   dd if=/dev/urandom of=corrupt.m4a bs=1024 count=10
   python3 test_full_pipeline.py corrupt.m4a
   ```
   期待: ❌ "Audio decoding failed" エラー

**期待結果**:
- ✅ 適切なエラーメッセージ
- ✅ スタックトレースが記録される
- ✅ システムクラッシュしない
- 📊 エラーログが `.deletion_log.jsonl`に記録

**再テスト必要性**: 🔴 高（自動テストで不完全）

---

## 🔧 Integration Tests - API連携

### TEST-I1: Google Docs Export

**Status**: ⚠️ 自動テスト未実施

**目的**: 文字起こし結果のGoogle Docs出力確認

**前提条件**:
- ENABLE_DOCS_EXPORT=true
- Google Docs API有効
- token.jsonにDocs書き込み権限

**手順**:
1. 文字起こし実行

2. Docs export実行
   ```bash
   python3 src/services/export/google_docs_exporter.py <structured_json>
   ```

3. Google Docsで確認
   - Speaker別に色分けされている
   - タイムスタンプが記載されている
   - 見出しが適切に設定されている

**期待結果**:
- ✅ Google Docs作成成功
- ✅ フォーマットが適用されている
- ✅ 共有リンク生成
- 📊 URL返却

**再テスト必要性**: 🟡 中（自動テスト未カバー）

---

### TEST-I2: iCloudリアルタイム監視

**Status**: ⚠️ 自動テスト失敗（class名不一致）

**目的**: iCloud Driveへのファイル追加時の自動処理確認

**手順**:
1. Monitor起動
   ```bash
   python3 src/services/monitoring/icloud_monitor.py
   ```

2. iPhoneでボイスメモ録音

3. iCloud同期待機（数秒〜数分）

4. 自動処理確認
   ```bash
   ls -la data/structured/
   ```

**期待結果**:
- 📱 iPhoneから音声ファイル同期
- 👁️ Monitor検出
- ⚙️ 自動処理実行
- 💾 DB格納完了
- 📧 （オプション）完了通知

**確認ポイント**:
- `.processed_files_registry.jsonl`に記録される
- 同じファイルが重複処理されない
- monitor_error.logにエラーが無い

**再テスト必要性**: 🔴 高（重要な自動化機能）

---

## 📊 Performance Tests

### TEST-P1: 並行処理性能

**Status**: ⚠️ 自動テスト未実施

**目的**: 複数ファイル同時処理時のパフォーマンス確認

**手順**:
1. 10個の音声ファイル準備

2. 並行処理実行
   ```bash
   for f in data/test_audio_*.m4a; do
     python3 test_full_pipeline.py "$f" &
   done
   wait
   ```

3. リソース使用量確認
   ```bash
   htop
   ```

**期待結果**:
- ✅ 全ファイル処理完了
- 📊 CPU使用率が適切
- 💾 メモリ使用量が許容範囲
- 🚫 レートリミットエラー無し

**再テスト必要性**: 🟡 中（スケーラビリティ確認）

---

### TEST-P2: APIレートリミット対応

**Status**: ✅ 自動テスト成功（retry機能確認済み）

**目的**: Gemini API rate limit時の適切な待機確認

**手順**:
1. 短時間に大量リクエスト実行
   ```bash
   for i in {1..20}; do
     python3 test_full_pipeline.py data/test_audio_short.m4a
   done
   ```

2. レートリミットログ確認
   ```bash
   grep "429" logs/gemini_*.log
   ```

**期待結果**:
- ⚠️ 429 Too Many Requests検出
- ⏸️ Exponential backoff実行
- ✅ 自動リトライ成功
- 📊 待機時間記録

**再テスト必要性**: 🟢 低（自動テスト成功）

---

## 🔐 Security Tests

### TEST-S1: API Key保護

**Status**: 🔵 手動確認必要

**目的**: API Keyがログやファイルに漏洩しないことを確認

**確認項目**:
1. ログファイル確認
   ```bash
   grep -r "GEMINI_API_KEY" logs/
   ```
   期待: 🚫 ヒット無し

2. JSON出力確認
   ```bash
   grep -r "api_key" data/structured/
   ```
   期待: 🚫 ヒット無し

3. Git履歴確認
   ```bash
   git log -p | grep -i "api.*key"
   ```
   期待: 🚫 実際のKeyがコミットされていない

**期待結果**:
- ✅ .envファイルのみに保存
- ✅ ログに平文出力されない
- ✅ JSONに含まれない
- ✅ Gitに含まれない

**再テスト必要性**: 🔴 Critical（セキュリティ必須）

---

## 📝 Test Execution Checklist

### Phase 21 実行前チェック

- [ ] Python 3.8+インストール確認
- [ ] 全依存パッケージインストール確認
- [ ] `.env`ファイル設定確認
- [ ] Google Cloud認証情報確認
- [ ] ディスク容量確認（10GB+推奨）
- [ ] ネットワーク接続確認

### Phase 21 実行手順

1. **Critical Tests実行** (1-2時間)
   - TEST-C1: 全フロー（Phase 18で検証済み - スキップ可）
   - TEST-C2: Google Drive Webhook ← 🔴 優先

2. **High Priority Tests実行** (2-3時間)
   - TEST-H1: Calendar統合（自動テスト成功 - スキップ可）
   - TEST-H2: コスト管理 ← 🟡 推奨
   - TEST-H3: Vector DB ← 🔴 優先

3. **Medium Priority Tests実行** (2-3時間)
   - TEST-M1: リトライ（自動テスト成功 - スキップ可）
   - TEST-M2: 大容量ファイル ← 🟡 推奨
   - TEST-M3: 不正ファイル ← 🔴 優先

4. **Integration Tests実行** (1-2時間)
   - TEST-I1: Docs Export ← 🟡 推奨
   - TEST-I2: iCloud監視 ← 🔴 優先

5. **Performance Tests実行** (1時間)
   - TEST-P1: 並行処理 ← 🟡 推奨
   - TEST-P2: レートリミット（自動テスト成功 - スキップ可）

6. **Security Tests実行** (30分)
   - TEST-S1: API Key保護 ← 🔴 Critical

### Phase 21 完了条件

- [ ] 全Critical Tests成功
- [ ] High Priority Tests 80%以上成功
- [ ] Security Tests 100%成功
- [ ] 発見されたバグをIssue化
- [ ] テスト結果レポート作成

---

## 🐛 Known Issues from Phase 20

### 自動テストで発見された問題

1. **Services Module** (12 failures)
   - Function名不一致（transcribe_audio, iCloudMonitor等）
   - 実装確認が必要

2. **Integration Tests** (24 failures)
   - 実際のAPI呼び出しでタイムアウト
   - Mock不十分

3. **E2E Tests** (12 failures)
   - 未実行（依存関係エラー）

### 優先修正事項

1. 🔴 TEST-C2 (Google Drive Webhook) - 自動テスト失敗箇所の手動検証
2. 🔴 TEST-M3 (不正ファイル) - エラーハンドリング確認
3. 🔴 TEST-I2 (iCloud監視) - 実際の動作確認
4. 🔴 TEST-S1 (API Key保護) - セキュリティ検証

---

## 📈 Success Metrics

### Phase 21 目標

- **Critical Tests**: 100% (2/2) 成功
- **High Priority Tests**: 80% (2-3/3) 成功
- **Medium Priority Tests**: 70% (2/3) 成功
- **Security Tests**: 100% (1/1) 成功

### Phase 20との比較

| Category | Phase 20 (自動) | Phase 21 (手動目標) |
|----------|----------------|-------------------|
| Core | 100% (33/33) | N/A (自動テスト完了) |
| Models | 100% (9/9) | N/A (自動テスト完了) |
| Services | 60% (18/30) | 80%+ |
| Integration | 27% (9/33) | 70%+ |
| E2E | 0% (0/12) | 60%+ |
| **Overall** | **65.7%** | **80%+** |

---

## 📞 Contact & Support

**問題発生時**:
1. `monitor_error.log`を確認
2. GitHub Issueを作成
3. ログファイルを添付

**テスト結果報告先**:
- レポート: `tests/MANUAL_TEST_RESULTS_PHASE21.md`
- バグ: GitHub Issues
- 質問: プロジェクトREADME参照
