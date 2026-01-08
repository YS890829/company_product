# Phase 3 実装タスク: 文字起こし機能

## 現在のタスク
**Phase 3: 文字起こし機能** - Gemini API連携、TranscriptionService

詳細設計: [PHASE3_IMPLEMENTATION_PLAN.md](PHASE3_IMPLEMENTATION_PLAN.md)

---

## 完了済みPhase

### Phase 1: 基盤構築 ✅
- SwiftData導入（Recording.swift）
- Keychain（KeychainService.swift）
- 設定画面（SettingsView.swift）

### Phase 2: 録音機能 ✅
- AVFoundation設定（AudioManager.swift）
- 録音UI（RecordingView.swift）
- ファイル保存（StorageManager.swift）
- バックグラウンド録音（Info.plist: UIBackgroundModes）

---

## 重要な制約

1. **既存の録音・保存機能を壊さない**
2. **各ステージ完了後にビルド確認**
3. **APIキーをログに出力しない**

---

## Phase 3 実装タスク

### ステージ A: TranscriptionService 基盤

| タスク | ファイル | 操作 |
|--------|---------|------|
| A-1 | `TranscriptionService.swift` | **新規作成** |
| A-2 | `TranscriptionError.swift` | **新規作成** |
| A-3 | `TranscriptionModels.swift` | **新規作成** |
| A-4 | ビルド確認 | xcodebuild |

### ステージ B: Google File API 連携

| タスク | ファイル | 操作 |
|--------|---------|------|
| B-1 | `TranscriptionService.swift` | 修正（uploadToFileAPI実装） |
| B-2 | ビルド確認 | xcodebuild |

### ステージ C: Gemini API 文字起こし

| タスク | ファイル | 操作 |
|--------|---------|------|
| C-1 | `TranscriptionService.swift` | 修正（callGeminiAPI実装） |
| C-2 | `Recording.swift` | 修正（結果保存メソッド追加） |
| C-3 | ビルド確認 | xcodebuild |

### ステージ D: UI 統合

| タスク | ファイル | 操作 |
|--------|---------|------|
| D-1 | `ContentView.swift` | 修正（ステータス表示追加） |
| D-2 | `RecordingDetailView.swift` | **新規作成** |
| D-3 | `RecordingRow` | 修正（詳細画面への遷移） |
| D-4 | ビルド確認 | xcodebuild |

### ステージ E: エラーハンドリング

| タスク | ファイル | 操作 |
|--------|---------|------|
| E-1 | `TranscriptionService.swift` | 修正（リトライロジック追加） |
| E-2 | UI各所 | エラー表示対応 |
| E-3 | 全フローテスト | 動作確認 |

---

## 技術スタック

| 項目 | 値 |
|------|-----|
| 言語 | Swift 6.0 |
| UI | SwiftUI |
| 対象OS | iOS 17.0+ |
| データ保存 | SwiftData |
| セキュリティ | Keychain |
| 音声処理 | AVFoundation |
| 文字起こし | Gemini API (gemini-2.5-flash) |
| ファイルアップロード | Google File API |
| プロジェクト生成 | xcodegen |

---

## ファイル構成（Phase 3 完了後）

```
VoiceMemoApp/
├── project.yml
├── VoiceMemoApp.xcodeproj/
├── VoiceMemoApp/
│   ├── VoiceMemoAppApp.swift
│   ├── ContentView.swift          # ステータス表示追加
│   ├── RecordingView.swift
│   ├── RecordingDetailView.swift  # **新規** 結果表示画面
│   ├── SettingsView.swift
│   ├── VoiceMemo.swift            # 既存（互換用）
│   ├── Recording.swift            # SwiftDataモデル
│   ├── AudioManager.swift
│   ├── StorageManager.swift
│   ├── KeychainService.swift
│   ├── TranscriptionService.swift # **新規** 文字起こしサービス
│   ├── TranscriptionError.swift   # **新規** エラー定義
│   ├── TranscriptionModels.swift  # **新規** APIレスポンスモデル
│   ├── Info.plist
│   └── Assets.xcassets/
└── README.md
```

---

## API仕様

### Google File API（アップロード）

```
POST https://generativelanguage.googleapis.com/upload/v1beta/files?key={API_KEY}
Content-Type: multipart/form-data
```

### Gemini API（文字起こし）

```
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}
Content-Type: application/json
```

---

## ビルドコマンド

```bash
cd /Users/test/Desktop/simple_voicememo_iphoneapp/VoiceMemoApp
xcodegen generate
xcodebuild -project VoiceMemoApp.xcodeproj \
           -scheme VoiceMemoApp \
           -destination 'platform=iOS Simulator,name=iPhone 16' \
           -derivedDataPath ./build \
           build
```

---

## 完了条件

- [ ] TranscriptionService が File API にアップロードできる
- [ ] Gemini API で文字起こし結果を取得できる
- [ ] Recording に結果が保存される
- [ ] 一覧画面でステータスが表示される
- [ ] 詳細画面で結果が閲覧できる
- [ ] エラー時にリトライまたはエラー表示される
- [ ] ビルドエラーがない
