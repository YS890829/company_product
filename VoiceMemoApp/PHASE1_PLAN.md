# Phase 1 実装プラン: 基盤構築

## 目的
現在動作している録音・保存機能を維持しながら、Phase 1（基盤構築）を完了する。

## 制約
- **既存の録音・保存機能を壊さない**
- 各ステージ完了後にビルド確認を行う
- 問題発生時はgitでロールバック可能にする

---

## 実装ステージ

### ステージ A: 独立機能追加（既存コードへの影響なし）

#### A-1. KeychainService.swift 新規作成
- パス: `VoiceMemoApp/VoiceMemoApp/KeychainService.swift`
- 機能:
  - `saveAPIKey(_ apiKey: String) throws` - APIキー保存
  - `getAPIKey() -> String?` - APIキー取得
  - `deleteAPIKey()` - APIキー削除
- iOS Keychain使用（kSecAttrAccessibleWhenUnlockedThisDeviceOnly）

#### A-2. SettingsView.swift 新規作成
- パス: `VoiceMemoApp/VoiceMemoApp/SettingsView.swift`
- 機能:
  - APIキー入力（SecureField）
  - キー検証ボタン
  - 保存ステータス表示
  - APIキー取得方法へのリンク

#### A-3. ContentView.swift 修正
- ツールバーに設定ボタン（歯車アイコン）追加
- NavigationLink で SettingsView へ遷移

#### A-4. ビルド＆動作確認
```bash
cd /Users/test/Desktop/simple_voicememo_iphoneapp/VoiceMemoApp
xcodegen generate
xcodebuild -project VoiceMemoApp.xcodeproj -scheme VoiceMemoApp -destination 'platform=iOS Simulator,name=iPhone 16' build
```

---

### ステージ B: SwiftData 導入

#### B-1. Recording.swift 新規作成（SwiftDataモデル）
- パス: `VoiceMemoApp/VoiceMemoApp/Recording.swift`
- SwiftData @Model クラス
- フィールド:
  - id: UUID (unique)
  - createdAt: Date
  - title: String?
  - audioFileName: String
  - duration: TimeInterval
  - fileSize: Int64
  - transcriptText: String? (Phase 3用)
  - transcriptJSON: Data? (Phase 3用)
  - status: String (pending/uploading/processing/completed/failed)
  - errorMessage: String?
  - processedAt: Date?

#### B-2. VoiceMemoAppApp.swift 修正
- import SwiftData 追加
- ModelContainer 設定追加
- .modelContainer(for: Recording.self) modifier追加

#### B-3. ビルド確認
```bash
xcodebuild -project VoiceMemoApp.xcodeproj -scheme VoiceMemoApp -destination 'platform=iOS Simulator,name=iPhone 16' build
```

---

### ステージ C: データ層切り替え

#### C-1. StorageManager.swift 修正
- SwiftData 対応に拡張
- ModelContext を使用した保存・読み込み
- 既存の UserDefaults/FileManager との互換性維持

#### C-2. ContentView.swift 修正
- @Query で SwiftData から録音一覧取得
- @Environment(\.modelContext) 追加
- 日付別グループ表示を維持

#### C-3. RecordingView.swift 修正
- 保存ロジックを SwiftData 対応に更新
- ModelContext への insert 処理
- **注意**: 保存ボタンの動作を維持

#### C-4. ビルド＆動作確認
```bash
xcodebuild -project VoiceMemoApp.xcodeproj -scheme VoiceMemoApp -destination 'platform=iOS Simulator,name=iPhone 16' build
```

---

### ステージ D: 最終確認

#### D-1. 全フローテスト
- 録音開始 → 停止 → 保存ボタン表示 → 保存 → 一覧表示 → 再生

#### D-2. 設定画面テスト
- APIキー入力 → 保存 → アプリ再起動 → キー読み込み確認

#### D-3. シミュレーター実行
```bash
xcrun simctl boot "iPhone 16"
open -a Simulator
xcrun simctl install booted ./build/Build/Products/Debug-iphonesimulator/VoiceMemoApp.app
xcrun simctl launch booted com.example.VoiceMemoApp
```

---

## 修正対象ファイル一覧

| ファイル | 操作 | ステージ |
|---------|------|---------|
| KeychainService.swift | **新規** | A |
| SettingsView.swift | **新規** | A |
| Recording.swift | **新規** | B |
| VoiceMemoAppApp.swift | 修正 | B |
| ContentView.swift | 修正 | A, C |
| StorageManager.swift | 修正 | C |
| RecordingView.swift | 修正 | C |

---

## 完了条件

1. KeychainService が正常にAPIキーを保存・取得できる
2. 設定画面でAPIキーを入力・保存できる
3. SwiftData で Recording モデルが永続化される
4. 録音 → 保存 → 一覧 → 再生 の全フローが動作する
5. ビルドエラーがない

---

## 注意事項

- VoiceMemo.swift（既存モデル）は削除しない（フォールバック用）
- 各ステージ完了後に git commit する
- iOS 17+ / SwiftData 使用
- project.yml の変更は不要（SwiftDataは標準フレームワーク）
