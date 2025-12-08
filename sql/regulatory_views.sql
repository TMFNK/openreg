-- =============================================
-- REGULATORY REPORTING LAYER
-- Simplified FINREP / COREP / Basel III
-- =============================================

-- FINREP F18: Credit Quality of Loans
CREATE VIEW finrep_f18_credit_quality AS
SELECT
    sector,
    CASE 
        WHEN npl_status = 1 THEN 'NON_PERFORMING'
        WHEN pd_rating < 0.02 THEN 'LOW_RISK'
        WHEN pd_rating < 0.05 THEN 'MEDIUM_RISK'
        ELSE 'HIGH_RISK'
    END AS credit_quality_bucket,
    COUNT(*) AS num_loans,
    SUM(outstanding_amount) AS exposure_amount,
    AVG(ltv_ratio) AS avg_ltv,
    SUM(ead * risk_weight) AS rwa  -- Risk-Weighted Assets
FROM v_loans_regulator
GROUP BY sector, credit_quality_bucket;

-- COREP CR SA: Standardized Approach Exposure
CREATE VIEW corep_cr_sa_exposure AS
SELECT
    l.sector,
    l.risk_weight,
    SUM(l.ead) AS ead_pre_crm,
    SUM(l.ead * (1 - COALESCE(c.haircut, 0))) AS ead_post_crm,
    SUM(l.ead * l.risk_weight) AS rwa
FROM v_loans_regulator l
LEFT JOIN sat_collateral c ON l.loan_hash = c.loan_hash
    AND c.load_datetime = (SELECT MAX(load_datetime) FROM sat_collateral WHERE loan_hash = l.loan_hash)
GROUP BY sector, risk_weight;

-- Liquidity Coverage Ratio (LCR) - Simplified
CREATE VIEW lcr_liquidity_metrics AS
SELECT
    'HIGH_QUALITY_LIQUID_ASSETS' AS category,
    SUM(amount) AS value
FROM hub_gl_entries
WHERE account IN ('1000_CASH', '1100_HQLA')
UNION ALL
SELECT
    'NET_CASH_OUTFLOWS' AS category,
    SUM(amount * 0.1) AS value  -- 10% runoff rate
FROM hub_gl_entries
WHERE account LIKE '2%';

-- NPL Ratio (Key Regulatory KPI)
CREATE VIEW kpi_npl_ratio AS
SELECT
    COUNT(CASE WHEN npl_status = 1 THEN 1 END) * 1.0 / COUNT(*) AS npl_ratio,
    SUM(CASE WHEN npl_status = 1 THEN outstanding_amount ELSE 0 END) / 
        SUM(outstanding_amount) AS npl_exposure_ratio
FROM v_loans_regulator;
