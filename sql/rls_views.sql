-- =============================================
-- ROW-LEVEL SECURITY VIEWS
-- =============================================

-- 1. Regulator View (Full Access)
CREATE VIEW v_loans_regulator AS
SELECT
    l.loan_hash,
    l.loan_id,
    s.principal_amount,
    s.outstanding_amount,
    s.interest_rate,
    s.currency,
    s.origination_date,
    s.maturity_date,
    s.ltv_ratio,
    s.pd_rating,
    s.lgd,
    s.ead,
    s.risk_weight,
    s.npl_status,
    s.sector,
    s.cost_center
FROM hub_loan l
JOIN sat_loan_details s ON l.loan_hash = s.loan_hash
WHERE s.load_datetime = (SELECT MAX(load_datetime) FROM sat_loan_details WHERE loan_hash = l.loan_hash);

-- 2. Controlling View (Cost-Center Restricted)
CREATE VIEW v_loans_controlling AS
SELECT * FROM v_loans_regulator
WHERE cost_center IN ('CC_1001', 'CC_1002', 'CC_1003');  -- Configurable per user

-- 3. Risk Department View (Loans Only)
CREATE VIEW v_loans_risk AS
SELECT 
    loan_id,
    pd_rating,
    lgd,
    ead,
    risk_weight,
    npl_status,
    sector
FROM v_loans_regulator;

-- 4. GL Access Control
CREATE VIEW v_gl_controlling AS
SELECT * FROM hub_gl_entries
WHERE cost_center IN (SELECT cost_center FROM user_cost_center_mapping WHERE username = CURRENT_USER);

-- Helper table for RLS (populated by identity provider)
CREATE TABLE user_cost_center_mapping (
    username VARCHAR(50),
    cost_center VARCHAR(20),
    PRIMARY KEY (username, cost_center)
);
