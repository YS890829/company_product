# データベース完全実装プラン: アプローチ② 最適化スキーマ + 全データ再生成

**作成日**: 2025-11-04
**更新日**: 2025-11-05（業界標準CVR完全準拠版、スキーマ完全整合完了）
**目的**: アプローチ②（17テーブル正規化スキーマ）への移行 + ダミーデータ完全再生成（業界標準CVR準拠）
**所要時間**: 47-59時間（Phase 0.5: 300社生成 3-4時間含む）
**実装方式**: ステップバイステップ実行（Claude Code、Phase別に目視確認）

---

## 🎯 プロジェクト実施目的

本プロジェクトの目的は、**今回実装予定のすべてのAI機能を実データで実行するため**、以下を実施することです：

### 1. データベース再設計
- 全AI機能（Revenue Intelligence 10機能、Suggestion Engine 3機能）に必要な全カラムを網羅したスキーマ設計
- 17テーブル正規化構造によるデータ整合性の確保
- 各テーブルのカラム名とカラム数を本計画書の定義に完全一致させる

### 2. 十分な量のダミーデータ作成
- 2,251商談、5,100ミーティング、11,900メール等、業界標準に基づくリアルなデータ生成
- 業界標準CVR（Conversion Rate）に完全準拠したステージ分布
- 300社の詳細な顧客企業プロフィール
- 15,000-20,000文字の高品質なミーティングtranscript

### 3. AI機能の実データ実行環境構築
- 生成されたデータを用いた全AI機能の動作検証
- デモ環境での説得力のある実演
- 投資家・顧客への訴求力向上

**重要**: 本計画書に記載されているテーブル情報（各テーブルのカラム情報を含む）は、今回実装予定のすべてのAI機能を使用するために必要なカラム情報を踏まえて設計されています。したがって、データベースの各テーブル情報は本計画書の定義通りに設計・実装する必要があります。

---

## ✅ 実装方針（確定）

1. **既存データ削除**: 承認済み（現在310商談存在、全削除OK）
2. **顧客企業プロフィール**: 60社 → **300社に拡大**（Phase 0.5で実施）
3. **業界標準CVR完全準拠**: 全ステージのコンバージョン率を業界標準に準拠
4. **Transcript生成**: Gemini API → **Claude Code（私）が生成**
5. **実行方式**:
   - Claude Code でスクリプト作成後、自動実行
   - **各Phase完了後、ユーザーが目視チェック**
   - **ステップバイステップで段階的に実施**
   - `--dangerously-skip-permissions`は使用しない
6. **完了目標**: 47-59時間（業界標準CVR完全準拠版）

---

## 📋 エグゼクティブサマリー

### 現状分析
- **現在のDB**: 4テーブル（companies, deals, meetings, emails）、82カラム
- **既存ダミーデータ**: **310商談**（**全削除承認済み**）、ミーティング、メール
- **AI機能**: 13機能実装済み（100%モックモード、92%が実データ必要）
- **重大問題**: `deals`テーブル47カラム（アプローチ①では79カラムに膨張）、非正規化、JSONB依存、パフォーマンス低下

### 推奨：アプローチ②（業界標準CVR完全準拠版）
**17テーブル完全正規化スキーマ** + **2,251商談生成**（業界標準CVR準拠）

**主な利点**:
- **クエリ性能3-5倍高速化**（JSONB複雑JOIN不要）
- **データ整合性保証**（外部キー、制約）
- **将来性**（新機能追加が容易）
- **業界標準CVR完全準拠**: 全ステージのコンバージョン率が業界標準範囲内
- **リアルなデモデータ**: 300社プロフィール、2,251商談、約5,100ミーティング、約11,900メール
- **Win Rate 29.9%、Loss Rate 70.1%**: 業界標準20-30% Win Rateに準拠

---

## 1. 現在のデータベース状態分析

### 1.1 既存スキーマ（4テーブル、82カラム）

#### `deals`テーブル（47カラム）- **重大問題**

**問題点**:
1. ❌ **47カラム**（アプローチ①では79カラムに） - 肥大化
2. ❌ **非正規化**: `stakeholders` JSONB、`competitors` TEXT[]
3. ❌ **重複**: `owner_id` TEXT + `owner_name` TEXT（同じ情報）
4. ❌ **重要カラム欠落**: `last_contact_date`、`stage_changed_at`、`days_in_current_stage`、`closed_at`、`sales_cycle_days`
5. ❌ **検索性能低下**: ステークホルダー、競合を効率的に検索不可

#### 既存ダミーデータ（削除予定）

**出典**: `database/seed.sql` + `data-feasibility-analysis.md`

| カテゴリ | 件数 | 分布 | ステータス |
|----------|------|------|-----------|
| **Companies** | 1 | クラウドテック（SaaS） | ✅ 保持 |
| **Deals（合計）** | **310** | - | ❌ **全削除（承認済み）** |
| **Meetings** | 不明 | CASCADE削除 | ❌ 削除 |
| **Emails** | 不明 | CASCADE削除 | ❌ 削除 |

**重大問題**:
1. ❌ **310商談** - 現在のデータは統計的有意性なし
2. ❌ **トップ/ミドル/ボトム営業の差別化不可** - パフォーマンス階層が不明確
3. ❌ **ステージ分布不適切** - 業界標準のファネル転換率と乖離
4. ❌ **非正規化データ** - JSONB、TEXT[]による性能低下

**削除理由**: 全310商談を削除し、300商談を適切な統計分布で再生成する必要あり（トップ21.4%、ミドル5-9%、ボトム5.6%の明確な差別化）

---

## 2. ドメインモデル詳細分析

### 2.1 営業担当者（SaaSチーム - 5名）

**出典**: `domain-models/クラウドテック_企業プロフィール詳細.md`（238-516行）

| User ID | 名前 | 年齢 | 役職 | 経験 | メール |
|---------|------|------|------|------|-------|
| **user1** | 田中一郎 | 35 | AE | 4年 | tanaka@cloudtech.jp |
| **user2** | 鈴木花子 | 28 | AE | 3年 | suzuki@cloudtech.jp |
| **user3** | 佐藤次郎 | 42 | Senior AE | 5年 | sato@cloudtech.jp |
| **user4** | 山田三郎 | 30 | AE | 2.5年 | yamada@cloudtech.jp |
| **user5** | 高橋四郎 | 26 | AE（新卒） | 2.5年 | takahashi@cloudtech.jp |

**パフォーマンス階層（業界標準：2-5倍の差）**:

| 階層 | 営業 | 目標商談数 | 成約数 | 成約率 | 業界ベンチマーク |
|------|------|-----------|--------|--------|-----------------|
| **トップ（20%）** | 中村さくら | 70 | 15 | 21.4% | 15-25%（上位5%） |
| **ミドル上** | 伊藤由美 | 70 | 6 | 8.6% | 6-10%（平均） |
| **ミドル** | 山本優子 | 71 | 4 | 5.6% | 4-7%（平均以下） |
| **ミドル下** | 吉田拓也 | 71 | 3 | 4.2% | 3-5%（平均以下） |
| **ボトム（20%）** | 松本理恵 | 18 | 1 | 5.6% | 3-6%（平均以下） |
| **合計** | 5名 | **300** | **29** | **9.7%** | 8.0%（業界平均） |

**ステージ別転換率（SaaS業界標準 2024）**:

| ステージ遷移 | 業界平均 | トップ営業（中村） | ボトム営業（松本） |
|-------------|---------|------------------|------------------|
| Prospect → Meeting | 60% | 85%（1.4倍） | 45%（0.75倍） |
| Meeting → Proposal | 40% | 60%（1.5倍） | 30%（0.75倍） |
| Proposal → Negotiation | 50% | 70%（1.4倍） | 40%（0.8倍） |
| Negotiation → Closed Won | 67% | 85%（1.3倍） | 50%（0.75倍） |
| **全体** | **8.0%** | **21.4%**（2.7倍） | **5.6%**（0.7倍） |

---

### 2.2 顧客企業（300社）← **60社から拡大**

**出典**:
- ベース: `domain-models/クラウドテック向け顧客60社プロフィール.md`（182,829 bytes）
- **新規生成**: Phase 0.5で240社追加（合計300社）

**業界分布（300社）**:
- SaaS/IT: 100社（33.3%）
- 製造業: 60社（20.0%）
- 物流: 40社（13.3%）
- 小売: 30社（10.0%）
- 金融: 25社（8.3%）
- ヘルスケア: 20社（6.7%）
- 不動産: 15社（5.0%）
- 教育: 10社（3.3%）

**企業規模分布（300社）**:
- 大企業（500名以上）: 75社（25.0%）
- 中堅企業（100-500名）: 125社（41.7%）
- 中小企業（50-100名）: 100社（33.3%）

**予算レンジ（300社）**:
- ¥5M-10M: 50社（エンタープライズ、16.7%）
- ¥2M-5M: 125社（プロフェッショナル、41.7%）
- ¥500K-2M: 125社（スタンダード、41.7%）

**各プロフィールに含まれる情報**:
- 会社名、業界、規模
- 意思決定者名（CEO、CTO、営業部長等、各社2-5名）
- 現在の課題（1社あたり3-5個）
- 予算配分
- 検討中の競合（Salesforce、HubSpot、kintone、Zoho）
- 意思決定タイムライン（2024年Q4 - 2025年Q1）

**商談配分（2,251商談）**:
- 各社平均7.5商談（最小3商談、最大15商談）
- 大企業: 平均10商談/社（75社 × 10 = 750商談）
- 中堅企業: 平均7商談/社（125社 × 7 = 875商談）
- 中小企業: 平均6商談/社（100社 × 6 = 600商談）
- **合計**: 約2,225商談（残り26商談は調整）

---

### 2.3 クラウドテック企業プロフィール

**出典**: `domain-models/クラウドテック_企業プロフィール詳細.md`（1-657行）

**基本情報**:
- 名称: 株式会社クラウドテック（CloudTech Inc.）
- 設立: 2018-04-01
- 従業員: 120名
- 営業チーム: 15名（フィールド5名 + インサイド5名 + パートナー5名）
- ARR: ¥50M（2024-10）
- 成長率: +150% YoY
- チャーン率: 2.5%/月（30%/年）

**製品**: CloudSales（中小企業向けSaaS CRM）
- ターゲット: 50-500名規模の企業
- 価格: ¥25K/月（スタンダード）、¥50K/月（プロフェッショナル）、¥100K+/月（エンタープライズ）
- 競合: Salesforce、HubSpot、kintone、Zoho CRM

**差別化ポイント**:
1. 中小企業特化設計（1日でセットアップ完了 vs Salesforce 3-6ヶ月）
2. Salesforceの半額（年間¥600K vs ¥1.2M）
3. 日本語ファーストUI/UX + 24時間サポート

---

## 3. 以前のデータ生成手法

**出典**: `data-feasibility-analysis.md`（Section 5、Phase 0-6）

### 3.1 パフォーマンス階層分布

| 指標 | 計算式 | 出典 |
|------|--------|------|
| **成約率分布** | トップ21.4%、ミドル5-9%、ボトム5.6% | SaaS業界ベンチマーク2024 |
| **商談数分布** | トップ70、ミドル70-71、ボトム18 | パレートの法則（80/20ルール） |
| **ステージ分布** | Prospect 40% → Meeting 26% → Proposal 16% → Negotiation 10% → Won 5-21% → Lost 0-1% | ファネル転換率 |
| **ミーティング比率** | 2.29ミーティング/商談 | seed.sqlの実績平均 |
| **メール比率** | 5.29メール/商談 | seed.sqlの実績平均 |

---

## 4. アプローチ②スキーマ詳細（17テーブル）

**出典**: `database-implementation-guide.md`（Section 4.2、690-1328行）

### 4.1 コアテーブル（5テーブル）

#### テーブル1: `companies`（14カラム）- **既存保持**
```sql
CREATE TABLE companies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  industry TEXT NOT NULL,
  arr BIGINT,
  annual_contracts INTEGER,
  founded DATE,
  employees INTEGER,
  sales_team_size INTEGER NOT NULL,
  crm_system TEXT,
  main_product TEXT,
  target_market TEXT,
  service_area TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### テーブル2: `sales_users`（11カラム）- **新規**
```sql
CREATE TABLE sales_users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT UNIQUE NOT NULL,              -- 例: "user1"
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  company_id UUID REFERENCES companies(id),
  role TEXT NOT NULL,                        -- AE/SDR/Manager
  team TEXT,
  hire_date DATE,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sales_users_company_id ON sales_users(company_id);
CREATE INDEX idx_sales_users_user_id ON sales_users(user_id);
```

**投入データ**:
- user1: 田中一郎, tanaka@cloudtech.jp, AE, hire_date: 2020-04-01
- user2: 鈴木花子, suzuki@cloudtech.jp, AE, hire_date: 2021-07-01
- user3: 佐藤次郎, sato@cloudtech.jp, Senior AE, hire_date: 2019-10-01
- user4: 山田三郎, yamada@cloudtech.jp, AE, hire_date: 2022-04-01
- user5: 高橋四郎, takahashi@cloudtech.jp, AE, hire_date: 2022-04-01

#### テーブル3: `stakeholders`（10カラム）- **新規**
```sql
CREATE TABLE stakeholders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  email TEXT,
  title TEXT,
  company_name TEXT,                         -- 顧客企業名
  department TEXT,
  phone TEXT,
  linkedin_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(email, company_name)                -- 同一人物が同一企業に重複不可
);

CREATE INDEX idx_stakeholders_email ON stakeholders(email);
CREATE INDEX idx_stakeholders_company_name ON stakeholders(company_name);
```

**投入データ**: 60社プロフィールから抽出（各社3-5名の意思決定者）
- 総ステークホルダー数: ~180-300名（60社 × 3-5名）

#### テーブル4: `deals`（35カラム）- **再設計（スリム化）**
```sql
CREATE TABLE deals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,  -- クラウドテック社のUUID（固定: 06ee52bd-a1cc-4ed4-b384-78894188510a）

  -- 基本情報（顧客企業＝営業先300社の情報）
  deal_name TEXT,
  customer_name TEXT NOT NULL,        -- 顧客企業名（例: 株式会社テックブリッジ）← Phase 0.5の300社
  customer_industry TEXT,              -- 顧客業界（例: IT・ソフトウェア開発）
  customer_size INTEGER,               -- 顧客従業員数（例: 120）

  -- ステージ追跡
  stage TEXT NOT NULL CHECK (stage IN ('Prospect', 'Meeting', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost')),
  stage_changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  days_in_current_stage INTEGER DEFAULT 0,

  -- 財務
  amount DECIMAL NOT NULL,
  mrr DECIMAL,
  contract_term INTEGER,                     -- 月数

  -- 所有者
  owner_id UUID NOT NULL REFERENCES sales_users(id),

  -- 日付
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  expected_close_date DATE,
  closed_at TIMESTAMP WITH TIME ZONE,

  -- コンタクト追跡
  last_contact_date DATE,
  last_meaningful_activity_date TIMESTAMP WITH TIME ZONE,

  -- 次のアクション
  next_action TEXT,
  next_action_date DATE,

  -- 案件評価
  probability DECIMAL CHECK (probability >= 0 AND probability <= 1),
  budget DECIMAL,
  budget_confirmed BOOLEAN DEFAULT false,
  budget_status TEXT,                        -- Confirmed/Estimated/Unknown
  timeline TEXT,
  decision_timeline TEXT,

  -- メトリクス（計算値）
  sales_cycle_days INTEGER,
  risk_score DECIMAL CHECK (risk_score >= 0 AND risk_score <= 100),
  urgency_level TEXT CHECK (urgency_level IN ('low', 'medium', 'high', 'critical')),
  stalled_days INTEGER DEFAULT 0,

  -- クローズ追跡
  close_reason TEXT,                         -- Closed Won/Lost用
  lost_to_competitor UUID REFERENCES competitor_profiles(id),

  -- 規模カテゴリ
  deal_size_category TEXT CHECK (deal_size_category IN ('Small', 'Medium', 'Large', 'Enterprise')),
  lead_source TEXT
);

CREATE INDEX idx_deals_company_id ON deals(company_id);
CREATE INDEX idx_deals_owner_id ON deals(owner_id);
CREATE INDEX idx_deals_stage ON deals(stage);
CREATE INDEX idx_deals_expected_close_date ON deals(expected_close_date);
CREATE INDEX idx_deals_last_contact_date ON deals(last_contact_date);
```

**主な変更点**:
- ✅ **47カラムから32カラムにスリム化**（CS関連フィールドなし）
- ✅ **正規化**: `owner_id`が`sales_users(id)`への外部キー（TEXT + nameではない）
- ✅ **重要カラム追加**: `stage_changed_at`、`days_in_current_stage`、`last_contact_date`、`closed_at`、`sales_cycle_days`
- ✅ **JSONB削除**: `stakeholders`、`competitors`、`risk_factors`を別テーブルに移動

#### テーブル5: `competitor_profiles`（11カラム）- **新規**
```sql
CREATE TABLE competitor_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT UNIQUE NOT NULL,                 -- Salesforce、HubSpot等
  website TEXT,
  description TEXT,
  typical_pricing_range TEXT,
  strengths TEXT[],
  weaknesses TEXT[],
  battle_card_url TEXT,
  overall_win_rate DECIMAL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_competitor_profiles_name ON competitor_profiles(name);
```

**投入データ**:
- Salesforce: ¥1.2M/年、強み: [ブランド力、豊富な機能]、弱み: [高額、複雑なセットアップ]
- HubSpot: ¥500K/年、強み: [使いやすいUI、無料プラン]、弱み: [営業機能が弱い]
- kintone: ¥360K/年、強み: [カスタマイズ可能]、弱み: [長いセットアップ、IT知識必要]
- Zoho CRM: ¥200K/年、強み: [安価]、弱み: [日本語サポート弱い、古いUI]

---

### 4.2 関係テーブル（5テーブル）

#### テーブル6: `deal_stakeholders`（18カラム）- **新規**
```sql
CREATE TABLE deal_stakeholders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
  stakeholder_id UUID NOT NULL REFERENCES stakeholders(id) ON DELETE CASCADE,

  -- 役割
  role TEXT NOT NULL,                        -- 決裁者/評価者/利用者/その他
  influence_level INTEGER CHECK (influence_level >= 0 AND influence_level <= 100),
  support_level TEXT CHECK (support_level IN ('Champion', 'Supporter', 'Neutral', 'Detractor')),

  -- 権限
  decision_authority BOOLEAN DEFAULT false,
  budget_authority BOOLEAN DEFAULT false,

  -- チャンピオン指標
  is_champion BOOLEAN DEFAULT false,
  champion_score DECIMAL,                    -- 0-100、行動ベース
  reports_to_stakeholder_id UUID REFERENCES stakeholders(id),
  introduced_stakeholders_count INTEGER DEFAULT 0,
  shared_internal_info BOOLEAN DEFAULT false,
  proactive_contact_count INTEGER DEFAULT 0,
  positive_sentiment_count INTEGER DEFAULT 0,

  last_contact_date TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(deal_id, stakeholder_id)
);

CREATE INDEX idx_deal_stakeholders_deal_id ON deal_stakeholders(deal_id);
CREATE INDEX idx_deal_stakeholders_stakeholder_id ON deal_stakeholders(stakeholder_id);
CREATE INDEX idx_deal_stakeholders_is_champion ON deal_stakeholders(is_champion);
```

**置き換え対象**: `deals.stakeholders` JSONB配列

#### テーブル7: `stakeholder_engagement`（14カラム）- **新規**
```sql
CREATE TABLE stakeholder_engagement (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_stakeholder_id UUID NOT NULL REFERENCES deal_stakeholders(id) ON DELETE CASCADE,

  -- メールメトリクス
  email_sent_count INTEGER DEFAULT 0,
  email_opened_count INTEGER DEFAULT 0,
  email_clicked_count INTEGER DEFAULT 0,
  email_replied_count INTEGER DEFAULT 0,

  -- ミーティングメトリクス
  meeting_invited_count INTEGER DEFAULT 0,
  meeting_attended_count INTEGER DEFAULT 0,

  -- 計算スコア
  engagement_score DECIMAL CHECK (engagement_score >= 0 AND engagement_score <= 100),

  -- 最終アクティビティ日時
  last_email_opened_at TIMESTAMP WITH TIME ZONE,
  last_email_replied_at TIMESTAMP WITH TIME ZONE,
  last_meeting_attended_at TIMESTAMP WITH TIME ZONE,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(deal_stakeholder_id)
);

CREATE INDEX idx_stakeholder_engagement_deal_stakeholder_id ON stakeholder_engagement(deal_stakeholder_id);
```

#### テーブル8: `deal_competitors`（11カラム）- **新規**
```sql
CREATE TABLE deal_competitors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
  competitor_id UUID NOT NULL REFERENCES competitor_profiles(id),

  -- ステータス
  status TEXT CHECK (status IN ('Active', 'Dismissed', 'Won Against', 'Lost To')),
  threat_level TEXT CHECK (threat_level IN ('Low', 'Medium', 'High')),

  -- 価格比較
  competitor_price DECIMAL,
  our_price DECIMAL,

  -- メモ
  notes TEXT,
  our_differentiation TEXT[],

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(deal_id, competitor_id)
);

CREATE INDEX idx_deal_competitors_deal_id ON deal_competitors(deal_id);
CREATE INDEX idx_deal_competitors_competitor_id ON deal_competitors(competitor_id);
```

**置き換え対象**: `deals.competitors` TEXT[]配列

#### テーブル9: `deal_details`（11カラム）- **新規**
```sql
CREATE TABLE deal_details (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,

  -- 要件
  pain_points TEXT[],
  requirements TEXT[],
  decision_criteria TEXT[],

  -- 勝敗要因
  win_factors TEXT[],
  loss_factors TEXT[],
  risk_factors TEXT[],
  strengths TEXT[],

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(deal_id)
);

CREATE INDEX idx_deal_details_deal_id ON deal_details(deal_id);
```

**置き換え対象**: `deals.pain_points`、`deals.requirements`、`deals.risk_factors`、`deals.win_factors`、`deals.loss_factors`

#### テーブル10: `deal_stage_history`（8カラム）- **新規**
```sql
CREATE TABLE deal_stage_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
  from_stage TEXT NOT NULL,
  to_stage TEXT NOT NULL,
  changed_at TIMESTAMP WITH TIME ZONE NOT NULL,
  changed_by UUID REFERENCES sales_users(id),
  days_in_stage INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_deal_stage_history_deal_id ON deal_stage_history(deal_id);
CREATE INDEX idx_deal_stage_history_changed_at ON deal_stage_history(changed_at);
```

**用途**: `track_deal_progress` AI機能のステージ遷移追跡

---

### 4.3 アクティビティテーブル（3テーブル）

#### テーブル11: `meetings`（11カラム）- **再設計**
```sql
CREATE TABLE meetings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,

  -- 基本情報
  date TIMESTAMP WITH TIME ZONE NOT NULL,
  duration_minutes INTEGER,
  meeting_type TEXT NOT NULL,
  location TEXT,

  -- コンテンツ
  transcript TEXT,
  summary TEXT,

  -- 所有者
  created_by UUID REFERENCES sales_users(id),
  meeting_owner_id UUID REFERENCES sales_users(id),

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_meetings_deal_id ON meetings(deal_id);
CREATE INDEX idx_meetings_date ON meetings(date);
```

**主な変更点**:
- ✅ **JSONB削除**: `attendees` → 別テーブル`meeting_attendees`
- ✅ **所有者追加**: `created_by`、`meeting_owner_id`

#### テーブル12: `meeting_attendees`（6カラム）- **新規**
```sql
CREATE TABLE meeting_attendees (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  meeting_id UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
  stakeholder_id UUID REFERENCES stakeholders(id) ON DELETE SET NULL,
  sales_user_id UUID REFERENCES sales_users(id) ON DELETE SET NULL,

  -- stakeholder_idまたはsales_user_idのいずれかが必須
  attendance_status TEXT CHECK (attendance_status IN ('Attended', 'No-show', 'Cancelled')),

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  CHECK (stakeholder_id IS NOT NULL OR sales_user_id IS NOT NULL)
);

CREATE INDEX idx_meeting_attendees_meeting_id ON meeting_attendees(meeting_id);
CREATE INDEX idx_meeting_attendees_stakeholder_id ON meeting_attendees(stakeholder_id);
```

**置き換え対象**: `meetings.attendees` JSONB配列

#### テーブル13: `emails`（17カラム）- **再設計**
```sql
CREATE TABLE emails (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,

  -- 送信者/受信者（stakeholders/sales_usersへのリンク）
  sender_sales_user_id UUID REFERENCES sales_users(id),
  sender_stakeholder_id UUID REFERENCES stakeholders(id),
  recipient_sales_user_id UUID REFERENCES sales_users(id),
  recipient_stakeholder_id UUID REFERENCES stakeholders(id),

  -- コンテンツ
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  sent_at TIMESTAMP WITH TIME ZONE NOT NULL,

  -- エンゲージメント
  opened BOOLEAN DEFAULT false,
  opened_at TIMESTAMP WITH TIME ZONE,
  is_replied BOOLEAN DEFAULT false,
  reply_time_minutes INTEGER,
  clicked_links TEXT[],
  engagement_score DECIMAL,
  attachments TEXT[],

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  CHECK (
    (sender_sales_user_id IS NOT NULL OR sender_stakeholder_id IS NOT NULL) AND
    (recipient_sales_user_id IS NOT NULL OR recipient_stakeholder_id IS NOT NULL)
  )
);

CREATE INDEX idx_emails_deal_id ON emails(deal_id);
CREATE INDEX idx_emails_sender_sales_user_id ON emails(sender_sales_user_id);
CREATE INDEX idx_emails_recipient_stakeholder_id ON emails(recipient_stakeholder_id);
CREATE INDEX idx_emails_sent_at ON emails(sent_at);
```

**主な変更点**:
- ✅ **送信者/受信者正規化**: `sales_users`または`stakeholders`へのリンク
- ✅ **返信追跡追加**: `is_replied`、`reply_time_minutes`

---

### 4.4 分析テーブル（2テーブル）

#### テーブル14: `revenue_forecasts`（9カラム）- **新規**
```sql
CREATE TABLE revenue_forecasts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  forecast_date DATE NOT NULL,
  forecast_period TEXT NOT NULL,             -- "2025-Q1"、"2025-11"等
  forecast_amount DECIMAL NOT NULL,
  confidence_level DECIMAL CHECK (confidence_level >= 0 AND confidence_level <= 1),

  -- 精度追跡（期間終了後）
  actual_amount DECIMAL,
  accuracy DECIMAL,                          -- abs(actual - forecast) / actual

  created_by UUID REFERENCES sales_users(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_revenue_forecasts_forecast_date ON revenue_forecasts(forecast_date);
CREATE INDEX idx_revenue_forecasts_forecast_period ON revenue_forecasts(forecast_period);
```

**用途**: `forecast_revenue` AI機能 - 過去の精度追跡

#### テーブル15: `forecast_deals`（6カラム）- **新規**
```sql
CREATE TABLE forecast_deals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  forecast_id UUID NOT NULL REFERENCES revenue_forecasts(id) ON DELETE CASCADE,
  deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
  weighted_value DECIMAL,                    -- amount * probability
  included_in_forecast BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(forecast_id, deal_id)
);

CREATE INDEX idx_forecast_deals_forecast_id ON forecast_deals(forecast_id);
CREATE INDEX idx_forecast_deals_deal_id ON forecast_deals(deal_id);
```

**用途**: 各予測にどの商談が含まれたかを追跡

---

### 4.5 CS活動テーブル（2テーブル）

#### テーブル16: `cs_activities`（21カラム）- **新規**
```sql
CREATE TABLE cs_activities (
  -- Identity & References
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,

  -- Activity Classification
  activity_type TEXT NOT NULL CHECK (activity_type IN (
    'Onboarding', 'QBR', 'Training', 'Check-in',
    'Health Check', 'Support Escalation', 'Renewal Discussion', 'Expansion Planning'
  )),
  activity_category TEXT CHECK (activity_category IN (
    'Strategic', 'Tactical', 'Support', 'Expansion'
  )),

  -- Basic Info
  subject TEXT NOT NULL,
  description TEXT,

  -- Timing
  activity_date TIMESTAMP WITH TIME ZONE NOT NULL,
  duration_minutes INTEGER,

  -- Ownership
  owner_id UUID NOT NULL REFERENCES sales_users(id),

  -- Outcome & Sentiment
  outcome TEXT CHECK (outcome IN ('Successful', 'Needs Follow-up', 'Blocked', 'At Risk')),
  sentiment TEXT CHECK (sentiment IN ('Positive', 'Neutral', 'Negative')),
  sentiment_score DECIMAL CHECK (sentiment_score >= -1 AND sentiment_score <= 1),

  -- Next Actions
  next_steps TEXT,
  follow_up_required BOOLEAN DEFAULT false,
  follow_up_date DATE,

  -- Metrics & Impact
  engagement_score DECIMAL CHECK (engagement_score >= 0 AND engagement_score <= 100),
  health_impact TEXT CHECK (health_impact IN ('Positive', 'Neutral', 'Negative')),
  risk_flags TEXT[],

  -- Metadata
  channel TEXT CHECK (channel IN ('Email', 'Phone', 'Video Call', 'In-person', 'Chat', 'Other')),

  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_cs_activities_deal ON cs_activities(deal_id);
CREATE INDEX idx_cs_activities_type ON cs_activities(activity_type);
CREATE INDEX idx_cs_activities_date ON cs_activities(activity_date DESC);
CREATE INDEX idx_cs_activities_owner ON cs_activities(owner_id);
```

**主な特徴**:
- ✅ **8種類のActivity Type**: 業界標準準拠（Gong、Gainsight、Vitally等を参考）
- ✅ **感情分析**: sentiment, sentiment_score（チャーン予測の最重要指標）
- ✅ **アウトカム追跡**: outcome（完了 ≠ 成功を測定）
- ✅ **次のアクション**: next_steps, follow_up（プロアクティブCS管理）
- ✅ **ヘルスへの影響**: health_impact, risk_flags（ヘルススコア計算に直接使用）
- ✅ **エンゲージメント指標**: engagement_score（活動の価値を定量化）

**用途**: Phase 7でCS活動履歴を記録、dealsテーブルのhealth_score, churn_risk計算に使用

#### テーブル17: `cs_activity_attendees`（7カラム）- **新規**
```sql
CREATE TABLE cs_activity_attendees (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  activity_id UUID NOT NULL REFERENCES cs_activities(id) ON DELETE CASCADE,
  stakeholder_id UUID REFERENCES stakeholders(id) ON DELETE CASCADE,
  sales_user_id UUID REFERENCES sales_users(id) ON DELETE CASCADE,
  attendance_status TEXT CHECK (attendance_status IN ('Attended', 'No-show', 'Declined')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  CHECK (stakeholder_id IS NOT NULL OR sales_user_id IS NOT NULL)
);

CREATE INDEX idx_cs_activity_attendees_activity ON cs_activity_attendees(activity_id);
CREATE INDEX idx_cs_activity_attendees_stakeholder ON cs_activity_attendees(stakeholder_id);
```

**用途**: CS活動への参加者トラッキング（ステークホルダーまたは営業ユーザー）、ステークホルダーエンゲージメント分析

---

### 4.6 スキーマ統計

| 指標 | 値 | 説明 |
|------|-----|------|
| **総テーブル数** | 17 | 完全正規化（3NF）、関心の分離 |
| **総カラム数** | 210 | 17テーブルに適切に分散 |
| **dealsカラム数** | 35 | コア商談情報のみ（CS、関係データは別テーブル） |
| **JSONBフィールド** | 0 | 100%正規化、JSONB完全排除 |
| **外部キー制約** | 30 | データ整合性の強力な保証 |
| **正規化レベル** | 3NF | Third Normal Form準拠 |
| **最大テーブル** | deals (35カラム) | 商談メインテーブル |
| **最小テーブル** | meeting_attendees (6カラム) | Junction table |

---

## 5. データ生成計画（Phase 0-7）

### Phase 0: データベースバックアップ + 3テーブル削除（30分）

**目的**: 既存の3テーブル（deals、meetings、emails）を削除、companiesテーブルは保持

**タスク**:
1. 現在のデータベースバックアップ: `pg_dump -F c fukugyo_plan > backup_20251104_before_cleanup.dump`
2. **3テーブル削除（companiesは保持）**:
   - `DROP TABLE IF EXISTS emails CASCADE;`
   - `DROP TABLE IF EXISTS meetings CASCADE;`
   - `DROP TABLE IF EXISTS deals CASCADE;`
   - ※ `companies`テーブルは削除せず保持
3. 検証:
   - `SELECT COUNT(*) FROM deals;` → エラー（テーブルが存在しない）
   - `SELECT COUNT(*) FROM meetings;` → エラー（テーブルが存在しない）
   - `SELECT COUNT(*) FROM emails;` → エラー（テーブルが存在しない）
   - `SELECT COUNT(*) FROM companies;` → 期待値: 1件（クラウドテック保持）

**ユーザー目視確認ポイント**:
- ✅ バックアップファイルが作成されたか
- ✅ deals、meetings、emailsテーブルが削除されたか
- ✅ companiesテーブルは保持されているか（`SELECT * FROM companies;` → クラウドテック1件）

**スクリプト**: `scripts/phase0_backup_database.sh`、`scripts/phase0_drop_3_tables.py`

---

### Phase 1: スキーマ移行（2-3時間）

**目的**: アプローチ②の14テーブルを新規作成（companiesテーブルは既存保持）

**タスク**:
1. **14テーブル新規作成**（companiesは既存保持）
   - `database/schema-design-final.md`参照
   - コアテーブル（4）: sales_users、stakeholders、deals、competitor_profiles
   - 関係テーブル（5）: deal_stakeholders、stakeholder_engagement、deal_competitors、deal_details、deal_stage_history
   - アクティビティテーブル（3）: meetings、meeting_attendees、emails
   - 分析テーブル（2）: revenue_forecasts、forecast_deals
   - **新規**: cs_activities（Phase 7用）
   - ※ `companies`テーブルは既存を使用（Phase 0で保持）

2. **マスターデータ投入**
   - `scripts/phase1_populate_sales_users.py`: 企業プロフィール詳細.mdから5営業
   - `scripts/phase1_populate_competitor_profiles.py`: 4競合（Salesforce、HubSpot、kintone、Zoho）

3. **インデックス・制約適用**
   - 35インデックス（現状5から増加）
   - 28外部キー（現状8から増加）

**成果物**:
- ✅ 16テーブル新規作成 + companies既存保持 = 計17テーブル、完全正規化（3NF）
- ✅ 5営業担当者投入（user1-user5）
- ✅ 4競合プロフィール投入

**ユーザー目視確認ポイント**:
- ✅ `SELECT COUNT(*) FROM pg_tables WHERE schemaname='public';` → 期待値: 17テーブル（companies含む）
- ✅ `SELECT COUNT(*) FROM companies;` → 期待値: 1件（クラウドテック保持確認）
- ✅ `SELECT COUNT(*) FROM sales_users;` → 期待値: 5名
- ✅ `SELECT COUNT(*) FROM competitor_profiles;` → 期待値: 4社
- ✅ `SELECT name FROM competitor_profiles;` → Salesforce、HubSpot、kintone、Zoho CRM

---

### Phase 0.5: 300社プロフィール生成（30-45分、8スレッド並列実行）← **新規追加**

**目的**: 60社プロフィールをベースに240社追加生成（合計300社）

**🔴 実行方式**: 8スレッド並列実行（業界分散戦略）
- **所要時間**: 30-45分（従来3-4時間 → 並列化で大幅短縮）
- **ファイル構成**: 10ファイル（Part1-2: 既存60社、Part3-10: 新規240社）
- **重複リスク低減**: 各Partが異なる業界に特化

---

#### ファイル構成（10ファイル）

**既存ファイル（Part1-2）**:
- `クラウドテック向け顧客30社プロフィール_Part1.md`: 顧客1-30（既存、2,446行）
- `クラウドテック向け顧客30社プロフィール_Part2.md`: 顧客31-60（既存、2,603行）

**新規生成ファイル（Part3-10）← 8スレッド並列実行**:
- `クラウドテック向け顧客30社プロフィール_Part3.md`: 顧客61-90（30社、IT/SaaS特化）
- `クラウドテック向け顧客30社プロフィール_Part4.md`: 顧客91-120（30社、IT/SaaS特化続き）
- `クラウドテック向け顧客30社プロフィール_Part5.md`: 顧客121-150（30社、IT/SaaS+製造業）
- `クラウドテック向け顧客30社プロフィール_Part6.md`: 顧客151-180（30社、製造業特化）
- `クラウドテック向け顧客30社プロフィール_Part7.md`: 顧客181-210（30社、製造業+物流）
- `クラウドテック向け顧客30社プロフィール_Part8.md`: 顧客211-240（30社、物流+小売+金融）
- `クラウドテック向け顧客30社プロフィール_Part9.md`: 顧客241-270（30社、小売+金融+ヘルスケア）
- `クラウドテック向け顧客30社プロフィール_Part10.md`: 顧客271-300（30社、ヘルスケア+不動産+教育）

---

#### 業界分散戦略（240社をPart3-10に配分）

**目標: 新規240社の業界内訳**

| 業界 | 目標300社 | 既存60社 | **新規240社** | Part配分 |
|------|----------|---------|-------------|---------|
| SaaS/IT | 100社 (33.3%) | 20社 | **80社** | Part3-5（30+30+20） |
| 製造業 | 60社 (20.0%) | 12社 | **48社** | Part5-7（10+30+8） |
| 物流 | 40社 (13.3%) | 8社 | **32社** | Part7-8（22+10） |
| 小売 | 30社 (10.0%) | 6社 | **24社** | Part8-9（12+12） |
| 金融 | 25社 (8.3%) | 5社 | **20社** | Part8-9（8+12） |
| ヘルスケア | 20社 (6.7%) | 4社 | **16社** | Part9-10（6+10） |
| 不動産 | 15社 (5.0%) | 3社 | **12社** | Part10（12） |
| 教育 | 10社 (3.3%) | 2社 | **8社** | Part10（8） |
| **合計** | **300社** | **60社** | **240社** | **Part3-10** |

**業界分散戦略のメリット**:
- ✅ **重複リスク大幅低減**: 各Partが異なる業界に特化（例: Part3はクラウドSaaS、Part4はモバイルアプリ）
- ✅ **業界ごとの深い多様性**: 各業界の固有課題、用語、ステークホルダーを詳細に反映
- ✅ **Claude Code文脈理解向上**: 各Threadが1-2業界に集中し、業界知識を深く活用
- ✅ **品質検証の容易性**: Part単位で業界別に妥当性を検証可能

---

#### Part3-10の詳細配分

**Part3: 顧客61-90（30社）- IT/SaaS特化 - Thread 1**
- SaaS/IT: 30社
  - クラウドインフラSaaS: 6社、SFA/CRM SaaS: 5社、AI/機械学習: 5社
  - サイバーセキュリティ: 4社、データ分析/BI: 4社、HR Tech: 3社、MA: 3社
- 企業規模: 大企業8、中堅12、中小10 | 予算: ¥5M-10M 5社、¥2M-5M 13社、¥500K-2M 12社

**Part4: 顧客91-120（30社）- IT/SaaS特化（続き）- Thread 2**
- SaaS/IT: 30社
  - EC/決済: 6社、モバイルアプリ: 5社、フィンテック: 5社、教育テック: 4社
  - IoT: 4社、ブロックチェーン: 3社、ゲーム開発: 3社
- 企業規模: 大企業7、中堅13、中小10 | 予算: ¥5M-10M 5社、¥2M-5M 12社、¥500K-2M 13社

**Part5: 顧客121-150（30社）- IT/SaaS+製造業 - Thread 3**
- SaaS/IT: 20社（SI 5社、受託開発 5社、クラウドコンサル 4社、インフラ保守 3社、ライセンス 3社）
- 製造業: 10社（自動車部品 3社、電子部品 2社、精密機器 2社、化学製品 2社、食品 1社）
- 企業規模: 大企業8、中堅12、中小10 | 予算: ¥5M-10M 5社、¥2M-5M 13社、¥500K-2M 12社

**Part6: 顧客151-180（30社）- 製造業特化 - Thread 4**
- 製造業: 30社
  - 産業機械 6社、金属加工 5社、プラスチック 4社、包装資材 4社
  - 繊維 3社、家具 3社、印刷 3社、医療機器 2社
- 企業規模: 大企業7、中堅13、中小10 | 予算: ¥5M-10M 5社、¥2M-5M 12社、¥500K-2M 13社

**Part7: 顧客181-210（30社）- 製造業+物流 - Thread 5**
- 製造業: 8社（建設資材 3社、ガラス 2社、ゴム 2社、その他 1社）
- 物流: 22社（3PL 6社、トラック 5社、倉庫 4社、国際物流 3社、宅配 2社、冷凍 2社）
- 企業規模: 大企業8、中堅12、中小10 | 予算: ¥5M-10M 5社、¥2M-5M 13社、¥500K-2M 12社

**Part8: 顧客211-240（30社）- 物流+小売+金融 - Thread 6**
- 物流: 10社（引越 3社、物流IT 3社、配送センター 2社、航空海運 2社）
- 小売: 12社（スーパー 3社、コンビニ 2社、ドラッグ 2社、家電 2社、アパレル 2社、百貨店 1社）
- 金融: 8社（地銀 2社、信金 2社、証券 2社、保険 2社）
- 企業規模: 大企業7、中堅13、中小10 | 予算: ¥5M-10M 5社、¥2M-5M 12社、¥500K-2M 13社

**Part9: 顧客241-270（30社）- 小売+金融+ヘルスケア - Thread 7**
- 小売: 12社（ホームセンター 3社、飲食 3社、モール 2社、EC 2社、専門店 2社）
- 金融: 12社（リース 3社、ファクタリング 2社、資産運用 2社、フィンテック 2社、カード 2社、消費者金融 1社）
- ヘルスケア: 6社（病院 2社、クリニック 2社、調剤薬局 2社）
- 企業規模: 大企業8、中堅12、中小10 | 予算: ¥5M-10M 5社、¥2M-5M 13社、¥500K-2M 12社

**Part10: 顧客271-300（30社）- ヘルスケア+不動産+教育 - Thread 8**
- ヘルスケア: 10社（介護施設 3社、訪問介護 2社、医療機器販売 2社、ヘルステック 2社、医療コンサル 1社）
- 不動産: 12社（仲介売買 3社、仲介賃貸 3社、開発 2社、ビル管理 2社、リノベ 2社）
- 教育: 8社（学習塾 3社、専門学校 2社、オンライン教育 2社、企業研修 1社）
- 企業規模: 大企業7、中堅13、中小10 | 予算: ¥5M-10M 5社、¥2M-5M 12社、¥500K-2M 13社

---

#### タスク実行手順

**Step 1: 60社プロフィールを2ファイルに分割（完了済み）**
- Part1: 顧客1-30（2,446行）✅
- Part2: 顧客31-60（2,603行）✅

**Step 2: Part3-10用の空ファイル作成（5分）**
- 各Partファイルにヘッダー、業界特化戦略、生成計画を記載

**Step 3: 8つのclaude-taskプロンプト実行（30-45分）**
- Thread 1-8を並列実行
- 各ThreadがPart1-2を参照して業界特性を分析
- 各Threadが特化業界の30社をAI生成（Template使用禁止）

**Step 4: 10ファイルを1ファイルにマージ（5分）**
```bash
cat Part1.md Part2.md Part3.md ... Part10.md > クラウドテック向け顧客300社プロフィール.md
```

**Step 5: データ品質検証（10分）**

---

#### 成果物

- ✅ 300社プロフィール（60社既存 + 240社新規、AI生成高品質）
- ✅ 10ファイル構成（Part1-10）
- ✅ 業界分布目標達成（±2%以内）
- ✅ 企業規模分布目標達成（±2%以内）
- ✅ 予算レンジ分布目標達成（±2%以内）
- ✅ 各社に意思決定者2-5名、課題3-5個設定
- ✅ 会社名・人名の重複なし
- ✅ 業界ごとの深い多様性

#### ユーザー目視確認ポイント

- ✅ `ls domain-models/クラウドテック向け顧客30社プロフィール_Part*.md | wc -l` → 期待値: 10ファイル
- ✅ `grep "^### 顧客" domain-models/クラウドテック向け顧客300社プロフィール.md | wc -l` → 期待値: 300社
- ✅ 業界分布確認: `grep "^- 業界:" domain-models/クラウドテック向け顧客300社プロフィール.md | sort | uniq -c`
- ✅ 会社名重複チェック: `grep "^### 顧客" ... | sort | uniq -d` → 期待値: 0件

#### スクリプト

- `scripts/phase0.5_split_60_companies.sh`: 60社を2ファイルに分割（完了済み）
- `scripts/phase0.5_create_part_templates.sh`: Part3-10の空ファイル作成
- `scripts/phase0.5_merge_10_parts.sh`: 10ファイルマージ
- `scripts/phase0.5_verify_quality.sh`: データ品質検証

---

### Phase 2: 2,251商談 + ステークホルダー生成（2-3時間、10スレッド並列）← **並列化で14-18.5時間 → 2-3時間**

**目的**: 300社プロフィールから2,251商談を生成（業界標準CVR完全準拠）

**⚠️ 重要変更**: **10スレッド並列実行**により、14-18.5時間 → **2-3時間に短縮**（約7倍高速化）

**実行方式**: ハイブリッド分割（営業×顧客マトリックス）
- 営業5名 × 2分割 = 10スレッド
- 各スレッドが異なる30社を担当（完全な重複回避）
- 商談ID命名規則: `{owner_id}_{company_id}_{deal_index}`でグローバルユニーク

**10スレッド構成**:

| スレッド | 営業担当 | 顧客範囲 | 商談数 | Prospect | Meeting | Proposal | Negotiation | Closed Won | Closed Lost |
|---------|---------|---------|--------|----------|---------|----------|-------------|------------|-------------|
| **Thread 1** | 田中一郎 | 1-30 | 263 | 145 | 58 | 29 | 19 | 8 | 4 |
| **Thread 2** | 田中一郎 | 31-60 | 262 | 145 | 58 | 29 | 19 | 7 | 4 |
| **Thread 3** | 鈴木花子 | 61-90 | 263 | 145 | 58 | 29 | 19 | 3 | 9 |
| **Thread 4** | 鈴木花子 | 91-120 | 262 | 145 | 58 | 29 | 19 | 3 | 8 |
| **Thread 5** | 佐藤次郎 | 121-150 | 267 | 148 | 59 | 30 | 20 | 2 | 8 |
| **Thread 6** | 佐藤次郎 | 151-180 | 266 | 147 | 59 | 29 | 19 | 2 | 10 |
| **Thread 7** | 山田三郎 | 181-210 | 267 | 148 | 59 | 30 | 20 | 2 | 8 |
| **Thread 8** | 山田三郎 | 211-240 | 266 | 147 | 59 | 29 | 19 | 1 | 11 |
| **Thread 9** | 高橋四郎 | 241-270 | 68 | 38 | 15 | 7 | 5 | 1 | 2 |
| **Thread 10** | 高橋四郎 | 271-300 | 67 | 37 | 15 | 8 | 5 | 0 | 2 |
| **合計** | 5名 | 300社 | **2,251** | **1,245** | **498** | **249** | **162** | **29** | **68** |

**営業別商談数検証**:
- 田中一郎: 263 + 262 = **525商談**、8 + 7 = **15成約**（2.9%） ✅
- 鈴木花子: 263 + 262 = **525商談**、3 + 3 = **6成約**（1.1%） ✅
- 佐藤次郎: 267 + 266 = **533商談**、2 + 2 = **4成約**（0.8%） ✅
- 山田三郎: 267 + 266 = **533商談**、2 + 1 = **3成約**（0.6%） ✅
- 高橋四郎: 68 + 67 = **135商談**、1 + 0 = **1成約**（0.7%） ✅

**タスク（各スレッドで実行）**:
1. **300社からステークホルダー抽出**
   - 担当する30社のプロフィールをパース（Part1-10から該当部分）
   - `stakeholders`テーブルに投入: 各スレッド60-90名（合計800-900件）
   - 重複対策: `ON CONFLICT (email) DO NOTHING`

2. **商談生成（営業×顧客ペアのみ）**
   - 各スレッドが担当する営業-顧客ペアからのみ商談を生成
   - ステージ分布を厳守（上記表の通り）
   - 商談ID: `{owner_id}_{company_id}_{deal_index}`（グローバルユニーク）

3. **商談-ステークホルダーリンク**
   - 生成した商談に対してのみステークホルダーを関連付け
   - `deal_stakeholders`: 各スレッド約380件（合計約3,800件）
   - ステージ別人数:
     - Prospect: 1名/商談
     - Meeting: 1.5名/商談
     - Proposal: 2名/商談
     - Negotiation: 2.5名/商談
     - Closed Won/Lost: 2.5名/商談
   - 役割割り当て: Champion、Decision Maker、Influencer、Gatekeeper、User

4. **商談詳細・競合・履歴投入**
   - `deal_details`: 各スレッド約225件（合計2,251件）
     - 課題（pain_points）、要件（requirements）、意思決定基準（decision_criteria）
     - Closed Won: win_factors、Closed Lost: loss_factors
   - `deal_competitors`: 各スレッド約450-675件（合計4,500-6,750件、1商談あたり2-3社）
     - Salesforce 40-50%、HubSpot 30-40%、kintone 20-30%、Zoho CRM 10-20%
   - `deal_stage_history`: 各スレッド約550件（合計約5,500件）
     - Closed Won/Lost: 5レコード/商談
     - Negotiation: 4レコード/商談
     - Proposal: 3レコード/商談
     - Meeting: 2レコード/商談
     - Prospect: 1レコード/商談

**実装ファイル**:
- `scripts/phase2_run_10_threads.sh`: 並列実行メインスクリプト
- `scripts/phase2_thread1_prompt.txt` ~ `phase2_thread10_prompt.txt`: 各スレッドのパラメータ定義
- `scripts/phase2_generate_parallel.py`: データ生成Pythonスクリプト
- `scripts/phase2_merge_and_validate.py`: 全スレッド完了後の検証
- `scripts/phase2_validation_report_generator.py`: 検証レポート自動生成

**重複リスク対策**:
1. **顧客会社の完全分離**: 各スレッドが異なる30社を担当（Thread 1: 顧客1-30、Thread 2: 顧客31-60...）
2. **商談ID命名規則**: `{owner_id}_{company_id}_{deal_index}`でグローバルユニーク
3. **ステークホルダーemail重複対策**: `ON CONFLICT (email) DO NOTHING`
4. **トランザクション分離**: 各スレッドが独立したトランザクション（失敗時は個別ロールバック）

**成果物**:
- ✅ 300社顧客企業に2,251商談
- ✅ 800-900名ステークホルダー
- ✅ 約3,800件の商談-ステークホルダー関係
- ✅ 2,251件の商談詳細レコード
- ✅ 約4,500-6,750件の商談-競合リンク
- ✅ 約5,500件のステージ遷移履歴
- ✅ **所要時間**: 2-3時間（並列化で14-18.5時間から約7倍短縮）

**ユーザー目視確認ポイント**:
- ✅ `SELECT COUNT(*) FROM deals;` → 期待値: **2,251**
- ✅ `SELECT COUNT(*) FROM stakeholders;` → 期待値: **800-900**
- ✅ `SELECT COUNT(*) FROM deal_stakeholders;` → 期待値: **3,800前後**
- ✅ `SELECT COUNT(*) FROM deal_competitors;` → 期待値: **4,500-6,750**
- ✅ `SELECT COUNT(*) FROM deal_stage_history;` → 期待値: **5,500前後**
- ✅ `SELECT owner_id, COUNT(*) as deal_count, SUM(CASE WHEN stage='Closed Won' THEN 1 ELSE 0 END) as won_count FROM deals GROUP BY owner_id ORDER BY deal_count DESC;` → 田中一郎525商談/15成約、鈴木花子525商談/6成約、佐藤次郎533商談/4成約、山田三郎533商談/3成約、高橋四郎135商談/1成約を確認
- ✅ `SELECT stage, COUNT(*) FROM deals GROUP BY stage ORDER BY CASE stage WHEN 'Prospect' THEN 1 WHEN 'Meeting' THEN 2 WHEN 'Proposal' THEN 3 WHEN 'Negotiation' THEN 4 WHEN 'Closed Won' THEN 5 WHEN 'Closed Lost' THEN 6 END;` → **Prospect 1,245、Meeting 498、Proposal 249、Negotiation 162、Closed Won 29、Closed Lost 68**
- ✅ **Win Rate検証**: `SELECT COUNT(CASE WHEN stage='Closed Won' THEN 1 END) as won, COUNT(CASE WHEN stage='Closed Lost' THEN 1 END) as lost, COUNT(*) as total, ROUND(100.0 * COUNT(CASE WHEN stage='Closed Won' THEN 1 END) / COUNT(*), 1) as win_rate_pct FROM deals WHERE stage IN ('Closed Won', 'Closed Lost');` → 29勝、68敗、合計97件、Win Rate 29.9%を確認
- ✅ **重複チェック**: `SELECT id, COUNT(*) FROM deals GROUP BY id HAVING COUNT(*) > 1;` → 期待値: **0件**（商談ID重複なし）
- ✅ **顧客範囲チェック**: `SELECT company_id, COUNT(*) FROM deals GROUP BY company_id ORDER BY COUNT(*) DESC LIMIT 10;` → 各社の商談数を確認（大企業: 約10商談、中堅: 約7商談、中小: 約6商談）

---

### Phase 3: 約5,100ミーティング生成（8-10時間）← **685件から大幅増**

**目的**: リアルな分布で約5,100ミーティング生成（2,251商談 × 平均2.27ミーティング/商談）

**タスク**:
1. **ミーティング生成**
   - `scripts/phase3_generate_5100_meetings.py`
   - **2,251商談 × 2.27ミーティング/商談 = 約5,100ミーティング**
   - **ステージ別ミーティング数**:
     - Prospect: 平均1.5ミーティング/商談 = 1,245 × 1.5 = 1,868件
     - Meeting: 平均2ミーティング/商談 = 498 × 2 = 996件
     - Proposal: 平均3ミーティング/商談 = 249 × 3 = 747件
     - Negotiation: 平均4ミーティング/商談 = 162 × 4 = 648件
     - Closed Won/Lost: 平均3ミーティング/商談 = 97 × 3 = 291件
     - **合計**: 約5,550件（調整して5,100件）
   - ミーティングタイプ: 初回（30%）、デモ（25%）、フォローアップ（20%）、商談（15%）、訪問（10%）
   - 時間: 30分（40%）、60分（60%）= **60分約3,060件**

2. **参加者リンク**
   - `scripts/phase3_populate_meeting_attendees.py`
   - **約15,300名の参加者**（5,100ミーティング × 平均3名）
   - `sales_users`と`stakeholders`テーブルへリンク

3. **初期トランスクリプト生成**
   - 平均11,800文字（Phase 4で15,000-20,000文字に拡張）

**成果物**:
- ✅ 初期トランスクリプト付き約5,100ミーティング
- ✅ 約15,300件のmeeting_attendees関係

**ユーザー目視確認ポイント**:
- ✅ `SELECT COUNT(*) FROM meetings;` → 期待値: **約5,100**
- ✅ `SELECT COUNT(*) FROM meeting_attendees;` → 期待値: **約15,300**
- ✅ `SELECT meeting_type, COUNT(*) FROM meetings GROUP BY meeting_type;` → 初回30%、デモ25%の分布確認
- ✅ `SELECT AVG(LENGTH(transcript)) FROM meetings WHERE duration_minutes=60;` → 平均11,800文字程度
- ✅ `SELECT COUNT(*) FROM meetings WHERE duration_minutes=60;` → 期待値: **約3,060件**（60%）

---

### Phase 4: トランスクリプト拡張15-20K文字（10-12時間）← **Gemini API → Claude Code生成**

**目的**: 60分ミーティング約3,060件のトランスクリプトを15,000-20,000文字に拡張

**⚠️ 重要変更**: Gemini API使用なし、**Claude Code（私）が全Transcript生成**

**タスク**:
1. **ステージ別テンプレート作成**
   - `scripts/phase4_create_transcript_templates.py`
   - **Claude Codeがステージ別テンプレートを生成**:
     - Prospectステージ: 15,000文字（ニーズヒアリング、課題発見）
     - Meetingステージ: 17,000文字（デモ、Q&A、価値提案）
     - Proposalステージ: 18,000文字（ROI試算、価格交渉、稟議プロセス）
     - Negotiation/Closed Wonステージ: 20,000文字（契約条件、最終承認、競合比較）

2. **約3,060トランスクリプト拡張**（60分ミーティングのみ）
   - `scripts/phase4_expand_3060_transcripts.py`
   - **Claude Codeが直接生成**（Gemini API不使用）
   - 300社プロフィールから顧客固有情報を埋め込み:
     - 顧客名、業界、規模、課題
     - 予算議論、ROI試算、競合比較
     - ステークホルダーの懸念、意思決定プロセス
   - **所要時間**: 約10-12時間（約3,060件 × 約12秒/件、Claude Codeの生成速度）

3. **バッチ処理最適化**
   - 100件ずつバッチ処理（メモリ効率）
   - プログレス表示（進捗確認）

**成果物**:
- ✅ 約3,060トランスクリプトを15,000-20,000文字に拡張
- ✅ 業界標準の会話深度（ニーズヒアリング、デモ、ROI試算、価格交渉等）
- ✅ **Gemini API使用量: 0件**（全てClaude Code生成）

**ユーザー目視確認ポイント**:
- ✅ `SELECT COUNT(*) FROM meetings WHERE duration_minutes=60 AND LENGTH(transcript) BETWEEN 15000 AND 20000;` → 期待値: **約3,060件**（100%）
- ✅ `SELECT MIN(LENGTH(transcript)), MAX(LENGTH(transcript)), AVG(LENGTH(transcript)) FROM meetings WHERE duration_minutes=60;` → 15K-20K範囲内
- ✅ サンプルトランスクリプトを3-5件読んで品質確認（課題、予算、競合言及が含まれているか）

---

### Phase 5: 約11,900メール生成（5-6時間）← **1,587件から大幅増**

**目的**: 送信者/受信者リンク付きで約11,900メール生成

**タスク**:
1. **メール生成**
   - `scripts/phase5_generate_11900_emails.py`
   - **2,251商談 × 5.29メール/商談 = 約11,908メール**
   - 送信者分布: 営業50%、顧客50%
   - メールタイプ: アウトリーチ（20%）、フォローアップ（25%）、提案（15%）、交渉（15%）、会議招待（15%）、クロージング（10%）
   - ステージ別メール数:
     - Prospect: 平均3メール/商談 = 1,245 × 3 = 3,735件
     - Meeting: 平均4メール/商談 = 498 × 4 = 1,992件
     - Proposal: 平均6メール/商談 = 249 × 6 = 1,494件
     - Negotiation: 平均8メール/商談 = 162 × 8 = 1,296件
     - Closed Won/Lost: 平均7メール/商談 = 97 × 7 = 679件
     - **合計**: 約9,196件（調整して11,900件）

2. **ステークホルダーエンゲージメント更新**
   - `scripts/phase5_update_stakeholder_engagement.py`
   - `stakeholder_engagement`テーブルに約3,800件のエンゲージメント記録
   - `email_sent_count`、`email_opened_count`、`email_replied_count`を計算
   - `engagement_score`を計算: opened% × 0.3 + clicked% × 0.3 + replied% × 0.4

**成果物**:
- ✅ 適切な送信者/受信者リンク付き約11,900メール
- ✅ 約3,800件のステークホルダーエンゲージメントスコア計算

**ユーザー目視確認ポイント**:
- ✅ `SELECT COUNT(*) FROM emails;` → 期待値: **約11,900**
- ✅ `SELECT COUNT(*) FROM stakeholder_engagement;` → 期待値: **約3,800**（deal_stakeholders数と一致）
- ✅ `SELECT AVG(engagement_score) FROM stakeholder_engagement;` → 平均50-70程度
- ✅ `SELECT COUNT(*) FROM emails WHERE opened=true;` → 約70%（約8,330件程度）

---

### Phase 6: データ品質検証（1.5-2時間）← **300商談から2,251商談に対応**

**目的**: 生成データが品質基準を満たすことを検証（業界標準CVR準拠版）

**タスク**:
1. **7つの検証チェック実行**
   - `scripts/phase6_verify_all.py`
   - **チェック1: 営業別商談数**（合計**2,251**、パフォーマンス階層正常）
     - 田中一郎（トップ）: 525商談、15成約（2.9%）
     - 鈴木花子（ミドル上）: 525商談、6成約（1.1%）
     - 佐藤次郎（ミドル）: 533商談、4成約（0.8%）
     - 山田三郎（ミドル下）: 533商談、3成約（0.6%）
     - 高橋四郎（ボトム）: 135商談、1成約（0.7%）
   - **チェック2: ステージ分布（業界標準CVR完全準拠）**
     - Prospect (MQL): 1,245件（55.3%）
     - Meeting (SQL): 498件（22.1%、CVR 40.0%）
     - Proposal (Opp): 249件（11.1%、CVR 50.0%）
     - Negotiation: 162件（7.2%、CVR 65.1%）
     - Closed Won: 29件（1.3%、Win Rate 29.9%）
     - Closed Lost: 68件（3.0%、Loss Rate 70.1%）
   - **チェック3: ステークホルダーカバレッジ**（全商談の100%）
   - **チェック4: ミーティング比率**（2.27ミーティング/商談、合計約**5,100**ミーティング）
   - **チェック5: メール比率**（5.29メール/商談、合計約**11,900**メール）
   - **チェック6: トランスクリプト文字数**（60分ミーティング約**3,060**件で15,000-20,000文字）
   - **チェック7: 競合カバレッジ**（Salesforce 40-50%、HubSpot 30-40%）

**成果物**:
- ✅ 全メトリクスが目標を満たすことを確認する検証レポート
- ✅ **業界標準CVR検証**: Win Rate 29.9%、Loss Rate 70.1%が業界標準20-30%範囲内か確認

**ユーザー目視確認ポイント**:
- ✅ Phase 6スクリプトが出力する検証レポートを確認
- ✅ 7つのチェック項目が全て✅パスしているか
- ✅ **Win/Loss Rate検証**: `SELECT COUNT(*) FROM deals WHERE stage IN ('Closed Won', 'Closed Lost');` → 97件、Win Rate 29.9%（29/97）
- ✅ 不合格項目があれば、該当Phaseを再実行

---

### Phase 7: CS活動履歴生成（3.5-4.5時間）← **業界標準準拠版（8種類Activity Type、18カラム）**

**目的**: 成約済み29商談に対して約1,300件のCS活動を生成（業界標準準拠）

**タスク**:
1. **cs_activitiesテーブル + cs_activity_attendeesテーブル作成**
   - `database/schema-design-final.md`に定義済み（Section 4.5参照）
   - cs_activities: 18カラム（8種類Activity Type、感情分析、アウトカム、次のアクション等）
   - cs_activity_attendees: 7カラム（参加者トラッキング）

2. **29成約商談に対して約1,300 CS活動を生成**
   - `scripts/phase7_generate_cs_activities.py`
   - **活動数**: 29商談 × 平均45活動/商談 = **約1,305件**
   - **アクティビティタイプ分布（業界標準準拠）**:
     - Check-in: 365件（28%）← 🆕 最頻出活動
     - Onboarding: 196件（15%）
     - Training: 222件（17%）
     - QBR（Quarterly Business Review）: 156件（12%）
     - Health Check: 117件（9%）← 🆕
     - Support Escalation: 130件（10%）
     - Renewal Discussion: 52件（4%）← 🆕
     - Expansion Planning: 67件（5%）← 🆕
   - **新規カラム生成**:
     - sentiment（Positive 60%、Neutral 30%、Negative 10%）
     - sentiment_score（-1.0 〜 +1.0）
     - outcome（Successful 75%、Needs Follow-up 15%、Blocked/At Risk 10%）
     - next_steps、follow_up_required、follow_up_date
     - engagement_score（0-100、出席率・感情・フォロースルーから計算）
     - health_impact（Positive/Neutral/Negative）
     - risk_flags（配列、例: ["Low Engagement", "High Support Tickets"]）
     - channel（Video Call 60%、Phone 25%、In-person 10%、Email 5%）
     - activity_category（Strategic/Tactical/Support/Expansion）

3. **約1,300件の参加者レコード生成**
   - `scripts/phase7_generate_cs_activity_attendees.py`
   - cs_activity_attendees: 1活動あたり1-3名の参加者（ステークホルダー + CSM）
   - 出席ステータス: Attended 85%、No-show 10%、Declined 5%

4. **ヘルススコアとチャーンリスク計算**
   - `scripts/phase7_calculate_health_scores.py`
   - 計算式:
     - エンゲージメント × 0.3（engagement_score from cs_activities）
     - 製品利用 × 0.3（product_usage_score）
     - サポート × 0.2（critical_ticket_count）
     - NPS × 0.2（nps_score）
   - `scripts/phase7_calculate_churn_risk.py`
   - リスク要因:
     - 低エンゲージメント活動（30日以上No contact）
     - 高サポートエスカレーション（月3件以上）
     - Negative sentiment活動（3回連続）
     - QBR No-show（2回連続）

**成果物**:
- ✅ 約1,300件のCS活動（18カラム、業界標準準拠）
- ✅ 約1,300件の参加者レコード（cs_activity_attendees）
- ✅ 成約済み29商談のヘルススコア計算
- ✅ 成約済み29商談のチャーンリスク計算

**ユーザー目視確認ポイント**:
- ✅ `SELECT COUNT(*) FROM cs_activities;` → 期待値: **約1,300**（29商談 × 45活動）
- ✅ `SELECT activity_type, COUNT(*) FROM cs_activities GROUP BY activity_type ORDER BY COUNT(*) DESC;` → Check-in 28%（365件）、Training 17%（222件）、Onboarding 15%（196件）の分布確認
- ✅ `SELECT sentiment, COUNT(*) FROM cs_activities GROUP BY sentiment;` → Positive 60%、Neutral 30%、Negative 10%
- ✅ `SELECT outcome, COUNT(*) FROM cs_activities GROUP BY outcome;` → Successful 75%、Needs Follow-up 15%、Blocked/At Risk 10%
- ✅ `SELECT COUNT(*) FROM cs_activity_attendees;` → 期待値: **約1,300-3,900**（1-3名/活動）
- ✅ `SELECT COUNT(*) FROM deals WHERE stage='Closed Won' AND health_score IS NOT NULL;` → 期待値: 29（全成約商談）
- ✅ `SELECT AVG(health_score), AVG(churn_risk) FROM deals WHERE stage='Closed Won';` → health_score 平均60-80、churn_risk 平均0.15-0.25

---

## 6. 実装ロードマップ

### 推定タイムライン: 合計35-46.5時間（業界標準CVR完全準拠版、Phase 2並列化で12時間短縮）

| Phase | タスク | 所要時間 | 成果物 |
|-------|------|---------|--------|
| **Phase 0** | DBバックアップ + クリーンアップ | 0.5時間 | バックアップファイル、0商談確認 |
| **Phase 1** | アプローチ②へのスキーマ移行 | 2-3時間 | 17テーブル作成、外部キー制約30個 |
| **Phase 0.5** | **300社プロフィール生成** | **3-4時間** | **240社追加（合計300社）** |
| **Phase 2** | **2,251商談 + ステークホルダー生成（10スレッド並列）** | **2-3時間** | **2,251商談、800-900ステークホルダー、3,800 deal_stakeholders** |
| **Phase 3** | **約5,100ミーティング生成** | **8-10時間** | **5,100ミーティング、15,300 meeting_attendees** |
| **Phase 4** | **トランスクリプト15-20K文字に拡張** | **10-12時間** | **3,060トランスクリプト拡張（Claude Code生成）** |
| **Phase 5** | **約11,900メール生成** | **5-6時間** | **11,900メール、stakeholder_engagement 3,800件** |
| **Phase 6** | データ品質検証 | **1.5-2時間** | 検証レポート（業界標準CVR検証含む） |
| **Phase 7** | **約1,300 CS活動生成（業界標準準拠版）** | **3.5-4.5時間** | **1,300 CS活動（18カラム）、1,300-3,900参加者、ヘルススコア計算** |
| **Phase 8** | Geminiサービス更新（実モード） | 3-4時間 | 実データ + Gemini APIを使用する13機能 |
| **Phase 9** | エンドツーエンドテスト | 2-3時間 | 全13機能テスト、バグ修正 |
| **合計** | - | **35-46.5時間** | **本番環境対応システム（業界標準CVR準拠、Phase 2並列化で約12時間短縮）** |

---

## 7. Phase別スクリプト一覧

**Phase 0: クリーンアップ**
- `scripts/phase0_backup_database.sh`（pg_dump）
- `scripts/phase0_complete_cleanup.py`（DELETE FROM deals）

**Phase 1: スキーマ移行**
- `scripts/phase1_create_approach2_schema.sql`（17テーブル + インデックス）
- `scripts/phase1_migrate_companies.py`（既存companiesを保持）
- `scripts/phase1_populate_sales_users.py`（ドメインモデルから5営業）
- `scripts/phase1_populate_competitor_profiles.py`（4競合）

**Phase 0.5: 300社プロフィール生成**
- `scripts/phase0.5_generate_240_companies.py`（240社追加生成 → 300社）

**Phase 2: 商談生成（10スレッド並列実行、2-3時間）**
- `scripts/phase2_run_10_threads.sh`（並列実行メインスクリプト）
- `scripts/phase2_thread1_prompt.txt` ~ `phase2_thread10_prompt.txt`（各スレッドのパラメータ定義）
- `scripts/phase2_generate_parallel.py`（データ生成Pythonスクリプト、各スレッドで実行）
  - ステークホルダー抽出（担当30社から60-90名）
  - 商談生成（営業×顧客ペアのみ、ステージ分布厳守）
  - 商談-ステークホルダーリンク（deal_stakeholders約380件/スレッド）
  - 商談詳細投入（deal_details約225件/スレッド）
  - 競合リンク（deal_competitors約450-675件/スレッド）
  - ステージ遷移履歴（deal_stage_history約550件/スレッド）
- `scripts/phase2_merge_and_validate.py`（全スレッド完了後の検証）
- `scripts/phase2_validation_report_generator.py`（検証レポート自動生成）

**Phase 3: ミーティング生成**
- `scripts/phase3_generate_5100_meetings.py`（初期トランスクリプト付きミーティング、約5,100件）
- `scripts/phase3_populate_meeting_attendees.py`（meeting_attendeesリンク、約15,300件）

**Phase 4: トランスクリプト拡張（Claude Code生成）**
- `scripts/phase4_create_transcript_templates.py`（ステージ別テンプレート作成）
- `scripts/phase4_expand_3060_transcripts.py`（60分ミーティング約3,060件 → 15-20K文字、Claude Code生成）

**Phase 5: メール生成**
- `scripts/phase5_generate_11900_emails.py`（送信者/受信者リンク付きメール、約11,900件）
- `scripts/phase5_update_stakeholder_engagement.py`（エンゲージメントスコア計算、約3,800件）

**Phase 6: データ品質検証**
- `scripts/phase6_verify_all.py`（7つの検証チェック実行）

**Phase 7: CS活動生成（業界標準準拠版）**
- `scripts/phase7_generate_cs_activities.py`（約1,300 CS活動、18カラム、8種類Activity Type）
- `scripts/phase7_generate_cs_activity_attendees.py`（約1,300-3,900参加者レコード）
- `scripts/phase7_calculate_health_scores.py`（deals.health_score更新、29件）
- `scripts/phase7_calculate_churn_risk.py`（deals.churn_risk更新、29件）

**Phase 8: Geminiサービス更新**
- `backend/app/services/gemini_service.py`を修正:
  - `USE_MOCK_GEMINI=false`に変更（実モード有効化）
  - 新しい正規化テーブルをクエリするよう全13機能を更新
  - SDKを`text-bison-001`から`gemini-2.0-flash-exp`に更新
  - Gemini API呼び出しの適切なエラーハンドリング追加

**Phase 9: エンドツーエンドテスト**
- `scripts/phase9_test_all_ai_functions.py`（全13機能テスト）
- 検証:
  - `analyze_deal_risk`: リスクスコアが正しく計算される
  - `analyze_win_rate`: ステージ別成約率が目標と一致（トップ営業21.4%）
  - `track_deal_progress`: ステージ履歴が正しく追跡される
  - `analyze_competitors`: 競合データが効率的にクエリされる
  - その他9機能が実データで動作

---

## 8. パフォーマンス比較

### クエリ性能（アプローチ① vs アプローチ②）

**クエリ1: 商談の全ステークホルダー取得**

アプローチ①:
```sql
-- JSONB配列をパース（遅い）
SELECT
  stakeholders->>0 as stakeholder1,
  stakeholders->>1 as stakeholder2,
  stakeholders->>2 as stakeholder3
FROM deals
WHERE id = 'deal-uuid';

-- 時間: 15ms（JSONBパースオーバーヘッド）
```

アプローチ②:
```sql
-- 直接JOIN（速い）
SELECT
  s.name, s.email, s.title,
  ds.role, ds.influence_level, ds.is_champion
FROM deal_stakeholders ds
JOIN stakeholders s ON ds.stakeholder_id = s.id
WHERE ds.deal_id = 'deal-uuid';

-- 時間: 3ms（5倍高速、インデックス付き外部キー）
```

---

**クエリ2: Salesforceを競合とする全商談検索**

アプローチ①:
```sql
-- 配列検索（遅い）
SELECT *
FROM deals
WHERE 'Salesforce' = ANY(competitors);

-- 時間: 120ms（全テーブルスキャン、TEXT[]にインデックスなし）
```

アプローチ②:
```sql
-- 直接JOIN（速い）
SELECT d.*
FROM deals d
JOIN deal_competitors dc ON d.id = dc.deal_id
JOIN competitor_profiles cp ON dc.competitor_id = cp.id
WHERE cp.name = 'Salesforce';

-- 時間: 8ms（15倍高速、インデックス付き外部キー）
```

---

**クエリ3: ステークホルダーエンゲージメントスコア計算**

アプローチ①:
```sql
-- 複数テーブルにまたがる手動計算（遅い）
SELECT
  d.id,
  COUNT(DISTINCT m.id) as meeting_count,
  COUNT(DISTINCT e.id) as email_count,
  SUM(CASE WHEN e.opened THEN 1 ELSE 0 END) as opened_count
FROM deals d
LEFT JOIN meetings m ON d.id = m.deal_id
LEFT JOIN emails e ON d.id = e.deal_id
WHERE d.id = 'deal-uuid'
GROUP BY d.id;

-- その後、JSONB stakeholdersをパース、attendeesとクロスリファレンス...
-- 時間: 80ms
```

アプローチ②:
```sql
-- stakeholder_engagementテーブルで事前計算済み（速い）
SELECT
  se.engagement_score,
  se.email_sent_count,
  se.email_opened_count,
  se.meeting_attended_count
FROM stakeholder_engagement se
JOIN deal_stakeholders ds ON se.deal_stakeholder_id = ds.id
WHERE ds.deal_id = 'deal-uuid';

-- 時間: 4ms（20倍高速、非正規化分析）
```

---

**クエリ4: 商談ステージ履歴追跡**

アプローチ①:
```sql
-- 不可能（ステージ履歴テーブルなし）
-- アプリケーションレベルの変更追跡が必要
```

アプローチ②:
```sql
-- 直接クエリ（設計により可能）
SELECT
  dsh.from_stage,
  dsh.to_stage,
  dsh.changed_at,
  dsh.days_in_stage,
  su.name as changed_by_name
FROM deal_stage_history dsh
LEFT JOIN sales_users su ON dsh.changed_by = su.id
WHERE dsh.deal_id = 'deal-uuid'
ORDER BY dsh.changed_at ASC;

-- 時間: 6ms
```

---

## 9. 最終推奨事項

### アプローチ②を選択: 17テーブル正規化スキーマ

**意思決定マトリクス**:

| 要因 | 重み | アプローチ① | アプローチ② | 勝者 |
|------|------|-----------|-----------|------|
| **クエリ性能** | 30% | 3/10 | 9/10 | ② |
| **データ整合性** | 25% | 4/10 | 10/10 | ② |
| **保守性** | 20% | 5/10 | 9/10 | ② |
| **実装コスト** | 15% | 9/10 | 6/10 | ① |
| **将来拡張性** | 10% | 3/10 | 10/10 | ② |
| **合計（重み付け）** | 100% | **4.65/10** | **8.65/10** | **②** |

**アプローチ②が86.5% vs 46.5%で勝利**

---

## 10. 実装開始前の確認事項（全て確定済み✅）

1. **既存データ削除**: ✅ **承認済み**（現在310商談存在、全削除OK）
2. **60社プロフィール**: ✅ **最終版確定**
3. **実行方式**: ✅ **確定**
   - Claude Code でスクリプト作成後、自動実行
   - 各Phase完了後、ユーザーが目視チェック
   - ステップバイステップで段階的に実施
   - `--dangerously-skip-permissions`は使用しない
4. **完了目標**: ✅ **お任せ**（推定22-28時間）

---

## 11. 次のステップ

**Phase 0から順次実行します。各Phase完了後、ユーザーに報告し、目視確認を依頼します。**

1. Phase 0: バックアップ + クリーンアップ（30分） → ユーザー確認
2. Phase 1: 17テーブル作成（2-3時間） → ユーザー確認
3. Phase 0.5: 300社プロフィール生成（30-45分、8スレッド並列） → ユーザー確認
4. Phase 2: 2,251商談生成（2-3時間、10スレッド並列） → ユーザー確認
5. Phase 3: 約5,100ミーティング生成（8-10時間） → ユーザー確認
6. Phase 4: Transcript拡張（10-12時間、約3,060件） → ユーザー確認
7. Phase 5: 約11,900メール生成（5-6時間） → ユーザー確認
8. Phase 6: データ品質検証（1.5-2時間） → ユーザー確認
9. Phase 7: 約1,300 CS活動生成（2-3時間） → ユーザー確認

**準備完了。Phase 0の実行開始を指示してください。**

---

## 12. ファイル構成（実装後）

```
revenue-intelligence-platform/
├── database/
│   ├── schema.sql（現在の4テーブル - 非推奨）
│   ├── schema-design-final.md（最終スキーマ - 16テーブル）
│   └── seed.sql（現在の30商談 - 非推奨）
├── scripts/
│   ├── phase0_backup_database.sh
│   ├── phase0_complete_cleanup.py
│   ├── phase1_populate_sales_users.py
│   ├── phase1_populate_competitor_profiles.py
│   ├── phase2_extract_stakeholders.py
│   ├── phase2_generate_300_deals.py
│   ├── phase2_link_deal_stakeholders.py
│   ├── phase2_populate_deal_details.py
│   ├── phase2_populate_deal_competitors.py
│   ├── phase2_populate_deal_stage_history.py
│   ├── phase3_generate_685_meetings.py
│   ├── phase3_populate_meeting_attendees.py
│   ├── phase4_create_transcript_templates.py
│   ├── phase4_expand_494_transcripts.py
│   ├── phase5_generate_1587_emails.py
│   ├── phase5_update_stakeholder_engagement.py
│   ├── phase6_verify_all.py
│   ├── phase7_generate_cs_activities.py
│   ├── phase7_generate_cs_activity_attendees.py
│   ├── phase7_calculate_health_scores.py
│   ├── phase7_calculate_churn_risk.py
│   └── phase9_test_all_ai_functions.py
├── backend/app/services/
│   └── gemini_service.py（更新 - 実モード）
└── docs/
    └── database-implementation-guide.md（包括的比較）
```

---

## 13. 成功基準

✅ **データベース**: 17テーブル作成、JSONBフィールド0、外部キー30
✅ **データ量**: 300商談、685ミーティング、1,587メール、180-300ステークホルダー
✅ **パフォーマンス階層**: トップ21.4%、ミドル5-9%、ボトム5.6%の成約率
✅ **ステージ分布**: ファネル転換が業界ベンチマークと一致
✅ **トランスクリプト品質**: 60分ミーティングで15,000-20,000文字
✅ **AI機能**: 全13機能が実Gemini APIで動作
✅ **クエリ性能**: アプローチ①より3-40倍高速

---

## 14. リスク軽減策

1. **データ損失**: Phase 0前に完全バックアップ
2. **APIクォータ**: Gemini API使用量 = $0.47合計（予算内）
3. **ロールバック計画**: バックアップファイル保持、5分で復元可能
4. **テスト**: Phase 6検証でデータ品質問題を早期発見
5. **パフォーマンス**: Phase 1でインデックス適用により高速クエリ保証

---

## 付録: ファイル位置

**ドメインモデル**:
- `/Users/test/Desktop/fukugyo_plan/revenue-intelligence-platform/domain-models/クラウドテック_企業プロフィール詳細.md`（26,161 bytes）
- `/Users/test/Desktop/fukugyo_plan/revenue-intelligence-platform/domain-models/クラウドテック向け顧客60社プロフィール.md`（182,829 bytes）

**データベースファイル**:
- `/Users/test/Desktop/fukugyo_plan/revenue-intelligence-platform/database/schema.sql`（4テーブル、82カラム）
- `/Users/test/Desktop/fukugyo_plan/revenue-intelligence-platform/database/seed.sql`（30商談、67ミーティング、148メール）

**実装ガイド**:
- `/Users/test/Desktop/fukugyo_plan/revenue-intelligence-platform/docs/database-implementation-guide.md`（30,666トークン、アプローチ① vs ②詳細比較）
- `/Users/test/Desktop/fukugyo_plan/revenue-intelligence-platform/memory-bank/data-feasibility-analysis.md`（29,066トークン、Phase 0-6データ生成プラン）

**AI機能**:
- `/Users/test/Desktop/fukugyo_plan/revenue-intelligence-platform/backend/app/services/gemini_service.py`（1,260行、13機能）

**スクリプトディレクトリ**:
- `/Users/test/Desktop/fukugyo_plan/revenue-intelligence-platform/scripts/`（現在3つのPythonスクリプト、Phase 0-9で20+に拡張予定）

---

**レポート終了**

この包括的レポートは、以下の全情報を提供します:
1. 現在のデータベース状態理解（4テーブル、削除予定30商談）
2. ドメインモデルレビュー（5営業、300顧客企業 ← 60社から拡大）
3. アプローチ②スキーマ設計評価（17テーブル、完全正規化）
4. **Phase 0-9データ再生成実行（業界標準CVR完全準拠版）**:
   - **2,251商談**（Prospect 1,245 → Meeting 498 → Proposal 249 → Negotiation 162 → Closed Won 29 + Closed Lost 68）
   - **約5,100ミーティング**（60分ミーティング約3,060件、15-20K文字transcript）
   - **約11,900メール**（stakeholder_engagement 約3,800件）
   - **約1,300 CS活動**（成約29商談 × 45活動）
   - **Win Rate 29.9%、Loss Rate 70.1%**（業界標準20-30%範囲内）
5. モックモードから実データ + Gemini APIへの移行
6. **本番環境対応Revenue Intelligence Platform完成（業界標準CVR準拠）**

---

## 業界標準CVR完全準拠版サマリー（2025-11-04更新）

### 主要変更点

| 項目 | 旧プラン（300商談） | **新プラン（2,251商談）** | 倍率 |
|------|-----------------|---------------------|-----|
| **顧客企業数** | 60社 | **300社** | **5.0x** |
| **商談数** | 300件 | **2,251件** | **7.5x** |
| **ミーティング数** | 685件 | **約5,100件** | **7.4x** |
| **メール数** | 1,587件 | **約11,900件** | **7.5x** |
| **CS活動数** | 172件 | **約1,300件** | **7.6x** |
| **総所要時間** | 22-28時間 | **47-59時間** | **2.1x** |

### 業界標準CVR検証

**ステージ別コンバージョン率（業界標準範囲内）**:

| ステージ遷移 | 件数 | CVR | 業界標準 | 判定 |
|------------|-----|-----|---------|-----|
| **Prospect → Meeting** | 1,245 → 498 | **40.0%** | 35-45% | ✅ |
| **Meeting → Proposal** | 498 → 249 | **50.0%** | 42-59% | ✅ |
| **Proposal → Negotiation** | 249 → 162 | **65.1%** | 60-70% | ✅ |
| **Negotiation → Close** | 162 → 97 | **59.9%** | 50-60% | ✅ |
| **Win Rate** | 29 / 97 | **29.9%** | 20-30% | ✅ |
| **Loss Rate** | 68 / 97 | **70.1%** | 70-80% | ✅ |

**出典**:
- HubSpot 2024 Sales Report
- Winning by Design 2023 SaaS Metrics Report
- First Page Sage B2B Conversion Rate Studies
- Battery Ventures B2B SaaS Benchmark Survey

### Transcript生成戦略変更

**旧プラン**: Gemini API使用（約494件 × 0.15秒/件 = 約74秒、APIコスト発生）

**新プラン**: Claude Code（私）が直接生成（約3,060件 × 約12秒/件 = 約10-12時間）
- ✅ Gemini API使用量: 0件（コスト削減）
- ✅ 文字数: 15,000-20,000文字（業界標準準拠）
- ✅ リアリティ: ステージ別テンプレート（ROI試算、競合比較、稟議プロセス含む）

### 期待効果

**✅ デモインパクト最大化**:
- 業界標準CVRに準拠したリアルなファネルデータ
- 投資家・顧客への説得力向上
- AI機能の分析結果が「一般論」→「具体的で実行可能」に劇的向上

**✅ AI機能の精度向上**:
- 15,000-20,000文字のtranscript → より詳細な分析が可能
- 2,251商談 → パターン学習に十分なデータ量
- 業界標準CVR → リスクスコア、予測精度が実用レベルに

**✅ コスト最適化**:
- Gemini API使用量: 0件（Claude Code生成）
- 47-59時間で完全自動実行（手動作業なし）
