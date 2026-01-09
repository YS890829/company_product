# Database Schema Documentation

## ⚠️ IMPORTANT: Schema Files

| ファイル | 用途 | ステータス |
|---------|------|-----------|
| `schema-design-final.md` | ✅ **完全なスキーマ定義**（16テーブル、30外部キー） | CURRENT |
| `database-complete-implementation-plan.md` | ✅ Phase 0-7実装プラン | CURRENT |

## 📊 テーブル構造（16テーブル）

### アーキテクチャ概要

- **Total Tables**: 16（companies既存 + 15新規）
- **Foreign Keys**: 30
- **Normalization**: 3NF（Third Normal Form）
- **Phase 0-7**: 別ブランチ `feature/data-generation-phase0-7` で完全実装完了

---

### Core Tables（4テーブル）

#### 1. companies（既存保持、13カラム）
```sql
companies (
  id, name, industry, arr, annual_contracts,
  founded, employees, sales_team_size,
  crm_system, main_product, target_market, service_area,
  created_at, updated_at
)
```

#### 2. sales_users（10カラム）
```sql
sales_users (
  id, user_id, name, email, company_id,
  role, team, hire_date, is_active,
  created_at, updated_at
)
```
**用途**: 営業担当者マスタ（5名投入済み）

#### 3. stakeholders（10カラム）
```sql
stakeholders (
  id, name, email, title, company_name,
  department, phone, linkedin_url,
  created_at, updated_at
)
```
**用途**: 顧客側のキーパーソン（800-900名）

#### 4. deals（32カラム）
```sql
deals (
  id, company_id, deal_name, customer_name, customer_industry, customer_size,
  stage, stage_changed_at, days_in_current_stage,
  amount, mrr, contract_term, owner_id,
  created_at, updated_at, expected_close_date, closed_at,
  last_contact_date, last_meaningful_activity_date,
  next_action, next_action_date,
  probability, budget, budget_confirmed, budget_status, timeline, decision_timeline,
  sales_cycle_days, risk_score, urgency_level, stalled_days,
  close_reason, lost_to_competitor, deal_size_category, lead_source
)
```
**用途**: 商談マスタ（2,251件生成済み）

#### 5. competitor_profiles（10カラム）
```sql
competitor_profiles (
  id, name, website, description, typical_pricing_range,
  strengths, weaknesses, battle_card_url, overall_win_rate,
  created_at, updated_at
)
```
**用途**: 競合マスタ（Salesforce、HubSpot、kintone、Zoho CRM）

---

### Relationship Tables（5テーブル）

#### 6. deal_stakeholders（18カラム）
```sql
deal_stakeholders (
  id, deal_id, stakeholder_id,
  role, influence_level, support_level,
  decision_authority, budget_authority,
  is_champion, champion_score, reports_to_stakeholder_id,
  introduced_stakeholders_count, shared_internal_info,
  proactive_contact_count, positive_sentiment_count,
  last_contact_date, created_at, updated_at
)
```
**用途**: 商談-ステークホルダーリンク（約3,800件）

#### 7. stakeholder_engagement（12カラム）
```sql
stakeholder_engagement (
  id, deal_stakeholder_id,
  email_sent_count, email_opened_count, email_clicked_count, email_replied_count,
  meeting_invited_count, meeting_attended_count,
  engagement_score,
  last_email_opened_at, last_email_replied_at, last_meeting_attended_at,
  created_at, updated_at
)
```
**用途**: ステークホルダー別エンゲージメント追跡

#### 8. deal_competitors（9カラム）
```sql
deal_competitors (
  id, deal_id, competitor_id,
  status, threat_level,
  competitor_price, our_price,
  notes, our_differentiation,
  created_at, updated_at
)
```
**用途**: 商談-競合リンク

#### 9. deal_details（8カラム）
```sql
deal_details (
  id, deal_id,
  pain_points, requirements, decision_criteria,
  win_factors, loss_factors, risk_factors, strengths,
  created_at, updated_at
)
```
**用途**: 商談詳細情報（配列型カラム活用）

#### 10. deal_stage_history（7カラム）
```sql
deal_stage_history (
  id, deal_id, from_stage, to_stage,
  changed_at, changed_by, days_in_stage,
  created_at
)
```
**用途**: ステージ履歴追跡（Deal Velocity分析用）

---

### Activity Tables（3テーブル）

#### 11. meetings（11カラム）
```sql
meetings (
  id, deal_id,
  date, duration_minutes, meeting_type, location,
  transcript, summary,
  created_by, meeting_owner_id,
  created_at
)
```
**用途**: ミーティング記録（大量生成完了）

#### 12. meeting_attendees（6カラム）
```sql
meeting_attendees (
  id, meeting_id, stakeholder_id, sales_user_id,
  attendance_status,
  created_at
)
```
**用途**: ミーティング参加者リンク

#### 13. emails（17カラム）
```sql
emails (
  id, deal_id,
  sender_sales_user_id, sender_stakeholder_id,
  recipient_sales_user_id, recipient_stakeholder_id,
  subject, body, sent_at,
  opened, opened_at, is_replied, reply_time_minutes,
  clicked_links, engagement_score, attachments,
  created_at
)
```
**用途**: メール記録（大量生成完了）

---

### Analytics Tables（2テーブル）

#### 14. revenue_forecasts（9カラム）
```sql
revenue_forecasts (
  id, forecast_date, forecast_period, forecast_amount, confidence_level,
  actual_amount, accuracy,
  created_by, created_at
)
```
**用途**: 売上予測管理

#### 15. forecast_deals（5カラム）
```sql
forecast_deals (
  id, forecast_id, deal_id,
  weighted_value, included_in_forecast,
  created_at
)
```
**用途**: 予測-商談リンク

---

### CS Tables（2テーブル）

#### 16. cs_activities（21カラム）
```sql
cs_activities (
  id, deal_id,
  activity_type, activity_category,
  subject, description,
  activity_date, duration_minutes,
  owner_id,
  outcome, sentiment, sentiment_score,
  next_steps, follow_up_required, follow_up_date,
  engagement_score, health_impact, risk_flags,
  channel,
  created_at, updated_at
)
```
**用途**: CS活動記録（Phase 7で生成完了）

#### 17. cs_activity_attendees（7カラム）
```sql
cs_activity_attendees (
  id, activity_id, stakeholder_id, sales_user_id,
  attendance_status,
  created_at, updated_at
)
```
**用途**: CS活動参加者リンク

## 🔧 使用方法

### スキーマの適用（別ブランチで実装完了）

**重要**: スキーマは別ブランチ `feature/data-generation-phase0-7` で完全実装済みです。

```bash
# 実装済みブランチへの切り替え
git worktree add /path/to/worktree feature/data-generation-phase0-7

# または直接ブランチをチェックアウト
git checkout feature/data-generation-phase0-7
```

### スキーマの確認

```sql
-- テーブル一覧
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
-- 結果: 16テーブル

-- 外部キー数確認
SELECT COUNT(*) FROM information_schema.table_constraints
WHERE constraint_type='FOREIGN KEY' AND table_schema='public';
-- 結果: 30

-- 各テーブルのカラム数確認
SELECT table_name, COUNT(*) as column_count
FROM information_schema.columns
WHERE table_schema = 'public'
GROUP BY table_name
ORDER BY table_name;
```

---

## 📋 スキーマバージョン履歴

### v2.0.0 (2025-11-04) - Current（別ブランチ実装完了）
- **変更内容**: 完全正規化（4テーブル → 16テーブル）
  - **Core Tables (4)**: sales_users, stakeholders, deals, competitor_profiles
  - **Relationship Tables (5)**: deal_stakeholders, stakeholder_engagement, deal_competitors, deal_details, deal_stage_history
  - **Activity Tables (3)**: meetings, meeting_attendees, emails
  - **Analytics Tables (2)**: revenue_forecasts, forecast_deals
  - **CS Tables (2)**: cs_activities, cs_activity_attendees
- **正規化**: 3NF（Third Normal Form）
- **外部キー**: 30個
- **データ件数**:
  - 300社プロフィール
  - 2,251商談
  - 800-900 stakeholders
  - 大量ミーティング・メール・CS活動
- **実装ブランチ**: `feature/data-generation-phase0-7`
- **実装プラン**: [database-complete-implementation-plan.md](database-complete-implementation-plan.md)
- **スキーマ定義**: [schema-design-final.md](schema-design-final.md)

### v1.2.0 (2025-11-04) - Deprecated
- **初期スキーマ**: 4テーブル（companies, deals, meetings, emails）
- **deals**: 48カラム（CS関連25カラム含む）
- **ステータス**: v2.0.0に移行（16テーブル正規化版）

---

## 🎯 Claude Code向けガイド

### スキーマ参照時の注意点

✅ **正しい手順**:
1. `database/schema-design-final.md`を読み込む（**最優先**）
2. スキーマは**16テーブル**と認識する
3. 外部キー30個で完全正規化されている
4. Phase 0-7は別ブランチ `feature/data-generation-phase0-7` で実装完了

❌ **避けるべき手順**:
- ~~古い4テーブル構成（v1.2.0以前）を参照する~~
- ~~`deals`テーブルが48カラムと仮定する~~（v2.0.0では32カラム）
- ~~mainブランチのスキーマを参照する~~（別ブランチで実装）

---

## 🔍 データ統計（Phase 0-7完了後、別ブランチ）

### テーブル別レコード数
| テーブル | レコード数 | 備考 |
|---------|-----------|------|
| companies | 300社 | Phase 0.5で生成 |
| sales_users | 5名 | Phase 1で投入 |
| competitor_profiles | 4社 | Salesforce、HubSpot、kintone、Zoho CRM |
| stakeholders | 800-900名 | Phase 2で生成 |
| deals | 2,251件 | 業界標準CVR準拠 |
| deal_stakeholders | ~3,800件 | Phase 2で生成 |
| stakeholder_engagement | ~3,800件 | Phase 2で生成 |
| deal_competitors | 大量生成 | Phase 2で生成 |
| deal_details | 2,251件 | Phase 2で生成 |
| deal_stage_history | 大量生成 | Phase 2で生成 |
| meetings | 大量生成 | Phase 3で生成 |
| meeting_attendees | 大量生成 | Phase 3で生成 |
| emails | 大量生成 | Phase 5で生成 |
| revenue_forecasts | 生成済み | Phase 2-7で生成 |
| forecast_deals | 生成済み | Phase 2-7で生成 |
| cs_activities | 生成済み | Phase 7で生成 |
| cs_activity_attendees | 生成済み | Phase 7で生成 |

### データ品質メトリクス
- **業界標準CVR準拠**: Prospect > Meeting > Proposal > Closed Won
- **Stakeholders設定率**: 100%（全商談にステークホルダー設定）
- **競合設定率**: 100%（全商談に競合設定）
- **正規化レベル**: 3NF（Third Normal Form）
- **外部キー整合性**: 30個すべて正常

---

## 📖 参考資料

- **スキーマ定義（v2.0.0）**: [schema-design-final.md](schema-design-final.md)
- **実装プラン（Phase 0-7）**: [database-complete-implementation-plan.md](database-complete-implementation-plan.md)
- **プロジェクト全体**: [../README.md](../README.md)
- **別ブランチ実装状況**: [../memory-bank/activeContext.md](../memory-bank/activeContext.md)

---

**最終更新**: 2025年11月6日
**現在のバージョン**: v2.0.0（16テーブル、3NF正規化）
**実装ステータス**: Phase 0-7完了（別ブランチ `feature/data-generation-phase0-7`）
