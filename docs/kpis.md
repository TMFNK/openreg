# Controlling KPIs

## Overview

This document outlines the key controlling (management accounting) KPIs implemented in the OpenReg platform for internal profitability analysis and cost-center performance tracking.

## Cost Center Structure

The platform categorizes costs and revenues by the following cost center hierarchy:

- **CC_1001**: Retail Banking - Consumer loans and deposit accounts
- **CC_1002**: Corporate Banking - Business loans and corporate deposits
- **CC_1003**: Investment Banking - Capital markets and advisory services

## Key Performance Indicators (KPIs)

### 1. Profitability KPIs

#### Net Interest Margin (NIM)

```sql
-- Formula: (Interest Revenue - Interest Expense) / Average Earning Assets
SELECT
    cost_center,
    ROUND(
        (SUM(interest_revenue) - SUM(interest_expense)) /
        AVG(balance) * 100, 2
    ) as nim_percentage
FROM v_controlling_profit
GROUP BY cost_center;
```

**Target**: 2.5-4.0% depending on risk profile
**Calculation**: Monthly, annualized

#### Return on Assets (ROA)

```sql
-- Formula: Net Profit / Average Assets
SELECT
    cost_center,
    ROUND(SUM(net_profit) / AVG(total_assets) * 100, 2) as roa_percentage
FROM v_controlling_profit
GROUP BY cost_center;
```

**Target**: 1.0-2.0% for retail, 0.5-1.5% for corporate

#### Return on Equity (ROE)

```sql
-- Formula: Net Profit / Equity Capital
SELECT
    cost_center,
    ROUND(SUM(net_profit) / AVG(equity) * 100, 2) as roe_percentage
FROM v_controlling_profit
GROUP BY cost_center;
```

**Target**: 10-15% depending on risk appetite

### 2. Growth KPIs

#### Month-over-Month Growth (MoM)

```sql
-- Formula: (Current Month - Previous Month) / Previous Month
SELECT
    cost_center,
    metric,
    ROUND(
        (current_value - previous_value) / NULLIF(previous_value, 0) * 100, 2
    ) as mom_growth_percentage
FROM v_controlling_mom_growth;
```

**Target**: 5-15% sustainable growth quarter-over-quarter

#### Customer Acquisition Cost (CAC)

```sql
-- Formula: Total Marketing & Acquisition Costs / New Customers
SELECT
    cost_center,
    ROUND(SUM(marketing_costs) / COUNT(new_customers), 2) as cac
FROM v_controlling_acquisition;
```

**Target**: < €500 for retail, < €5,000 for corporate

### 3. Concentration Risk KPIs

#### Herfindahl-Hirschman Index (HHI)

```sql
-- Formula: Sum of squared market shares
SELECT
    sector,
    ROUND(SUM(POWER(market_share, 2)), 2) as hhi_index
FROM v_controlling_concentration
GROUP BY sector;
```

**Interpretation**:

- < 1,500: Unconcentrated
- 1,500-2,500: Moderately concentrated
- > 2,500: Highly concentrated

#### Top 10 Customer Concentration

```sql
-- Formula: Sum of balances for top 10 customers / Total portfolio
SELECT
    cost_center,
    ROUND(SUM(top10_balance) / SUM(total_balance) * 100, 2) as concentration_ratio
FROM v_controlling_customer_concentration;
```

**Target**: < 20% maximum exposure to avoid concentration risk

### 4. Efficiency KPIs

#### Cost-Income Ratio (CIR)

```sql
-- Formula: Operating Costs / Operating Income
SELECT
    cost_center,
    ROUND(SUM(operating_costs) / SUM(operating_income) * 100, 2) as cir_percentage
FROM v_controlling_efficiency;
```

**Target**: 50-70% efficiency ratio

#### Revenue per Employee (RPE)

```sql
-- Formula: Total Revenue / Number of Employees
SELECT
    cost_center,
    ROUND(SUM(total_revenue) / AVG(employee_count), 0) as revenue_per_employee
FROM v_controlling_productivity;
```

**Target**: > €250,000 per employee annually

## Dashboard Integration

Controlling KPIs are available through the Streamlit dashboard (`dashboard/app.py`) with:

- Real-time profit & loss statements by cost center
- Historical trend analysis (quarterly/annual)
- Variance analysis vs. budget
- Risk-adjusted performance metrics

## Reporting

Monthly controlling reports are generated to `reports/controlling/` containing:

- Profit & Loss statements by cost center
- KPI dashboards and trend charts
- Budget vs. actual analysis
- Risk-adjusted return metrics

## Data Sources

All controlling KPIs are calculated from the Data Vault layer using views defined in:

- `sql/controlling_views.sql` - Core controlling calculations
- `sql/schema.sql` - Underlying data structures

KPIs are recalculated nightly as part of the ETL pipeline (`run_pipeline.py`).
