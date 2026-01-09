-- ============================================================================
-- Revenue Intelligence Platform - Approach② Schema (15 Tables)
-- ============================================================================
-- Generated: 2025-11-04
-- Purpose: Complete normalization (3NF), 14 new tables + companies (existing)
-- Tables: 15 total (companies preserved from Phase 0)
-- Foreign Keys: 28
-- Indexes: None (deferred for performance optimization later)
-- ============================================================================

-- ============================================================================
-- Core Tables (4 new tables)
-- ============================================================================

-- Table 1: sales_users (10 columns) - NEW
DROP TABLE IF EXISTS sales_users CASCADE;

CREATE TABLE sales_users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT UNIQUE NOT NULL,              -- e.g., "user1"
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

-- Table 2: stakeholders (10 columns) - NEW
DROP TABLE IF EXISTS stakeholders CASCADE;

CREATE TABLE stakeholders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  email TEXT,
  title TEXT,
  company_name TEXT,                         -- Customer company name
  department TEXT,
  phone TEXT,
  linkedin_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(email, company_name)                -- No duplicate person in same company
);

-- Table 3: deals (32 columns) - REDESIGNED (slimmed from 47)
-- Note: Drops existing deals table from Phase 0
DROP TABLE IF EXISTS deals CASCADE;

CREATE TABLE deals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

  -- Basic info
  deal_name TEXT,
  customer_name TEXT NOT NULL,
  customer_industry TEXT,
  customer_size INTEGER,

  -- Stage tracking
  stage TEXT NOT NULL CHECK (stage IN ('Prospect', 'Meeting', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost')),
  stage_changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  days_in_current_stage INTEGER DEFAULT 0,

  -- Financial
  amount DECIMAL NOT NULL,
  mrr DECIMAL,
  contract_term INTEGER,                     -- months

  -- Owner
  owner_id UUID NOT NULL REFERENCES sales_users(id),

  -- Dates
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  expected_close_date DATE,
  closed_at TIMESTAMP WITH TIME ZONE,

  -- Contact tracking
  last_contact_date DATE,
  last_meaningful_activity_date TIMESTAMP WITH TIME ZONE,

  -- Next action
  next_action TEXT,
  next_action_date DATE,

  -- Deal evaluation
  probability DECIMAL CHECK (probability >= 0 AND probability <= 1),
  budget DECIMAL,
  budget_confirmed BOOLEAN DEFAULT false,
  budget_status TEXT,                        -- Confirmed/Estimated/Unknown
  timeline TEXT,
  decision_timeline TEXT,

  -- Metrics (calculated)
  sales_cycle_days INTEGER,
  risk_score DECIMAL CHECK (risk_score >= 0 AND risk_score <= 100),
  urgency_level TEXT CHECK (urgency_level IN ('low', 'medium', 'high', 'critical')),
  stalled_days INTEGER DEFAULT 0,

  -- Close tracking
  close_reason TEXT,                         -- For Closed Won/Lost
  lost_to_competitor UUID REFERENCES competitor_profiles(id),

  -- Size category
  deal_size_category TEXT CHECK (deal_size_category IN ('Small', 'Medium', 'Large', 'Enterprise')),
  lead_source TEXT
);

-- Table 4: competitor_profiles (10 columns) - NEW
DROP TABLE IF EXISTS competitor_profiles CASCADE;

CREATE TABLE competitor_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT UNIQUE NOT NULL,                 -- Salesforce, HubSpot, etc.
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

-- ============================================================================
-- Relationship Tables (5 new tables)
-- ============================================================================

-- Table 5: deal_stakeholders (18 columns) - NEW
DROP TABLE IF EXISTS deal_stakeholders CASCADE;

CREATE TABLE deal_stakeholders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
  stakeholder_id UUID NOT NULL REFERENCES stakeholders(id) ON DELETE CASCADE,

  -- Role
  role TEXT NOT NULL,                        -- Decision maker/Evaluator/User/Other
  influence_level INTEGER CHECK (influence_level >= 0 AND influence_level <= 100),
  support_level TEXT CHECK (support_level IN ('Champion', 'Supporter', 'Neutral', 'Detractor')),

  -- Authority
  decision_authority BOOLEAN DEFAULT false,
  budget_authority BOOLEAN DEFAULT false,

  -- Champion metrics
  is_champion BOOLEAN DEFAULT false,
  champion_score DECIMAL,                    -- 0-100, behavior-based
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

-- Table 6: stakeholder_engagement (12 columns) - NEW
DROP TABLE IF EXISTS stakeholder_engagement CASCADE;

CREATE TABLE stakeholder_engagement (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_stakeholder_id UUID NOT NULL REFERENCES deal_stakeholders(id) ON DELETE CASCADE,

  -- Email metrics
  email_sent_count INTEGER DEFAULT 0,
  email_opened_count INTEGER DEFAULT 0,
  email_clicked_count INTEGER DEFAULT 0,
  email_replied_count INTEGER DEFAULT 0,

  -- Meeting metrics
  meeting_invited_count INTEGER DEFAULT 0,
  meeting_attended_count INTEGER DEFAULT 0,

  -- Calculated score
  engagement_score DECIMAL CHECK (engagement_score >= 0 AND engagement_score <= 100),

  -- Last activity timestamps
  last_email_opened_at TIMESTAMP WITH TIME ZONE,
  last_email_replied_at TIMESTAMP WITH TIME ZONE,
  last_meeting_attended_at TIMESTAMP WITH TIME ZONE,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(deal_stakeholder_id)
);

-- Table 7: deal_competitors (9 columns) - NEW
DROP TABLE IF EXISTS deal_competitors CASCADE;

CREATE TABLE deal_competitors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
  competitor_id UUID NOT NULL REFERENCES competitor_profiles(id),

  -- Status
  status TEXT CHECK (status IN ('Active', 'Dismissed', 'Won Against', 'Lost To')),
  threat_level TEXT CHECK (threat_level IN ('Low', 'Medium', 'High')),

  -- Price comparison
  competitor_price DECIMAL,
  our_price DECIMAL,

  -- Notes
  notes TEXT,
  our_differentiation TEXT[],

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(deal_id, competitor_id)
);

-- Table 8: deal_details (8 columns) - NEW
DROP TABLE IF EXISTS deal_details CASCADE;

CREATE TABLE deal_details (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,

  -- Requirements
  pain_points TEXT[],
  requirements TEXT[],
  decision_criteria TEXT[],

  -- Win/loss factors
  win_factors TEXT[],
  loss_factors TEXT[],
  risk_factors TEXT[],
  strengths TEXT[],

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(deal_id)
);

-- Table 9: deal_stage_history (7 columns) - NEW
DROP TABLE IF EXISTS deal_stage_history CASCADE;

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

-- ============================================================================
-- Activity Tables (3 new tables)
-- ============================================================================

-- Table 10: meetings (11 columns) - REDESIGNED
-- Note: Drops existing meetings table from Phase 0
DROP TABLE IF EXISTS meetings CASCADE;

CREATE TABLE meetings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,

  -- Basic info
  date TIMESTAMP WITH TIME ZONE NOT NULL,
  duration_minutes INTEGER,
  meeting_type TEXT NOT NULL,
  location TEXT,

  -- Content
  transcript TEXT,
  summary TEXT,

  -- Owner
  created_by UUID REFERENCES sales_users(id),
  meeting_owner_id UUID REFERENCES sales_users(id),

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table 11: meeting_attendees (6 columns) - NEW
DROP TABLE IF EXISTS meeting_attendees CASCADE;

CREATE TABLE meeting_attendees (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  meeting_id UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
  stakeholder_id UUID REFERENCES stakeholders(id) ON DELETE SET NULL,
  sales_user_id UUID REFERENCES sales_users(id) ON DELETE SET NULL,

  -- Either stakeholder_id or sales_user_id must be set
  attendance_status TEXT CHECK (attendance_status IN ('Attended', 'No-show', 'Cancelled')),

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  CHECK (stakeholder_id IS NOT NULL OR sales_user_id IS NOT NULL)
);

-- Table 12: emails (17 columns) - REDESIGNED
-- Note: Drops existing emails table from Phase 0
DROP TABLE IF EXISTS emails CASCADE;

CREATE TABLE emails (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,

  -- Sender/recipient (links to stakeholders/sales_users)
  sender_sales_user_id UUID REFERENCES sales_users(id),
  sender_stakeholder_id UUID REFERENCES stakeholders(id),
  recipient_sales_user_id UUID REFERENCES sales_users(id),
  recipient_stakeholder_id UUID REFERENCES stakeholders(id),

  -- Content
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  sent_at TIMESTAMP WITH TIME ZONE NOT NULL,

  -- Engagement
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

-- ============================================================================
-- Analytics Tables (2 new tables)
-- ============================================================================

-- Table 13: revenue_forecasts (9 columns) - NEW
DROP TABLE IF EXISTS revenue_forecasts CASCADE;

CREATE TABLE revenue_forecasts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  forecast_date DATE NOT NULL,
  forecast_period TEXT NOT NULL,             -- "2025-Q1", "2025-11", etc.
  forecast_amount DECIMAL NOT NULL,
  confidence_level DECIMAL CHECK (confidence_level >= 0 AND confidence_level <= 1),

  -- Accuracy tracking (after period ends)
  actual_amount DECIMAL,
  accuracy DECIMAL,                          -- abs(actual - forecast) / actual

  created_by UUID REFERENCES sales_users(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table 14: forecast_deals (5 columns) - NEW
DROP TABLE IF EXISTS forecast_deals CASCADE;

CREATE TABLE forecast_deals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  forecast_id UUID NOT NULL REFERENCES revenue_forecasts(id) ON DELETE CASCADE,
  deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
  weighted_value DECIMAL,                    -- amount * probability
  included_in_forecast BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(forecast_id, deal_id)
);

-- Table 15: cs_activities (21 columns) - NEW
DROP TABLE IF EXISTS cs_activities CASCADE;

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

-- Table 16: cs_activity_attendees (7 columns) - NEW
DROP TABLE IF EXISTS cs_activity_attendees CASCADE;

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

-- ============================================================================
-- Schema Statistics
-- ============================================================================
-- Total Tables: 16 (companies existing + 15 new)
-- Total Columns: ~210 (distributed across 16 tables)
-- Foreign Keys: 30
-- Indexes: 0 (deferred for later)
-- Normalization: 3NF (Third Normal Form)
-- ============================================================================

-- ============================================================================
-- Verification Queries
-- ============================================================================
-- SELECT COUNT(*) FROM pg_tables WHERE schemaname='public';
-- Expected: 16 tables
--
-- SELECT COUNT(*) FROM information_schema.table_constraints
-- WHERE constraint_type='FOREIGN KEY' AND table_schema='public';
-- Expected: 30 foreign keys
-- ============================================================================
