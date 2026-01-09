# Scripts - ユーティリティスクリプト集

**最終更新**: 2025年11月4日
**目的**: データベース管理スクリプト（バックアップ、エクスポート、復元）の一元管理

---

## 📁 ディレクトリ構成

```
scripts/
├── README.md                    # このファイル
├── backup/                      # バックアップスクリプト
│   └── generate_backup.py       # JSON形式バックアップ生成
├── export/                      # データエクスポートスクリプト
│   └── dump_latest_database.py  # SQL形式ダンプ生成
├── generation/                  # データ復元スクリプト
│   └── restore_database.py      # データベース復元
└── archive/                     # 旧バックアップファイル保管
    ├── README.md                # アーカイブ説明
    └── supabase_backup_full_20251102_073312.json  # Phase 0-6前のバックアップ
```

---

## 💾 backup/ - バックアップスクリプト

### generate_backup.py
**サイズ**: 3,479 bytes
**用途**: Supabase全データバックアップ（JSON形式）

#### 機能
- 全テーブルデータ抽出（companies, deals, meetings, emails等）
- JSON形式で保存
- タイムスタンプ付きファイル名（`supabase_backup_full_YYYYMMDD_HHMMSS.json`）

#### 実行方法
```bash
cd revenue-intelligence-platform/scripts/backup
python3 generate_backup.py
```

#### 前提条件
- Supabase接続情報（`.env`）
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`

#### 出力例
- `supabase_backup_full_20251104_120000.json`

#### 用途
- 定期バックアップ（週次推奨）
- メンテナンス前のスナップショット
- データ移行時のエクスポート

---

## 📤 export/ - データエクスポートスクリプト

### dump_latest_database.py
**サイズ**: 11,015 bytes
**用途**: 最新DBの完全ダンプ（SQL形式）

#### 機能
- PostgreSQLスキーマ抽出（49カラム、全制約含む）
- 全テーブルデータダンプ（2,789レコード）
- ページネーション対応（1,590メール対応）
- SQL INSERT文生成

#### 実行方法
```bash
cd revenue-intelligence-platform/scripts/export
python3 dump_latest_database.py
```

#### 前提条件
- PostgreSQL接続情報（`.env`）
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
- psycopg2ライブラリ
  ```bash
  python3 -m pip install psycopg2-binary
  ```

#### 出力ファイル（Deprecated - v1.2.0以前）

**⚠️ 重要**: 現在のスキーマ（v2.0.0）は16テーブル正規化版です。
- 最新スキーマ定義: `../../database/schema-design-final.md`
- 実装プラン: `../../database/database-complete-implementation-plan.md`
- 実装ブランチ: `feature/data-generation-phase0-7`

**旧バージョン出力ファイル**（v1.2.0、4テーブル版）:
- `../../database/schema.sql` (3.8 KB) - Deprecated
  - 4テーブル構成（companies, deals, meetings, emails）
  - deals: 48カラム

- `../../database/seed.sql` (33 MB) - Deprecated
  - Companies: 2件
  - Deals: 310件
  - Meetings: 887件
  - Emails: 1,590件

#### 用途
- ~~schema.sql + seed.sqlの更新~~（v1.2.0まで）
- 現在のスキーマ（v2.0.0）は別ブランチで実装完了
- このスクリプトは旧バージョン用（アーカイブ）

---

## 🔄 generation/ - データ復元スクリプト

### restore_database.py
**サイズ**: 1,532 bytes
**用途**: schema.sql + seed.sqlからDB復元

#### 機能
- schema.sql実行（テーブル作成）
- seed.sql実行（データ投入）
- エラーハンドリング

#### 実行方法
```bash
cd revenue-intelligence-platform/scripts/generation
python3 restore_database.py
```

#### 前提条件
- PostgreSQL接続情報（`.env`）
- `../../database/schema.sql` 存在
- `../../database/seed.sql` 存在

#### 注意事項
- 既存データは削除される（DROP TABLE IF EXISTS）
- 実行前にバックアップ推奨

---

## 🗄️ archive/ - 旧バックアップ保管

### supabase_backup_full_20251102_073312.json
**サイズ**: 4,277,423 bytes (4.08 MB)
**作成日**: 2025年11月2日 07:33:12
**内容**: Phase 0-6実装前のDBバックアップ

#### データ件数（旧構成）
- Companies: 2件
- Deals: 60件
- Meetings: 116件
- Emails: 280件

#### 注意
- **現在のDB構成とは異なります**
- 現在: Deals 310件、Meetings 887件、Emails 1,590件
- 参照用のみ（復元非推奨）

詳細は [archive/README.md](archive/README.md) を参照

---

## 📊 実行推奨順序

### 定期バックアップ（週次）
```bash
# 1. JSON形式バックアップ
cd revenue-intelligence-platform/scripts/backup
python3 generate_backup.py

# 2. SQL形式ダンプ（schema.sql + seed.sql更新）
cd ../export
python3 dump_latest_database.py
```

### データベース復元
```bash
# バックアップから復元
cd revenue-intelligence-platform/scripts/generation
python3 restore_database.py
```

### メンテナンス前のスナップショット
```bash
# 両形式でバックアップ取得
cd revenue-intelligence-platform/scripts/backup
python3 generate_backup.py
cd ../export
python3 dump_latest_database.py
```

---

## 🔐 環境変数設定

### 必須環境変数

#### Supabase接続
```bash
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
```

### 設定方法
1. `/database/.env.example` をコピー
2. `.env` ファイルを作成
3. 実際の値を設定
4. `.env` をGitにコミットしない（`.gitignore`で除外済み）

---

## 📝 トラブルシューティング

### psycopg2 ImportError
```bash
# インストール
python3 -m pip install psycopg2-binary

# バージョン確認
python3 -c "import psycopg2; print(psycopg2.__version__)"
```

### Supabase接続エラー
```bash
# 環境変数確認
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv('../../database/.env')
print(f'SUPABASE_URL: {os.getenv(\"SUPABASE_URL\")}')
print(f'Key exists: {bool(os.getenv(\"SUPABASE_SERVICE_ROLE_KEY\"))}')
"
```

### dump_latest_database.py でメール件数不足
- **原因**: Supabase 1,000件制限
- **対策**: ページネーション実装済み（自動処理）
- **確認**: seed.sqlの`INSERT INTO emails`件数を確認

### restore_database.py でエラー
```bash
# schema.sql存在確認
ls -lh ../../database/schema.sql

# seed.sql存在確認
ls -lh ../../database/seed.sql

# PostgreSQL接続確認
psql postgresql://postgres:postgres@127.0.0.1:54322/postgres -c "SELECT version();"
```

---

## 🚀 バックアップ戦略

### 推奨バックアップ頻度

| バックアップ形式 | 頻度 | 目的 |
|----------------|------|------|
| JSON（generate_backup.py） | 週次 | 定期バックアップ |
| SQL（dump_latest_database.py） | データ変更時 | schema.sql + seed.sql更新 |
| Git commit | 実装完了時 | バージョン管理 |

### バックアップファイル保管

#### 保持するバックアップ
- **JSON**: 直近4週間分（週次バックアップ）
- **SQL**: 最新のみ（Git管理）
- **アーカイブ**: マイルストーン時点（archive/）

#### 削除対象
- 4週間以前のJSON
- 旧実装フェーズのスクリプト
- 旧データ構造のエクスポートファイル

---

## 📖 関連ドキュメント

- [../database/README.md](../database/) - DB定義とマイグレーション
- [../database/schema.sql](../database/schema.sql) - 最新スキーマ定義（49カラム）
- [../database/seed.sql](../database/seed.sql) - 最新データダンプ（2,789レコード）
- [archive/README.md](archive/README.md) - アーカイブファイル説明

---

## 📈 現在のデータベース状態（2025年11月6日時点）

**⚠️ 重要**: Phase 0-7は別ブランチ `feature/data-generation-phase0-7` で完全実装完了

### スキーマバージョン
- **現在のバージョン**: v2.0.0（16テーブル、3NF正規化）
- **テーブル数**: 16テーブル（companies既存 + 15新規）
- **外部キー数**: 30個
- **実装ブランチ**: `feature/data-generation-phase0-7`

### テーブル別レコード数（Phase 0-7完了後）
| テーブル | レコード数 | Phase | 備考 |
|---------|-----------|-------|------|
| companies | 300社 | Phase 0.5 | 20業界以上 |
| sales_users | 5名 | Phase 1 | 営業担当者マスタ |
| competitor_profiles | 4社 | Phase 1 | Salesforce、HubSpot、kintone、Zoho CRM |
| stakeholders | 800-900名 | Phase 2 | 顧客側キーパーソン |
| deals | 2,251件 | Phase 2 | 業界標準CVR準拠 |
| deal_stakeholders | ~3,800件 | Phase 2 | 商談-ステークホルダーリンク |
| stakeholder_engagement | ~3,800件 | Phase 2 | エンゲージメント追跡 |
| deal_competitors | 大量生成 | Phase 2 | 商談-競合リンク |
| deal_details | 2,251件 | Phase 2 | 商談詳細情報 |
| deal_stage_history | 大量生成 | Phase 2 | ステージ履歴 |
| meetings | 大量生成 | Phase 3 | ミーティング記録 |
| meeting_attendees | 大量生成 | Phase 3 | 参加者リンク |
| emails | 大量生成 | Phase 5 | メール記録 |
| revenue_forecasts | 生成済み | Phase 2-7 | 売上予測 |
| forecast_deals | 生成済み | Phase 2-7 | 予測-商談リンク |
| cs_activities | 生成済み | Phase 7 | CS活動記録 |
| cs_activity_attendees | 生成済み | Phase 7 | CS活動参加者リンク |

### スキーマ変更履歴
- **v1.2.0 (2025-11-04)**: 4テーブル構成（deals: 48カラム）- Deprecated
- **v2.0.0 (2025-11-04)**: 16テーブル正規化版（3NF、30外部キー）- Current
  - 別ブランチ `feature/data-generation-phase0-7` で実装完了
  - Phase 0-7完了（22-28時間の実装）

---

**作成日**: 2025年11月3日
**最終更新**: 2025年11月6日
**プロジェクト**: Revenue Intelligence Platform
**役割**: データベース管理スクリプトの一元管理とドキュメント化
**現在のスキーマバージョン**: v2.0.0（16テーブル、3NF正規化、別ブランチ実装完了）
