# アーキテクチャ決定事項と残論点

**作成日**: 2026-01-09
**ステータス**: Phase 1 実装中 / アーキテクチャ検討中

---

## 1. 決定事項

### 1.1 基本方針

| 項目 | 決定内容 |
|-----|---------|
| **アプローチ** | クラウド連携版（スマホ完結ではない） |
| **バックエンド処理** | 既存の structured_transcriber を活用 |
| **データ管理** | 一元蓄積（後の分析活用のため） |

### 1.2 クラウド連携版の構成

```
┌─────────────────┐          ┌─────────────────────────────────────┐
│   iPhone App    │          │       Mac (structured_transcriber)  │
│                 │          │                                     │
│  • 録音         │  Google  │  • webhook_server.py (ファイル検知) │
│  • Drive Upload │─────────▶│  • structured_transcribe.py         │
│  • 結果閲覧     │   Drive  │  • ChromaDB (Vector DB)             │
└─────────────────┘          │  • 一元データ蓄積                   │
                             └─────────────────────────────────────┘
```

### 1.3 structured_transcriber の要件採用

| 機能 | 内容 |
|-----|------|
| **話者識別** | Speaker 1, Speaker 2 形式 |
| **構造化JSON** | segments（話者、テキスト、タイムスタンプ） |
| **要約生成** | エグゼクティブサマリー + 主要ポイント |
| **Vector DB** | ChromaDB によるセマンティック検索 |
| **使用モデル** | Gemini 2.5 Flash |

### 1.4 技術選定根拠

**Web検索による検証結果（2026-01-09）:**

- `google-generative-ai-swift` SDK は 2025年11月に非推奨化
- Firebase AI Logic SDK が公式推奨だが、クラウド連携版では不要
- Gemini Audio API は話者識別・構造化JSON出力に対応
- Files API で最大2GBの音声ファイルに対応

**参考資料:**
- [Audio Understanding - Gemini API](https://ai.google.dev/gemini-api/docs/audio)
- [Files API - Gemini](https://ai.google.dev/gemini-api/docs/files)
- [Firebase AI Logic](https://firebase.google.com/docs/ai-logic)

---

## 2. 現在の実装状況

### 2.1 Phase 1: 基盤構築（進行中）

| ステージ | タスク | 状態 |
|---------|-------|------|
| A-1 | KeychainService.swift 新規作成 | ✅ 完了 |
| A-2 | SettingsView.swift 新規作成 | ⬜ 未着手 |
| A-3 | ContentView.swift 修正（設定ボタン追加） | ⬜ 未着手 |
| A-4 | ビルド確認 | ⬜ 未着手 |
| B-1〜3 | SwiftData 導入 | ⬜ 未着手 |
| C-1〜4 | データ層切り替え | ⬜ 未着手 |
| D-1〜2 | 最終確認 | ⬜ 未着手 |

### 2.2 既存リソース

| リソース | パス |
|---------|------|
| iPhoneアプリ | `/Users/test/Desktop/simple_voicememo_iphoneapp/` |
| structured_transcriber | `/Users/test/Desktop/fukugyo_plan/SaaS候補アプリ/structured_transcriber/` |
| revenue-intelligence-platform | `/Users/test/Desktop/fukugyo_plan/revenue-intelligence-platform/` |

---

## 3. 残論点（要検討）

### 3.1 マルチプラットフォーム対応

| 論点 | 内容 |
|-----|------|
| **Webブラウザ版** | Mac/Windows両対応の録音フロントエンド作成 |
| **共通バックエンド** | iPhoneアプリとWebブラウザ版で同じ structured_transcriber を使用 |

```
┌─────────────────────────────────────────────────────────────────────┐
│                    将来アーキテクチャ構想                            │
│                                                                     │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐             │
│   │ iPhone App  │   │ Web Browser │   │ (将来)      │             │
│   │             │   │ Mac/Windows │   │ Android等   │             │
│   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘             │
│          │                 │                 │                     │
│          └────────────────┬┴─────────────────┘                     │
│                           │                                        │
│                           ▼                                        │
│              ┌─────────────────────────┐                          │
│              │   共通バックエンド       │                          │
│              │   (structured_transcriber)                         │
│              └─────────────────────────┘                          │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 サーバー移行計画

| 項目 | 現状 | 将来 |
|-----|------|------|
| **実行環境** | Mac (ローカル) | Google Cloud（最有力） |
| **課題** | Mac常時起動必要 | クラウドで常時稼働 |
| **候補サービス** | - | Cloud Run / Cloud Functions |

### 3.3 SFA/CRM連携

| 論点 | 内容 |
|-----|------|
| **連携先** | revenue-intelligence-platform |
| **連携データ** | 文字起こし結果、構造化データ、要約 |
| **連携方式** | API連携 or 共有DB（要検討） |

### 3.4 マイクロサービス設計

| サービス | 役割 | 独立性 |
|---------|------|--------|
| **録音フロントエンド** | iPhone / Web / 他 | 独立 |
| **文字起こし・構造化** | structured_transcriber | 独立 |
| **データ蓄積・検索** | Vector DB + Storage | 独立 |
| **SFA/CRM** | revenue-intelligence-platform | 独立 |

```
┌─────────────────────────────────────────────────────────────────────┐
│                    マイクロサービス構成案                            │
│                                                                     │
│   ┌───────────────┐                                                │
│   │ 録音フロント   │ ─────┐                                        │
│   │ (iPhone/Web)  │      │                                        │
│   └───────────────┘      │                                        │
│                          ▼                                        │
│                   ┌───────────────┐      ┌───────────────┐        │
│                   │ 文字起こし    │      │ データ蓄積    │        │
│                   │ 構造化サービス │─────▶│ 検索サービス  │        │
│                   │ (transcriber) │      │ (Vector DB)   │        │
│                   └───────────────┘      └───────┬───────┘        │
│                                                  │                 │
│                                                  ▼                 │
│                                          ┌───────────────┐        │
│                                          │ SFA/CRM       │        │
│                                          │ (revenue-     │        │
│                                          │  intelligence)│        │
│                                          └───────────────┘        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. 今後の予定

### 4.1 短期（Phase 1-4 完了まで）

| フェーズ | 内容 | 備考 |
|---------|------|------|
| Phase 1 | 基盤構築（SwiftData, Keychain, 設定画面） | 現在進行中 |
| Phase 2 | 録音機能 | |
| Phase 3 | Google Drive連携（アップロード） | クラウド連携版 |
| Phase 4 | 結果表示（Drive/Docs閲覧） | |
| Mac設定 | structured_transcriber + ngrok + webhook | 並行作業 |

### 4.2 中期（別スレッドで検討）

| 項目 | 内容 |
|-----|------|
| Webブラウザ版 | 録音フロントエンド（Mac/Windows対応） |
| API設計 | マイクロサービス間のインターフェース定義 |
| SFA/CRM連携 | revenue-intelligence-platform との接続 |

### 4.3 長期

| 項目 | 内容 |
|-----|------|
| クラウド移行 | Mac → Google Cloud |
| スケーラビリティ | 複数ユーザー対応 |

---

## 5. 参考情報

### 5.1 関連ドキュメント

| ドキュメント | パス |
|-------------|------|
| Phase 1 詳細プラン | [PHASE1_PLAN.md](PHASE1_PLAN.md) |
| ローカル完結版設計 | [LOCAL_IMPLEMENTATION_DESIGN.md](LOCAL_IMPLEMENTATION_DESIGN.md) |
| クラウド連携プラン | [CLOUD_INTEGRATION_PLAN.md](CLOUD_INTEGRATION_PLAN.md) |
| プロジェクト指示 | [CLAUDE.md](CLAUDE.md) |

### 5.2 デバイス環境

| デバイス | スペック |
|---------|---------|
| Mac | MacBook Pro 16" 2019 / i9 / 16GB / macOS Tahoe 26.0.1 |
| iPhone | iPhone 17 / iOS 26.1 / 8GB RAM |

---

## 6. 次のアクション

1. **Phase 1 実装継続** - 現在のiPhoneアプリ基盤構築を完了
2. **別スレッドで議論** - マイクロサービス設計、Webブラウザ版、SFA/CRM連携の詳細検討

---

**更新履歴:**
- 2026-01-09: 初版作成（クラウド連携版採用決定、残論点整理）
