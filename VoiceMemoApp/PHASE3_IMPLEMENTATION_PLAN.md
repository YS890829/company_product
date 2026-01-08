# Phase 3 実装プラン: 文字起こし機能

**作成日**: 2026-01-09
**ステータス**: 実装準備完了

---

## 1. 概要

Gemini APIを使用した音声文字起こし機能を実装する。録音完了後、Google File APIにアップロードし、**Gemini 2.5 Flash** で文字起こしを行い、結果をSwiftDataに保存する。

### 1.1 使用モデル

| モデル | 理由 |
|--------|------|
| **Gemini 2.5 Flash** | 高精度な文字起こし・構造化が可能 |

### 1.2 無料枠の詳細（2026年1月時点）

| モデル | RPM | TPM | RPD（リクエスト/日） |
|--------|-----|-----|---------------------|
| Gemini 2.5 Flash-Lite | 15 | 250,000 | 1,000 |
| **Gemini 2.5 Flash** | **10** | 250,000 | **250** |
| Gemini 2.5 Pro | 5 | 250,000 | 100 |

### 1.3 2時間音声の処理

| 項目 | 値 |
|------|-----|
| 最大音声長 | 9.5時間/プロンプト |
| 2時間の音声 | 230,400トークン（制限内） |
| 必要リクエスト数 | 3リクエスト/音声（アップロード+文字起こし+構造化） |
| 1日処理可能数 | **83件/日**（Flash使用時） |

### 1.4 営業チーム対応可否（個人APIキー前提）

| シナリオ | 必要リクエスト/人 | 対応可否 |
|---------|-----------------|---------|
| 1人 × 3件/日 | 9 | ✅ 余裕あり |
| 1人 × 10件/日 | 30 | ✅ 対応可能 |
| 1人 × 30件/日 | 90 | ⚠️ 制限に近い |

※ 各営業マンが個別のAPIキーを使用する想定

---

## 2. 前提条件

- Phase 1・2 完了済み（録音・保存・一覧表示が動作）
- Recording.swiftにPhase3用フィールド追加済み（transcriptText, status等）
- KeychainServiceでAPIキー管理済み

---

## 3. 実装ステージ

### ステージ A: TranscriptionService 基盤

**新規作成ファイル:**

| ファイル | 内容 |
|---------|------|
| `TranscriptionError.swift` | エラー定義 |
| `TranscriptionModels.swift` | APIレスポンスモデル |
| `TranscriptionService.swift` | サービス基盤（actor、スタブメソッド） |

**完了条件:** ビルド成功

---

### ステージ B: Google File API 連携

**修正ファイル:**

| ファイル | 変更内容 |
|---------|---------|
| `TranscriptionService.swift` | `uploadToFileAPI(audioURL:)` 実装 |

**実装内容:**
- multipart/form-data でm4aファイルをアップロード
- fileUri を返却

**完了条件:** ビルド成功

---

### ステージ C: Gemini API 文字起こし

**修正ファイル:**

| ファイル | 変更内容 |
|---------|---------|
| `TranscriptionService.swift` | `callGeminiAPI(fileUri:)` 実装、`transcribe(recording:)` 統合 |

**実装内容:**
- **Gemini 2.5 Flash** 呼び出し（`gemini-2.5-flash`）
- JSON形式で結果取得（summary, keyPoints, actionItems, fullTranscript）
- Recording更新メソッド

**完了条件:** ビルド成功

---

### ステージ D: UI 統合

**新規作成ファイル:**

| ファイル | 内容 |
|---------|------|
| `RecordingDetailView.swift` | 詳細画面（要約・重要ポイント・アクションアイテム・全文表示） |

**修正ファイル:**

| ファイル | 変更内容 |
|---------|---------|
| `ContentView.swift` | ステータス表示追加、詳細画面への遷移、文字起こし開始ボタン |

**完了条件:** ビルド成功

---

### ステージ E: エラーハンドリング

**修正ファイル:**

| ファイル | 変更内容 |
|---------|---------|
| `TranscriptionService.swift` | リトライロジック追加（指数バックオフ） |
| `ContentView.swift` | エラーステータス表示・リトライボタン |
| `RecordingDetailView.swift` | エラー時の表示対応 |

**完了条件:** ビルド成功、全フロー動作確認

---

## 4. 詳細実装内容

### 4.1 TranscriptionError.swift

```swift
enum TranscriptionError: LocalizedError {
    case noAPIKey
    case invalidAPIKey
    case networkError(underlying: Error)
    case uploadFailed(statusCode: Int)
    case apiFailed(statusCode: Int, message: String)
    case quotaExceeded
    case audioFileNotFound
    case decodingFailed

    var errorDescription: String? {
        switch self {
        case .noAPIKey:
            return "APIキーが設定されていません"
        case .invalidAPIKey:
            return "APIキーが無効です"
        case .networkError:
            return "ネットワークエラーが発生しました"
        case .uploadFailed(let code):
            return "ファイルのアップロードに失敗しました（\(code)）"
        case .apiFailed(_, let message):
            return "API処理に失敗しました: \(message)"
        case .quotaExceeded:
            return "本日の無料枠を超えました。明日再度お試しください"
        case .audioFileNotFound:
            return "音声ファイルが見つかりません"
        case .decodingFailed:
            return "レスポンスの解析に失敗しました"
        }
    }
}
```

### 4.2 TranscriptionModels.swift

```swift
import Foundation

// MARK: - File API レスポンス
struct FileUploadResponse: Codable {
    let file: FileInfo

    struct FileInfo: Codable {
        let name: String
        let uri: String
    }
}

// MARK: - Gemini API レスポンス
struct GeminiResponse: Codable {
    let candidates: [Candidate]?
    let error: GeminiError?

    struct Candidate: Codable {
        let content: Content
    }

    struct Content: Codable {
        let parts: [Part]
    }

    struct Part: Codable {
        let text: String?
    }

    struct GeminiError: Codable {
        let code: Int
        let message: String
    }
}

// MARK: - 文字起こし結果
struct TranscriptResult: Codable {
    let summary: String
    let keyPoints: [String]
    let actionItems: [ActionItem]
    let fullTranscript: String

    struct ActionItem: Codable {
        let task: String
        let deadline: String?
    }
}
```

### 4.3 TranscriptionService.swift（主要構造）

```swift
import Foundation
import SwiftData

actor TranscriptionService {
    private let apiKey: String
    private let model = "gemini-2.5-flash"

    private let fileAPIBaseURL = "https://generativelanguage.googleapis.com/upload/v1beta/files"
    private let geminiAPIBaseURL = "https://generativelanguage.googleapis.com/v1beta/models"

    init() throws {
        guard let key = KeychainService.shared.getAPIKey(), !key.isEmpty else {
            throw TranscriptionError.noAPIKey
        }
        self.apiKey = key
    }

    /// メイン処理
    func transcribe(recording: Recording, modelContext: ModelContext) async throws {
        // 1. ステータス更新: uploading
        await updateStatus(recording, .uploading, modelContext: modelContext)

        // 2. File APIにアップロード
        let audioURL = StorageManager.shared.getFileURL(fileName: recording.audioFileName)
        let fileUri = try await uploadToFileAPI(audioURL: audioURL)

        // 3. ステータス更新: processing
        await updateStatus(recording, .processing, modelContext: modelContext)

        // 4. Gemini APIで文字起こし
        let result = try await callGeminiAPI(fileUri: fileUri)

        // 5. 結果を保存
        await saveResult(recording, result, modelContext: modelContext)

        // 6. (オプション) File APIのファイルを削除
        try? await deleteFromFileAPI(fileUri: fileUri)
    }

    private func uploadToFileAPI(audioURL: URL) async throws -> String
    private func callGeminiAPI(fileUri: String) async throws -> TranscriptResult
    private func deleteFromFileAPI(fileUri: String) async throws
    private func updateStatus(_ recording: Recording, _ status: Recording.Status, modelContext: ModelContext) async
    private func saveResult(_ recording: Recording, _ result: TranscriptResult, modelContext: ModelContext) async
}
```

### 4.4 RecordingDetailView.swift

- 要約セクション
- 重要ポイントセクション（リスト表示）
- アクションアイテムセクション（チェックリスト風）
- 全文セクション（折りたたみ可能）
- ステータス表示（処理中/エラー時）

### 4.5 ContentView.swift 変更点

- RecordingRowにステータスアイコン追加
- 詳細画面へのNavigationLink
- 「文字起こし開始」ボタン（pending状態の録音用）
- エラー時リトライボタン

---

## 5. API仕様

### 5.1 Google File API（アップロード）

```http
POST https://generativelanguage.googleapis.com/upload/v1beta/files?key={API_KEY}
Content-Type: multipart/form-data

--boundary
Content-Disposition: form-data; name="metadata"
Content-Type: application/json

{"file": {"displayName": "recording.m4a"}}
--boundary
Content-Disposition: form-data; name="file"; filename="recording.m4a"
Content-Type: audio/mp4

(binary audio data)
--boundary--
```

### 5.2 Gemini API（文字起こし）

```http
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}
Content-Type: application/json

{
  "contents": [{
    "parts": [
      {"fileData": {"mimeType": "audio/mp4", "fileUri": "..."}},
      {"text": "この音声を文字起こしして、以下のJSON形式で出力..."}
    ]
  }],
  "generationConfig": {
    "responseMimeType": "application/json"
  }
}
```

---

## 6. ファイル構成（Phase 3 完了後）

```
VoiceMemoApp/
├── VoiceMemoAppApp.swift
├── ContentView.swift              # 修正
├── RecordingView.swift
├── RecordingDetailView.swift      # 新規
├── SettingsView.swift
├── Recording.swift
├── AudioManager.swift
├── StorageManager.swift
├── KeychainService.swift
├── TranscriptionService.swift     # 新規
├── TranscriptionError.swift       # 新規
├── TranscriptionModels.swift      # 新規
└── VoiceMemo.swift
```

---

## 7. 検証方法

### 7.1 ビルド確認（各ステージ完了時）

```bash
cd /Users/test/Desktop/simple_voicememo_iphoneapp/VoiceMemoApp
xcodegen generate && xcodebuild -project VoiceMemoApp.xcodeproj \
  -scheme VoiceMemoApp \
  -destination 'platform=iOS Simulator,name=iPhone 16' \
  -derivedDataPath ./build build
```

### 7.2 動作確認（Phase 3 完了時）

1. 設定画面でAPIキーを入力
2. 録音を作成
3. 一覧画面で「文字起こし開始」をタップ
4. ステータスが pending → uploading → processing → completed に変化
5. 詳細画面で結果が表示される
6. エラー時にエラーメッセージが表示される

---

## 8. 重要な制約

1. **既存の録音・保存機能を壊さない**
2. **各ステージ完了後にビルド確認**
3. **APIキーをログに出力しない**

---

## 9. 完了条件

- [ ] TranscriptionService が File API にアップロードできる
- [ ] Gemini 2.5 Flash-Lite で文字起こし結果を取得できる
- [ ] Recording に結果が保存される
- [ ] 一覧画面でステータスが表示される
- [ ] 詳細画面で結果が閲覧できる
- [ ] エラー時にリトライまたはエラー表示される
- [ ] ビルドエラーがない

---

## 10. 参考情報

### 10.1 公式ドキュメント

| リソース | URL |
|---------|-----|
| Gemini API | https://ai.google.dev/docs |
| Google AI Studio | https://aistudio.google.com/ |
| File API | https://ai.google.dev/api/files |
| Rate Limits | https://ai.google.dev/gemini-api/docs/rate-limits |

### 10.2 APIキー取得手順

1. https://aistudio.google.com/ にアクセス
2. Googleアカウントでログイン
3. 左メニュー「Get API Key」をクリック
4. 「Create API Key」をクリック
5. 表示されたキー（AIzaSy...）をコピー
6. アプリの設定画面に貼り付け

---

**更新履歴:**
- 2026-01-09: 初版作成、Gemini 2.5 Flash採用決定
