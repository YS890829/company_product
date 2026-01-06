# ローカル完結版 詳細設計書

**作成日**: 2026-01-06
**バージョン**: 1.0
**目的**: サーバーインフラ不要のボイスメモ文字起こしアプリ設計

---

## 1. 概要

### 1.1 コンセプト

| 項目 | 内容 |
|-----|------|
| **アーキテクチャ** | サーバーレス（ローカル完結） |
| **文字起こし** | Gemini API 直接呼び出し |
| **APIキー管理** | ユーザー個別（各自のAPIキー使用） |
| **データ保存** | 完全ローカル（Core Data + FileManager） |
| **月額コスト** | **$0**（Gemini無料枠活用） |

### 1.2 クラウド版との比較

| 項目 | クラウド版（v4ハイブリッド） | ローカル完結版 |
|-----|-------------------------|--------------|
| サーバーコスト | $31/月 | **$0/月** |
| Gemini API | $0（無料枠） | $0（無料枠） |
| 複雑さ | Cloud Run + Eventarc設定必要 | **シンプル** |
| 複数デバイス同期 | 可能 | 不可（iCloud使用で可能） |
| オフライン対応 | 部分的 | 録音のみ可能 |

### 1.3 対象ユーザー

- 技術リテラシーが比較的高い（APIキー取得可能）
- コスト最優先
- 単一デバイスでの利用が中心
- 企業内営業チーム（31名→68名想定）

---

## 2. システムアーキテクチャ

### 2.1 全体構成図

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ローカル完結アーキテクチャ                                │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         iPhone App                                   │   │
│  │                                                                      │   │
│  │   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐           │   │
│  │   │   録音機能   │   │  設定画面    │   │  履歴一覧    │           │   │
│  │   │ AVFoundation │   │  APIキー入力 │   │  結果表示    │           │   │
│  │   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘           │   │
│  │          │                  │                  │                    │   │
│  │          ▼                  ▼                  ▼                    │   │
│  │   ┌─────────────────────────────────────────────────────────────┐  │   │
│  │   │                   TranscriptionService                       │  │   │
│  │   │                                                              │  │   │
│  │   │  1. File APIアップロード  →  2. Gemini API呼出  →  3. 保存  │  │   │
│  │   └─────────────────────────────────────────────────────────────┘  │   │
│  │          │                                              │           │   │
│  │          ▼                                              ▼           │   │
│  │   ┌──────────────┐                              ┌──────────────┐   │   │
│  │   │ FileManager  │                              │  Core Data   │   │   │
│  │   │ (音声保存)   │                              │ (結果保存)   │   │   │
│  │   └──────────────┘                              └──────────────┘   │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                    │                               │
                    │ HTTPS                         │ HTTPS
                    ▼                               ▼
          ┌──────────────────┐            ┌──────────────────┐
          │ Google File API  │            │   Gemini API     │
          │                  │            │                  │
          │ • 一時アップロード│            │ • 文字起こし     │
          │ • 48h自動削除    │            │ • 1,500件/日無料 │
          │ • 無料           │            │                  │
          └──────────────────┘            └──────────────────┘
```

### 2.2 データフロー

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           データフロー詳細                                   │
└─────────────────────────────────────────────────────────────────────────────┘

[録音開始]
    │
    ▼
┌─────────────────┐
│ AVAudioRecorder │
│ • m4a (AAC)     │
│ • 44.1kHz       │
└────────┬────────┘
         │
         ▼
[録音完了]
         │
         ├─────────────────────────────────────────┐
         │                                         │
         ▼                                         ▼
┌─────────────────┐                      ┌─────────────────┐
│ FileManager     │                      │ Core Data       │
│                 │                      │                 │
│ Documents/      │                      │ Recording       │
│  └─recordings/  │                      │ • id            │
│     └─xxx.m4a   │                      │ • createdAt     │
└────────┬────────┘                      │ • audioFileName │
         │                               │ • status:pending│
         │                               └─────────────────┘
         │
         ▼
[文字起こし開始]
         │
         ▼
┌─────────────────┐      POST /upload
│ Google File API │◀─────────────────────
│                 │      multipart/form-data
│ files/{fileId}  │
└────────┬────────┘
         │
         │ file_uri
         ▼
┌─────────────────┐      POST /generateContent
│   Gemini API    │◀─────────────────────
│                 │      { fileData: { fileUri } }
│ gemini-1.5-flash│
└────────┬────────┘
         │
         │ transcript text
         ▼
┌─────────────────┐
│ Core Data       │
│                 │
│ Recording       │
│ • status:done   │
│ • transcriptText│
│ • transcriptJSON│
└─────────────────┘
         │
         ▼
[完了・UI更新]
```

---

## 3. 技術スタック

### 3.1 iPhoneアプリ

| レイヤー | 技術 | 備考 |
|---------|------|------|
| **UI** | SwiftUI | iOS 17+ |
| **録音** | AVFoundation | AVAudioRecorder |
| **永続化** | Core Data + SwiftData | iOS 17ならSwiftData推奨 |
| **ファイル** | FileManager | Documents配下に保存 |
| **ネットワーク** | URLSession | async/await |
| **セキュリティ** | Keychain | APIキー保存 |
| **バックグラウンド** | BGTaskScheduler | 長時間処理対応 |

### 3.2 外部API

| API | 用途 | エンドポイント |
|-----|------|---------------|
| **Google File API** | 音声ファイル一時保存 | `generativelanguage.googleapis.com/upload/v1beta/files` |
| **Gemini API** | 文字起こし | `generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent` |

### 3.3 依存ライブラリ

| ライブラリ | 用途 | 必須/任意 |
|-----------|------|----------|
| なし | - | - |

> **注**: 外部ライブラリ不要。標準フレームワークのみで実装可能。

---

## 4. データモデル

### 4.1 Core Data エンティティ

```swift
// Recording.swift
@Entity
class Recording {
    @Attribute(.unique) var id: UUID
    var createdAt: Date
    var title: String?

    // 音声ファイル
    var audioFileName: String           // "2026-01-06_143022.m4a"
    var duration: TimeInterval          // 秒
    var fileSize: Int64                 // バイト

    // 文字起こし結果
    var transcriptText: String?         // プレーンテキスト
    var transcriptJSON: Data?           // 構造化データ（JSON）

    // ステータス
    var status: TranscriptStatus        // pending/processing/completed/failed
    var errorMessage: String?           // エラー時のメッセージ

    // メタデータ
    var processedAt: Date?              // 処理完了日時
    var geminiFileUri: String?          // File APIのURI（処理中のみ使用）
}

enum TranscriptStatus: String, Codable {
    case pending      // 未処理
    case uploading    // File APIアップロード中
    case processing   // Gemini API処理中
    case completed    // 完了
    case failed       // 失敗
}
```

### 4.2 構造化データ（JSON）

```json
{
  "summary": "商談の要約テキスト...",
  "keyPoints": [
    "ポイント1",
    "ポイント2"
  ],
  "actionItems": [
    {
      "task": "見積書を送付",
      "deadline": "2026-01-10"
    }
  ],
  "participants": ["田中", "鈴木"],
  "fullTranscript": "完全な文字起こしテキスト..."
}
```

### 4.3 ファイル構成

```
Documents/
├── recordings/
│   ├── 2026-01-06_143022.m4a
│   ├── 2026-01-06_150000.m4a
│   └── ...
└── (Core Data SQLite files)
```

---

## 5. API仕様

### 5.1 Google File API

#### アップロード

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

#### レスポンス

```json
{
  "file": {
    "name": "files/abc123xyz",
    "displayName": "recording.m4a",
    "mimeType": "audio/mp4",
    "sizeBytes": "15000000",
    "createTime": "2026-01-06T14:30:22Z",
    "expirationTime": "2026-01-08T14:30:22Z",
    "uri": "https://generativelanguage.googleapis.com/v1beta/files/abc123xyz"
  }
}
```

#### ファイル削除（オプション）

```http
DELETE https://generativelanguage.googleapis.com/v1beta/files/{fileId}?key={API_KEY}
```

### 5.2 Gemini API

#### 文字起こしリクエスト

```http
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}
Content-Type: application/json

{
  "contents": [
    {
      "parts": [
        {
          "fileData": {
            "mimeType": "audio/mp4",
            "fileUri": "https://generativelanguage.googleapis.com/v1beta/files/abc123xyz"
          }
        },
        {
          "text": "この音声を文字起こしして、以下の形式でJSON出力してください：\n{\"summary\": \"要約\", \"keyPoints\": [\"ポイント\"], \"actionItems\": [{\"task\": \"タスク\", \"deadline\": \"期限\"}], \"fullTranscript\": \"全文\"}"
        }
      ]
    }
  ],
  "generationConfig": {
    "responseMimeType": "application/json"
  }
}
```

#### レスポンス

```json
{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "text": "{\"summary\": \"...\", \"keyPoints\": [...], ...}"
          }
        ]
      }
    }
  ]
}
```

### 5.3 API制限

| API | 無料枠制限 | 備考 |
|-----|-----------|------|
| **Google File API** | 20GB/プロジェクト | ファイルは48時間で自動削除 |
| **Gemini 1.5 Flash** | 1,500リクエスト/日 | 15 RPM |
| **Gemini 1.5 Pro** | 50リクエスト/日 | 2 RPM |

---

## 6. 処理フロー詳細

### 6.1 録音フロー

```swift
// RecordingViewModel.swift
class RecordingViewModel: ObservableObject {
    @Published var isRecording = false
    @Published var duration: TimeInterval = 0

    private var audioRecorder: AVAudioRecorder?
    private var timer: Timer?

    func startRecording() async throws {
        // 1. マイク権限確認
        guard await requestMicrophonePermission() else {
            throw RecordingError.permissionDenied
        }

        // 2. ファイルパス生成
        let fileName = generateFileName()  // "2026-01-06_143022.m4a"
        let fileURL = getDocumentsDirectory()
            .appendingPathComponent("recordings")
            .appendingPathComponent(fileName)

        // 3. 録音設定
        let settings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
            AVSampleRateKey: 44100,
            AVNumberOfChannelsKey: 1,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
        ]

        // 4. 録音開始
        audioRecorder = try AVAudioRecorder(url: fileURL, settings: settings)
        audioRecorder?.record()
        isRecording = true

        // 5. タイマー開始（UI更新用）
        startTimer()
    }

    func stopRecording() -> URL? {
        audioRecorder?.stop()
        isRecording = false
        stopTimer()
        return audioRecorder?.url
    }
}
```

### 6.2 文字起こしフロー

```swift
// TranscriptionService.swift
actor TranscriptionService {
    private let apiKey: String

    init() {
        self.apiKey = KeychainService.getAPIKey() ?? ""
    }

    /// メイン処理：録音→文字起こし→保存
    func transcribe(recording: Recording) async throws -> TranscriptResult {
        // 0. ステータス更新
        await updateStatus(recording, .uploading)

        // 1. File APIにアップロード
        let audioURL = getAudioFileURL(recording.audioFileName)
        let fileUri = try await uploadToFileAPI(audioURL: audioURL)

        // 2. ステータス更新
        await updateStatus(recording, .processing)

        // 3. Gemini APIで文字起こし
        let result = try await callGeminiAPI(fileUri: fileUri)

        // 4. 結果を保存
        await saveResult(recording, result)
        await updateStatus(recording, .completed)

        // 5. (オプション) File APIのファイルを削除
        try? await deleteFromFileAPI(fileUri: fileUri)

        return result
    }

    /// File APIアップロード
    private func uploadToFileAPI(audioURL: URL) async throws -> String {
        let boundary = UUID().uuidString
        var request = URLRequest(url: URL(string:
            "https://generativelanguage.googleapis.com/upload/v1beta/files?key=\(apiKey)")!)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)",
                        forHTTPHeaderField: "Content-Type")

        // multipart body構築
        var body = Data()

        // metadata part
        body.append("--\(boundary)\r\n")
        body.append("Content-Disposition: form-data; name=\"metadata\"\r\n")
        body.append("Content-Type: application/json\r\n\r\n")
        body.append("{\"file\": {\"displayName\": \"\(audioURL.lastPathComponent)\"}}\r\n")

        // file part
        body.append("--\(boundary)\r\n")
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(audioURL.lastPathComponent)\"\r\n")
        body.append("Content-Type: audio/mp4\r\n\r\n")
        body.append(try Data(contentsOf: audioURL))
        body.append("\r\n--\(boundary)--\r\n")

        request.httpBody = body

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw TranscriptionError.uploadFailed
        }

        let result = try JSONDecoder().decode(FileUploadResponse.self, from: data)
        return result.file.uri
    }

    /// Gemini API呼び出し
    private func callGeminiAPI(fileUri: String) async throws -> TranscriptResult {
        let url = URL(string:
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=\(apiKey)")!

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let prompt = """
        この音声を文字起こしして、以下のJSON形式で出力してください：
        {
          "summary": "会話の要約（200文字以内）",
          "keyPoints": ["重要ポイント1", "重要ポイント2", ...],
          "actionItems": [{"task": "タスク内容", "deadline": "期限（あれば）"}],
          "fullTranscript": "完全な文字起こし"
        }
        """

        let body: [String: Any] = [
            "contents": [
                [
                    "parts": [
                        ["fileData": ["mimeType": "audio/mp4", "fileUri": fileUri]],
                        ["text": prompt]
                    ]
                ]
            ],
            "generationConfig": [
                "responseMimeType": "application/json"
            ]
        ]

        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw TranscriptionError.apiFailed
        }

        let geminiResponse = try JSONDecoder().decode(GeminiResponse.self, from: data)
        let resultText = geminiResponse.candidates.first?.content.parts.first?.text ?? ""

        return try JSONDecoder().decode(TranscriptResult.self,
                                        from: resultText.data(using: .utf8)!)
    }
}
```

### 6.3 バックグラウンド処理

```swift
// BackgroundTaskManager.swift
class BackgroundTaskManager {
    static let shared = BackgroundTaskManager()

    func registerBackgroundTasks() {
        BGTaskScheduler.shared.register(
            forTaskWithIdentifier: "com.app.transcription",
            using: nil
        ) { task in
            self.handleTranscriptionTask(task as! BGProcessingTask)
        }
    }

    func scheduleTranscription(for recording: Recording) {
        let request = BGProcessingTaskRequest(identifier: "com.app.transcription")
        request.requiresNetworkConnectivity = true
        request.requiresExternalPower = false

        do {
            try BGTaskScheduler.shared.submit(request)
        } catch {
            print("Failed to schedule: \(error)")
        }
    }

    private func handleTranscriptionTask(_ task: BGProcessingTask) {
        task.expirationHandler = {
            // タスクがキャンセルされた場合の処理
        }

        Task {
            do {
                let pendingRecordings = try await fetchPendingRecordings()
                for recording in pendingRecordings {
                    try await TranscriptionService().transcribe(recording: recording)
                }
                task.setTaskCompleted(success: true)
            } catch {
                task.setTaskCompleted(success: false)
            }
        }
    }
}
```

---

## 7. UI設計

### 7.1 画面構成

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              画面遷移図                                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│   起動画面      │
│   (Splash)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     APIキー未設定時     ┌─────────────────┐
│   ホーム画面    │ ─────────────────────▶ │   設定画面      │
│   (録音一覧)    │                         │   (APIキー入力) │
└────────┬────────┘                         └─────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────────┐
│ 録音  │ │ 詳細画面  │
│ 画面  │ │ (結果表示)│
└───────┘ └───────────┘
```

### 7.2 ホーム画面（録音一覧）

```
┌─────────────────────────────────────┐
│  ボイスメモ                    ⚙️   │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 📝 商談メモ 2026/01/06      │   │
│  │    15:30  ⏱️ 45:23          │   │
│  │    ✅ 文字起こし完了         │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 📝 打ち合わせ 2026/01/06    │   │
│  │    10:00  ⏱️ 32:10          │   │
│  │    ⏳ 処理中...              │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 📝 朝会 2026/01/05          │   │
│  │    09:00  ⏱️ 12:45          │   │
│  │    ⚠️ 未処理（タップで開始） │   │
│  └─────────────────────────────┘   │
│                                     │
│                                     │
│         ┌───────────────┐          │
│         │   🎙️ 録音     │          │
│         └───────────────┘          │
│                                     │
└─────────────────────────────────────┘
```

### 7.3 録音画面

```
┌─────────────────────────────────────┐
│  ← 戻る              録音中         │
├─────────────────────────────────────┤
│                                     │
│                                     │
│                                     │
│              ◉                      │
│           録音中                    │
│                                     │
│           45:23                     │
│                                     │
│     ━━━━━━━━━━━━━━━━━━━━━━━━━      │
│     波形表示                        │
│                                     │
│                                     │
│                                     │
│         ┌───────────────┐          │
│         │   ⏹️ 停止     │          │
│         └───────────────┘          │
│                                     │
│  💡 録音中にアプリを閉じても        │
│     バックグラウンドで継続します     │
│                                     │
└─────────────────────────────────────┘
```

### 7.4 詳細画面（結果表示）

```
┌─────────────────────────────────────┐
│  ← 戻る        商談メモ        📤   │
├─────────────────────────────────────┤
│                                     │
│  📅 2026/01/06 15:30               │
│  ⏱️ 45分23秒                        │
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  📋 要約                            │
│  ───────                            │
│  本日の商談では、新規プロジェクト   │
│  の提案を行い、先方から前向きな     │
│  回答を得た。次回は詳細見積もりを   │
│  持参予定。                         │
│                                     │
│  🎯 重要ポイント                    │
│  ───────────                        │
│  • 予算規模: 500万円程度            │
│  • 決定者: 田中部長                 │
│  • 競合: A社が先行提案済み          │
│                                     │
│  ✅ アクションアイテム              │
│  ─────────────────                  │
│  □ 見積書作成（1/10まで）          │
│  □ 技術担当との打ち合わせ設定       │
│                                     │
│  📝 全文                      ▼     │
│  ───────                            │
│  (折りたたみ表示)                   │
│                                     │
└─────────────────────────────────────┘
```

### 7.5 設定画面

```
┌─────────────────────────────────────┐
│  ← 戻る              設定           │
├─────────────────────────────────────┤
│                                     │
│  Gemini API 設定                    │
│  ─────────────────────────────────  │
│                                     │
│  APIキー                            │
│  ┌─────────────────────────────┐   │
│  │ AIza...                     │   │
│  └─────────────────────────────┘   │
│                                     │
│  [APIキーの取得方法 ↗]              │
│                                     │
│  ┌─────────────────────────────┐   │
│  │       キーを検証            │   │
│  └─────────────────────────────┘   │
│                                     │
│  ステータス: ✅ 有効                │
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  💡 ヒント                          │
│  Google AI Studio で無料の          │
│  APIキーを取得できます。            │
│  1日1,500件まで無料で利用可能です。 │
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  データ管理                         │
│  ───────────                        │
│  • 保存データ: 156 MB               │
│  • 録音数: 23件                     │
│                                     │
│  [データをエクスポート]             │
│  [全データを削除]                   │
│                                     │
└─────────────────────────────────────┘
```

---

## 8. セキュリティ

### 8.1 APIキー管理

```swift
// KeychainService.swift
class KeychainService {
    private static let service = "com.app.voicememo"
    private static let account = "gemini_api_key"

    static func saveAPIKey(_ apiKey: String) throws {
        let data = apiKey.data(using: .utf8)!

        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        ]

        // 既存のキーを削除
        SecItemDelete(query as CFDictionary)

        // 新しいキーを保存
        let status = SecItemAdd(query as CFDictionary, nil)
        guard status == errSecSuccess else {
            throw KeychainError.saveFailed
        }
    }

    static func getAPIKey() -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        guard status == errSecSuccess,
              let data = result as? Data,
              let apiKey = String(data: data, encoding: .utf8) else {
            return nil
        }

        return apiKey
    }

    static func deleteAPIKey() {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account
        ]
        SecItemDelete(query as CFDictionary)
    }
}
```

### 8.2 セキュリティ対策一覧

| 対策 | 実装方法 |
|-----|---------|
| **APIキー暗号化保存** | iOS Keychain（AES-256） |
| **通信暗号化** | HTTPS必須（TLS 1.3） |
| **メモリ保護** | APIキーは使用後即破棄 |
| **デバイスロック連動** | `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` |
| **ログ出力禁止** | APIキーをログに出力しない |

---

## 9. エラーハンドリング

### 9.1 エラー種別

```swift
enum TranscriptionError: LocalizedError {
    case noAPIKey
    case invalidAPIKey
    case networkError(underlying: Error)
    case uploadFailed
    case apiFailed(statusCode: Int, message: String)
    case quotaExceeded
    case audioFileNotFound
    case processingTimeout

    var errorDescription: String? {
        switch self {
        case .noAPIKey:
            return "APIキーが設定されていません"
        case .invalidAPIKey:
            return "APIキーが無効です"
        case .networkError:
            return "ネットワークエラーが発生しました"
        case .uploadFailed:
            return "ファイルのアップロードに失敗しました"
        case .apiFailed(_, let message):
            return "API処理に失敗しました: \(message)"
        case .quotaExceeded:
            return "本日の無料枠を超えました。明日再度お試しください"
        case .audioFileNotFound:
            return "音声ファイルが見つかりません"
        case .processingTimeout:
            return "処理がタイムアウトしました"
        }
    }
}
```

### 9.2 リトライ戦略

| エラー種別 | リトライ | 回数 | 間隔 |
|-----------|---------|------|------|
| ネットワークエラー | ✅ | 3回 | 指数バックオフ（2s, 4s, 8s） |
| 429 Too Many Requests | ✅ | 3回 | Retry-Afterヘッダーに従う |
| 500系サーバーエラー | ✅ | 3回 | 指数バックオフ |
| 400 Bad Request | ❌ | - | 即時エラー通知 |
| 401 Unauthorized | ❌ | - | APIキー再設定を促す |

---

## 10. 実装フェーズ

### Phase 1: 基盤構築（3日）

| タスク | 詳細 |
|-------|------|
| プロジェクト設定 | SwiftUI, iOS 17+, SwiftData |
| データモデル定義 | Recording エンティティ |
| Keychainサービス | APIキー保存/取得 |
| 設定画面 | APIキー入力UI |

### Phase 2: 録音機能（3日）

| タスク | 詳細 |
|-------|------|
| AVFoundation設定 | 録音設定、権限リクエスト |
| 録音UI | 開始/停止、波形表示 |
| ファイル保存 | Documents/recordings/ |
| バックグラウンド録音 | Audio Background Mode |

### Phase 3: 文字起こし機能（5日）

| タスク | 詳細 |
|-------|------|
| File API連携 | アップロード処理 |
| Gemini API連携 | 文字起こし処理 |
| エラーハンドリング | リトライ、エラー通知 |
| 進捗表示 | ステータス更新UI |

### Phase 4: 結果表示・仕上げ（3日）

| タスク | 詳細 |
|-------|------|
| 詳細画面 | 結果表示UI |
| 一覧画面 | 録音リスト |
| データエクスポート | JSON/テキスト出力 |
| テスト・修正 | 動作確認、バグ修正 |

### 合計工数

| フェーズ | 工数 |
|---------|------|
| Phase 1 | 3日 |
| Phase 2 | 3日 |
| Phase 3 | 5日 |
| Phase 4 | 3日 |
| **合計** | **約2週間** |

---

## 11. 制約・注意事項

### 11.1 技術的制約

| 制約 | 影響 | 対策 |
|-----|------|------|
| **Gemini無料枠** | 1,500件/日 | 1ユーザー3-4件/日なら問題なし |
| **File API保存期間** | 48時間 | 処理完了後は不要、元ファイルはローカル保持 |
| **バックグラウンド処理** | iOS制限あり | BGProcessingTask使用 |
| **オフライン** | 文字起こし不可 | 録音のみ可能、オンライン復帰後に処理 |

### 11.2 ユーザー向け注意事項

| 注意事項 | 説明 |
|---------|------|
| **APIキー取得** | ユーザー自身でGoogle AI Studioから取得が必要 |
| **機種変更** | データ移行は手動エクスポート/iCloud |
| **複数デバイス** | 同期不可（iCloud使用で可能） |

### 11.3 今後の拡張

| 拡張項目 | 優先度 | 備考 |
|---------|-------|------|
| iCloud同期 | 中 | 複数デバイス対応 |
| Apple Watch対応 | 低 | 録音のみ |
| Webアプリ版 | 中 | 同じアーキテクチャで実装可能 |
| オフライン文字起こし | 低 | Whisper.cppなどローカルモデル |

---

## 12. 参考情報

### 12.1 公式ドキュメント

| リソース | URL |
|---------|-----|
| Gemini API | https://ai.google.dev/docs |
| Google AI Studio | https://aistudio.google.com/ |
| File API | https://ai.google.dev/api/files |

### 12.2 APIキー取得手順

1. https://aistudio.google.com/ にアクセス
2. Googleアカウントでログイン
3. 左メニュー「Get API Key」をクリック
4. 「Create API Key」をクリック
5. 表示されたキー（AIzaSy...）をコピー
6. アプリの設定画面に貼り付け

---

**以上**
