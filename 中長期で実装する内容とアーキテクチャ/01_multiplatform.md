# マルチプラットフォーム対応

## 調査日
2026-01-09

## 調査目的

iPhoneアプリに加え、Mac/Windows対応のWebブラウザ版を実現する方法を調査

---

## 調査結果

### 1. Web録音技術

#### MediaRecorder API

| 項目 | 詳細 |
|------|------|
| **概要** | ブラウザ標準のメディアストリーム録音API |
| **ブラウザ対応** | Chrome, Firefox, Safari 11+, Edge (Chromium) |
| **コーデック** | Chrome/Opera: `audio/webm;codecs=opus`, Firefox: `audio/ogg;codecs=opus` |
| **制限事項** | ビットレート制御 (`audioBitPerSecond`) は現時点で未サポート |

**ベストプラクティス:**
- `MediaRecorder.isTypeSupported()` でMIMEタイプ対応を事前確認
- `getUserMedia()` でマイクアクセス取得
- `ondataavailable` イベントで録音データをチャンク取得
- Safari用にPCM/WAVポリフィルの準備が必要な場合あり

#### Web Audio API

| 項目 | 詳細 |
|------|------|
| **用途** | エフェクト追加、可視化、空間効果 |
| **連携** | MediaRecorder APIと併用可能 |
| **追加機能** | SpeechRecognition APIで音声テキスト変換も可能 |

### 2. フロントエンドフレームワーク比較

| フレームワーク | 特徴 | 推奨用途 | 学習コスト |
|--------------|------|---------|-----------|
| **React** | 最大シェア(39%+)、柔軟性高、大規模エコシステム | カスタムオーディオUI、複雑な状態管理 | 中 |
| **Next.js** | React + SSR/SSG、フルスタック対応 | SEO重視、SaaS製品 | 中〜高 |
| **Vue.js** | シンプル、学習曲線緩やか、Proxy-based reactivity | ダッシュボード、SPA、開発速度重視 | 低 |

**推奨:** 音声アプリはクライアントサイド中心のため **React** または **Vue.js** が適切。SEOが不要ならNext.jsのSSRは過剰。

### 3. PWA（Progressive Web App）対応

| 機能 | 対応状況 |
|------|---------|
| **オフライン録音** | Service Workerでキャッシュ可能 |
| **インストール** | ホーム画面追加可能（iOS/Android/Desktop） |
| **バックグラウンド** | Background Sync APIで復帰後に同期 |
| **マイクアクセス** | 全主要ブラウザ対応 |

**PWAの利点:**
- ストア申請不要
- 単一コードベースでマルチプラットフォーム対応
- オフライン時の録音データはローカル保存 → オンライン復帰時にアップロード

### 4. デスクトップアプリ: Tauri vs Electron

| 比較項目 | Electron | Tauri |
|---------|----------|-------|
| **アプリサイズ** | 100MB以上 | 10MB未満 |
| **メモリ使用量** | 数百MB | 30-40MB (idle) |
| **起動時間** | 1-2秒 | 0.5秒未満 |
| **レンダリング** | 内蔵Chromium | システムWebView (WRY) |
| **バックエンド言語** | Node.js (JavaScript) | Rust |
| **モバイル対応** | なし | Tauri 2.x でiOS/Android対応 |
| **エコシステム** | 成熟、豊富なパッケージ | 成長中、Rust知識が一部必要 |
| **採用事例** | Slack, Discord, VS Code | 新興アプリ多数 |
| **セキュリティ** | 標準的 | Rust bridgeで強化 |

**Tauri 2.0 (2024年後半リリース):** 採用率が前年比35%増加

---

## 技術選定肢

### Option A: PWA (Progressive Web App)

```
React/Vue.js + MediaRecorder API + Service Worker
```

**メリット:**
- 開発コスト最小
- iOS/Android/Mac/Windows/Linux全対応
- ストア申請不要
- オフライン録音可能

**デメリット:**
- iOSのPWA制限（通知など）
- ブラウザ依存の音声品質差

### Option B: PWA + Tauri

```
React/Vue.js (共通) + PWA (Web) + Tauri (Desktop)
```

**メリット:**
- Web版とデスクトップ版で共通フロントエンド
- デスクトップ版は高性能・軽量
- 将来的にTauriでモバイルも可能

**デメリット:**
- Rustの学習コスト（高度な機能使用時）
- 2つのビルドパイプライン管理

### Option C: Electron

```
React + Electron (Desktop) + React (Web)
```

**メリット:**
- Node.js知識で完結
- 成熟したエコシステム

**デメリット:**
- アプリサイズ大
- メモリ消費大
- モバイル非対応

---

## 推奨案

### **Option A: PWA優先アプローチ**

**理由:**
1. **開発効率**: 単一コードベースで全プラットフォーム対応
2. **コスト**: 追加フレームワーク不要
3. **段階的拡張**: 将来的にTauriでネイティブ化も可能
4. **ボイスメモ用途**: 複雑なOS連携不要、PWAで十分

**技術スタック:**

| レイヤー | 技術 |
|---------|------|
| フレームワーク | **React** (TypeScript) |
| 状態管理 | Zustand or Jotai |
| 録音 | MediaRecorder API |
| オフライン | Service Worker + IndexedDB |
| ビルド | Vite |
| PWA化 | vite-plugin-pwa |

**段階的実装:**

1. **Phase 1**: Web版 (React + PWA) - Mac/Windows/Linux対応
2. **Phase 2**: PWA最適化 - オフライン録音、インストール対応
3. **Phase 3**: (オプション) Tauri化 - デスクトップ専用機能が必要な場合

---

## 参考資料

- [MediaRecorder API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder)
- [Using the MediaStream Recording API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/MediaStream_Recording_API/Using_the_MediaStream_Recording_API)
- [MediaRecorder Browser Support - Can I Use](https://caniuse.com/mediarecorder)
- [PWA Audio Recording Demo - Progressier](https://progressier.com/pwa-capabilities/audio-recording)
- [What PWA Can Do Today - Audio Recording](https://whatpwacando.today/audio-recording/)
- [PWA Offline and Background Operation - MDN](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Offline_and_background_operation)
- [Tauri vs Electron Comparison 2025 - Raftlabs](https://www.raftlabs.com/blog/tauri-vs-electron-pros-cons/)
- [Electron vs Tauri - DoltHub Blog](https://www.dolthub.com/blog/2025-11-13-electron-vs-tauri/)
- [Tauri vs Electron Performance - GetHopp](https://www.gethopp.app/blog/tauri-vs-electron)
- [React vs Next.js vs Vue 2025 - DEV Community](https://dev.to/ciphernutz/react-vs-nextjs-vs-vue-which-frontend-framework-wins-in-2025-26gj)
- [JavaScript Frameworks Comparison 2025 - Brilworks](https://www.brilworks.com/blog/javascript-web-frameworks-comparison/)

---

## 結論・決定事項

| 項目 | 決定 |
|------|------|
| **Web版技術** | React (TypeScript) + PWA |
| **録音方式** | MediaRecorder API |
| **オフライン対応** | Service Worker + IndexedDB |
| **デスクトップアプリ** | 当面不要（PWAで対応）、将来的にTauri検討 |
| **iOSアプリ** | 既存Swift実装を維持 |

---

## 残課題

1. **Safari対応の詳細検証**: MediaRecorderのコーデック互換性
2. **オフライン録音のデータ同期設計**: 競合解決、リトライ戦略
3. **React状態管理ライブラリの最終選定**: Zustand vs Jotai vs Redux Toolkit
4. **iPhoneアプリとWebアプリのUI/UX統一ガイドライン**
