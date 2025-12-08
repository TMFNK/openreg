# Regulatory Report Definitions

## FINREP F18: Credit Quality

- **Purpose**: Report credit quality breakdown by exposure class
- **Source**: `sat_loan_details.npl_status`, `pd_rating`
- **Buckets**: Performing, NPL, Low/Medium/High risk
- **Frequency**: Monthly
- **Threshold**: NPL ratio &gt; 5% triggers escalation

## COREP CR SA: Standardized Credit Risk

- **Purpose**: Calculate Risk-Weighted Assets (RWA)
- **Formula**: RWA = EAD × Risk Weight
- **Source**: `sat_loan_details.risk_weight`, `ead`
- **CRM**: Collateral reduces EAD via haircuts
