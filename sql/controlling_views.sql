-- =============================================
-- CONTROLLING KPI LAYER
-- =============================================

-- Cost Center Profitability
CREATE VIEW controlling_cost_center_profit AS
SELECT
    cost_center,
    COUNT(DISTINCT loan_id) AS active_loans,
    SUM(principal_amount) AS loan_volume,
    SUM(outstanding_amount * interest_rate) AS interest_income,
    SUM(outstanding_amount * pd_rating * lgd) AS expected_loss,
    SUM(outstanding_amount * interest_rate - outstanding_amount * pd_rating * lgd) AS net_contribution_margin
FROM v_loans_controlling
GROUP BY cost_center
ORDER BY net_contribution_margin DESC;

-- Month-over-Month Loan Growth
CREATE VIEW controlling_mom_growth AS
SELECT
    strftime('%Y-%m', origination_date) AS month,
    COUNT(*) AS new_loans,
    SUM(principal_amount) AS new_volume,
    LAG(COUNT(*)) OVER (ORDER BY strftime('%Y-%m', origination_date)) AS prev_month_loans,
    LAG(SUM(principal_amount)) OVER (ORDER BY strftime('%Y-%m', origination_date)) AS prev_month_volume,
    (COUNT(*) * 1.0 / LAG(COUNT(*)) OVER (ORDER BY strftime('%Y-%m', origination_date))) - 1 AS loan_growth_rate
FROM v_loans_controlling
WHERE origination_date >= date('now', '-12 months')
GROUP BY month;

-- Loan Concentration Risk (max 25% per sector per cost center)
CREATE VIEW controlling_concentration_risk AS
SELECT
    cost_center,
    sector,
    SUM(outstanding_amount) AS sector_exposure,
    SUM(SUM(outstanding_amount)) OVER (PARTITION BY cost_center) AS total_exposure,
    SUM(outstanding_amount) * 1.0 / SUM(SUM(outstanding_amount)) OVER (PARTITION BY cost_center) AS concentration_ratio
FROM v_loans_controlling
GROUP BY cost_center, sector
HAVING concentration_ratio > 0.15;  -- Alert threshold