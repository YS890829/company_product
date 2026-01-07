# Phase 1 実装タスク: 基盤構築

## 現在のタスク
**Phase 1: 基盤構築** - SwiftData導入、Keychain、設定画面

詳細プラン: [PHASE1_PLAN.md](PHASE1_PLAN.md)

---

## 重要な制約

1. **既存の録音・保存機能を壊さない** - RecordingViewの保存ボタンは正常動作中
2. **各ステージ完了後にビルド確認**
3. **VoiceMemo.swift（既存モデル）は削除しない**

---

## Phase 1 実装タスク

### ステージ A: 独立機能追加

| タスク | ファイル | 操作 |
|--------|---------|------|
| A-1 | `VoiceMemoApp/VoiceMemoApp/KeychainService.swift` | **新規作成** |
| A-2 | `VoiceMemoApp/VoiceMemoApp/SettingsView.swift` | **新規作成** |
| A-3 | `VoiceMemoApp/VoiceMemoApp/ContentView.swift` | 修正（設定ボタン追加） |
| A-4 | ビルド確認 | xcodegen + xcodebuild |

### ステージ B: SwiftData 導入

| タスク | ファイル | 操作 |
|--------|---------|------|
| B-1 | `VoiceMemoApp/VoiceMemoApp/Recording.swift` | **新規作成** |
| B-2 | `VoiceMemoApp/VoiceMemoApp/VoiceMemoAppApp.swift` | 修正（ModelContainer追加） |
| B-3 | ビルド確認 | xcodebuild |

### ステージ C: データ層切り替え

| タスク | ファイル | 操作 |
|--------|---------|------|
| C-1 | `VoiceMemoApp/VoiceMemoApp/StorageManager.swift` | 修正（SwiftData対応） |
| C-2 | `VoiceMemoApp/VoiceMemoApp/ContentView.swift` | 修正（@Query使用） |
| C-3 | `VoiceMemoApp/VoiceMemoApp/RecordingView.swift` | 修正（SwiftData保存） |
| C-4 | ビルド確認 | xcodebuild |

### ステージ D: 最終確認

| タスク | 内容 |
|--------|------|
| D-1 | 全フローテスト: 録音→保存→一覧→再生 |
| D-2 | 設定画面テスト: APIキー保存・読み込み |

---

## 技術スタック

| 項目 | 値 |
|------|-----|
| 言語 | Swift 5.9+ |
| UI | SwiftUI |
| 対象OS | iOS 17.0+ |
| データ保存 | **SwiftData** (Phase 1で導入) |
| セキュリティ | **Keychain** (APIキー保存) |
| 音声処理 | AVFoundation |
| プロジェクト生成 | xcodegen |

---

## ファイル構成（Phase 1 完了後）

```
VoiceMemoApp/
├── project.yml
├── VoiceMemoApp.xcodeproj/
├── VoiceMemoApp/
│   ├── VoiceMemoAppApp.swift      # ModelContainer設定追加
│   ├── ContentView.swift          # 設定ボタン追加、@Query使用
│   ├── RecordingView.swift        # SwiftData保存対応
│   ├── SettingsView.swift         # **新規** APIキー設定画面
│   ├── VoiceMemo.swift            # 既存（削除しない）
│   ├── Recording.swift            # **新規** SwiftDataモデル
│   ├── AudioManager.swift         # 変更なし
│   ├── StorageManager.swift       # SwiftData対応
│   ├── KeychainService.swift      # **新規** APIキー管理
│   ├── Info.plist
│   └── Assets.xcassets/
└── README.md
```

---

## ビルドコマンド

```bash
# プロジェクト生成
cd /Users/test/Desktop/simple_voicememo_iphoneapp/VoiceMemoApp
xcodegen generate

# ビルド
xcodebuild -project VoiceMemoApp.xcodeproj \
           -scheme VoiceMemoApp \
           -destination 'platform=iOS Simulator,name=iPhone 16' \
           -derivedDataPath ./build \
           build

# シミュレーター実行
xcrun simctl boot "iPhone 16"
open -a Simulator
xcrun simctl install booted ./build/Build/Products/Debug-iphonesimulator/VoiceMemoApp.app
xcrun simctl launch booted com.example.VoiceMemoApp
```

---

## 実装詳細

### KeychainService.swift

```swift
import Foundation
import Security

class KeychainService {
    static let shared = KeychainService()
    private let service = "com.example.VoiceMemoApp"
    private let account = "gemini_api_key"

    func saveAPIKey(_ apiKey: String) throws { /* Keychain保存 */ }
    func getAPIKey() -> String? { /* Keychain読み込み */ }
    func deleteAPIKey() { /* Keychain削除 */ }
}
```

### Recording.swift (SwiftData)

```swift
import Foundation
import SwiftData

@Model
class Recording {
    @Attribute(.unique) var id: UUID
    var createdAt: Date
    var title: String?
    var audioFileName: String
    var duration: TimeInterval
    var fileSize: Int64

    // Phase 3 文字起こし用
    var transcriptText: String?
    var transcriptJSON: Data?
    var status: String = "pending"
    var errorMessage: String?
    var processedAt: Date?
}
```

### SettingsView.swift

```swift
import SwiftUI

struct SettingsView: View {
    @State private var apiKey: String = ""
    @State private var showSavedMessage = false

    var body: some View {
        Form {
            Section("Gemini API設定") {
                SecureField("APIキー", text: $apiKey)
                Button("保存") { saveAPIKey() }
            }
        }
        .navigationTitle("設定")
    }
}
```

---

## 完了条件

- [ ] KeychainService が APIキーを保存・取得できる
- [ ] 設定画面で APIキーを入力・保存できる
- [ ] SwiftData で Recording が永続化される
- [ ] 録音→保存→一覧→再生 が動作する
- [ ] ビルドエラーがない

---

## 注意事項

- **xcodegen generate** をファイル追加後に必ず実行
- iOS 17+ / SwiftData 使用（project.yml の deploymentTarget を 17.0 に変更が必要）
- 既存の UserDefaults データとの互換性は考慮しない（新規インストール前提）
