# 🏦 OpenReg: Synthetic Regulatory Reporting & Controlling Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)]()

A demonstration of **Data Engineering + Regulatory Reporting + Compliance** skills using synthetic banking data, Data Vault 2.0, and modern Python/SQL pipelines.

## 🎯 What This Project Proves

| Skill                    | Evidence                                                  |
| ------------------------ | --------------------------------------------------------- |
| **Regulatory Reporting** | FINREP F18, COREP CR SA, LCR, NPL ratios                  |
| **Controlling**          | Cost-center profitability, MoM growth, concentration risk |
| **Data Quality**         | Configurable DQ framework with 98% completeness threshold |
| **Row-Level Security**   | Role-based views (Regulator/Controlling/Risk)             |
| **Data Vault 2.0**       | Hubs, Links, Satellites for auditability                  |
| **ETL Pipeline**         | Python + SQLite with full logging & error handling        |
| **Audit Trail**          | `etl_audit_log` table tracks every run                    |
| **Lineage**              | Data dictionary + Mermaid diagrams                        |

## 📊 Architecture

```mermaid
graph TD
    A[Synthetic Generator] --&gt; B[Raw CSVs];
    B --&gt; C[Data Transformer];
    C --&gt; D[DQ Engine];
    D --&gt; E{Quality &gt;= 95%?};
    E --&gt;|No| F[Abort & Alert];
    E --&gt;|Yes| G[Data Vault Loader];
    G --&gt; H[(SQLite)];
    H --&gt; I[Regulatory Views];
    H --&gt; J[Controlling Views];
    H --&gt; K[RLS Views];
    I --&gt; L[FINREP/COREP CSVs];
    J --&gt; M[KPI Reports];
    K --&gt; N[Streamlit Dashboard];
    G --&gt; O[Audit Log];
```

🏃 Quick Start

```bash
Copy
# Clone repo
git clone https://github.com/yourusername/openreg.git
cd openreg

# Install

pip install -r requirements.txt

# Run full pipeline (5 minutes)

python run_pipeline.py

# Launch dashboard
streamlit run dashboard/app.py
```

## 📂 Generated Reports

```table
| Report             | Location                    | Description                          |
| ------------------ | --------------------------- | ------------------------------------ |
| FINREP F18         | `reports/finrep/`           | Credit quality buckets by sector     |
| COREP CR SA        | `reports/corep/`            | Risk-weighted assets under Basel III |
| NPL Ratio          | `reports/kpi_npl_ratio.csv` | Key regulatory KPI                   |
| Cost Center Profit | `reports/controlling/`      | Internal profitability               |

```

🔍 Data Quality Results

```bash
cat data/dq_results/dq_report.csv
```

## 🔒 Row-Level Security

```sql
-- Regulator sees everything
SELECT * FROM v_loans_regulator;

-- Controlling sees only CC_1001-1003
SELECT * FROM v_loans_controlling;

-- Risk sees anonymized data
SELECT * FROM v_loans_risk;
```

## 📖 Documentation

Architecture
Data Vault Model
Regulatory Report Definitions
Controlling KPIs
Security & RLS

## 🎓 Learning Path

This project demonstrates exactly what banks need:
Technical: Python, SQL, Pandas, ETL
Domain: FINREP, COREP, Basel III, cost center logic
Compliance: DQ, audit logs, RLS, lineage

## 🤝 Contributing

PRs welcome! Focus on:
Additional regulatory templates
More sophisticated DQ rules
PostgreSQL support
Docker containerization
