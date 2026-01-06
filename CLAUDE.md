# Simple Voice Memo iPhone App

## プロジェクト概要

iPhone 17向けのシンプルなボイスメモアプリ。
Claude Codeで完全自動作成する。**xcodegen**を使用してプロジェクト生成。

---

## 技術スタック

| 項目 | 値 |
|------|-----|
| 言語 | Swift 5.9+ |
| UI | SwiftUI |
| 対象OS | iOS 26.0+ |
| 対象デバイス | iPhone 17 |
| 音声処理 | AVFoundation |
| データ保存 | ローカル（Documents + UserDefaults） |
| プロジェクト生成 | xcodegen |

---

## 機能要件（MVP）

| 機能 | 説明 | 優先度 |
|------|------|--------|
| 録音 | マイクで音声を録音し.m4a形式で保存 | 必須 |
| 一覧表示 | アップロード日別にグループ化して表示 | 必須 |
| 再生 | 保存した音声を再生/停止 | 必須 |

---

## ファイル構成

```
VoiceMemoApp/
├── project.yml                    # xcodegen設定（これが重要）
├── VoiceMemoApp.xcodeproj/        # xcodegen が自動生成
├── VoiceMemoApp/
│   ├── VoiceMemoAppApp.swift      # @main エントリーポイント
│   ├── ContentView.swift          # メイン画面（日付別一覧）
│   ├── RecordingView.swift        # 録音画面（シート）
│   ├── VoiceMemo.swift            # データモデル
│   ├── AudioManager.swift         # 録音・再生ロジック
│   ├── StorageManager.swift       # データ永続化
│   ├── Info.plist                 # 権限設定
│   └── Assets.xcassets/           # アセット
└── README.md
```

---

## 実装ルール

### Swift コーディング規約

- SwiftUI の宣言的UIパターンに従う
- `@StateObject`, `@ObservedObject`, `@Published` で状態管理
- エラーハンドリングは最小限（print文でログ出力）
- 過度な抽象化を避け、シンプルな実装を優先

### プロジェクト設定（project.yml）

```yaml
name: VoiceMemoApp
targets:
  VoiceMemoApp:
    type: application
    platform: iOS
    deploymentTarget: "26.0"
    sources: [VoiceMemoApp]
    info:
      path: VoiceMemoApp/Info.plist
    settings:
      PRODUCT_BUNDLE_IDENTIFIER: com.example.VoiceMemoApp
      INFOPLIST_KEY_NSMicrophoneUsageDescription: 音声メモを録音するためにマイクを使用します
```

### 権限（Info.plist）

必須:
```xml
<key>NSMicrophoneUsageDescription</key>
<string>音声メモを録音するためにマイクを使用します</string>
```

---

## ビルド・実行コマンド

### プロジェクト生成（xcodegen）
```bash
cd /Users/test/Desktop/fukugyo_plan/simple_voicememo_iphoneapp/VoiceMemoApp
xcodegen generate
```

### ビルド
```bash
xcodebuild -project VoiceMemoApp.xcodeproj \
           -scheme VoiceMemoApp \
           -destination 'platform=iOS Simulator,name=iPhone 17' \
           -derivedDataPath ./build \
           build
```

### シミュレーター起動
```bash
xcrun simctl boot "iPhone 17"
open -a Simulator
```

### アプリインストール・起動
```bash
xcrun simctl install booted ./build/Build/Products/Debug-iphonesimulator/VoiceMemoApp.app
xcrun simctl launch booted com.example.VoiceMemoApp
```

---

## 実装ステップ

詳細は [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) を参照。

| Step | 内容 | 依存 |
|------|------|------|
| 1 | xcodegen導入 + 全ファイル作成 | なし |
| 2 | プロジェクト生成 + ビルド | Step 1 |
| 3 | シミュレーター起動・動作確認 | Step 2 |
| 4 | バグ修正（オプション） | Step 3 |

---

## 注意事項

- **xcodegen generate** を実行しないとproject.pbxprojが生成されない
- ファイル追加/削除時は必ず **xcodegen generate** を再実行
- シミュレーターでのマイク使用はMacのマイクを使用
- エラー発生時は該当Stepのみ再実行

---

## 追加機能（将来）

MVP完成後に追加可能:
- 削除機能（スワイプ）
- タイトル編集
- 検索機能
- iCloud同期
