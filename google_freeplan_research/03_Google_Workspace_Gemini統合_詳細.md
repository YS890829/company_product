# Google Workspace Gemini統合 詳細

**調査日**: 2026年1月2日
**対象**: Google WorkspaceにおけるGemini AI機能の詳細

---

## 2025年の大型アップデート

### 変更の概要

- **2025年1月16日〜**: 新規ユーザーにGemini統合適用開始
- **2025年3月17日〜**: 既存ユーザーにも適用、料金改定

### アドオン廃止

- 旧「Gemini for Google Workspace」アドオン（月額¥2,260）が**廃止**
- 2025年2月1日以降、アドオンライセンス料金の請求停止
- 残存期間に応じて返金

---

## Business Standard（¥1,600/月）で使えるGemini機能

### Geminiサイドパネル

各アプリ内でGeminiを呼び出し、コンテキストを切り替えずにAI機能を利用可能。

| アプリ | できること |
|--------|-----------|
| **Gmail** | メール要約、返信案作成、文章のトーン調整 |
| **Google Docs** | 文章生成、要約、リライト、翻訳 |
| **Google Sheets** | データ分析、数式提案、グラフ作成支援 |
| **Google Slides** | スライド生成、画像挿入提案 |
| **Google Drive** | ファイル検索、要約 |
| **Google Meet** | 録画、文字起こし（日本語対応）、要約 |

### Gemini Advanced相当の機能

- **Gemini 3 Pro**（思考モード）へのアクセス
- **NotebookLM Plus**: 音声概要、高度なノートブック機能

### その他のAI機能

- Cloud Search: Gmail・Drive・Docs等を横断検索
- Smart Compose / Smart Reply
- 自動生成された要約・アクションアイテム

---

## プラン別Gemini機能比較

| 機能 | Starter | Standard | Plus | Enterprise |
|------|---------|----------|------|------------|
| Geminiサイドパネル | ✅ | ✅ | ✅ | ✅ |
| Gemini 3 Pro | ✅ | ✅ | ✅ | ✅ |
| NotebookLM Plus | ✅ | ✅ | ✅ | ✅ |
| Meet録画・文字起こし | ❌ | ✅ | ✅ | ✅ |
| Meetノイズキャンセル | ❌ | ✅ | ✅ | ✅ |
| Cloud Search | ❌ | ✅ | ✅ | ✅ |
| DLP（データ損失防止） | ❌ | ❌ | ❌ | ✅ |
| セキュリティセンター | ❌ | ❌ | ❌ | ✅ |

---

## Gemini for WorkspaceとGemini APIの違い

| 項目 | Gemini for Workspace | Gemini API |
|------|---------------------|------------|
| **対象** | エンドユーザー | 開発者 |
| **利用方法** | サイドパネル、アプリ内UI | プログラムからAPI呼び出し |
| **課金** | Workspaceプラン料金に含む | 従量課金（または無料枠） |
| **制限** | プラン機能による | RPM/TPM/RPDによる |
| **データ保護** | Workspace契約で保証 | Cloud Billing有効化で保証 |
| **用途** | 業務効率化 | アプリ開発 |

### 重要ポイント

**WorkspaceプランでAPI無料枠は増えない**

- Gemini APIの制限は**プロジェクト単位**
- Workspaceプランは**Gemini for Workspace**（UI機能）に影響
- API利用には別途Cloud Billing設定が必要

---

## 料金改定の詳細（2025年3月17日〜）

### 値上げ幅

| プラン | 旧料金（税抜） | 新料金（税抜） | 値上げ額 |
|--------|--------------|--------------|---------|
| Business Starter | ¥680 | ¥800 | +¥120 |
| Business Standard | ¥1,360 | ¥1,600 | +¥240 |
| Business Plus | ¥2,040 | ¥2,500 | +¥460 |

### 値上げの理由

- Gemini AI機能の統合
- AI機能開発・運用コストの反映
- 旧アドオン（¥2,260/月）が不要になった分、実質的にはお得

### 適用タイミング

- **新規ユーザー**: 2025年1月16日から
- **既存ユーザー**: 2025年3月17日以降の更新日から
- **10ユーザー以下の既存契約**: 2026年1月まで旧料金

---

## Google AI Pro vs Google Workspace

| 項目 | Google AI Pro | Workspace Business Standard |
|------|--------------|----------------------------|
| 月額（税抜） | ¥2,900 | ¥1,600 |
| 独自ドメインメール | ❌ | ✅ |
| Gemini 3 Pro | ✅（アプリ） | ✅（サイドパネル） |
| Gmail/Docs等との統合 | ❌ | ✅ |
| Meet録画・文字起こし | ❌ | ✅ |
| ストレージ | 2TB（個人） | 2TB（業務用） |
| ファミリー共有 | ✅（5人まで） | ❌ |
| 用途 | 個人AI利用 | 法人業務全般 |

### 結論

法人・個人事業主で独自ドメインメールが必要なら、**Workspace Business Standard（¥1,600/月）の方がコスパ良好**。

---

## 参考リンク

- [Google Workspace Gemini統合発表](https://www.yoshidumi.co.jp/collaboration-lab/gws_pricing_summary)
- [Gemini for Workspace お支払いの仕組み](https://support.google.com/a/answer/13969047?hl=ja)
- [Google Workspace 各エディションの比較](https://support.google.com/a/answer/6043385?hl=ja)
