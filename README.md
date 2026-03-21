# OpenReg: Synthetic Regulatory Reporting & Controlling Data Platform

> A Data Vault 2.0 ETL pipeline for regulatory reporting (FINREP / COREP / Basel III),
> internal controlling KPIs, and a role-gated Streamlit dashboard — built with Python,
> SQLite / PostgreSQL, and Docker.

---

## 🏃 Quick Start

```bash
# 1. Clone
git clone https://github.com/TMFNK/openreg.git
cd openreg

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env          # fill in passwords before production use

# 4. Run full pipeline (SQLite – no external services needed)
python run_pipeline.py

# 5. Launch dashboard
streamlit run dashboard/app.py
```

---

## 📐 Architecture

```mermaid
graph TD
    A[Synthetic Generator] --> B[Raw CSVs]
    B --> C[Data Transformer]
    C --> D[DQ Engine]
    D --> E{Quality >= 98%?}
    E -->|No|  F[Abort & Alert]
    E -->|Yes| G[Data Vault Loader]
    G --> H[(SQLite or PostgreSQL)]
    H --> I[Regulatory Views]
    H --> J[Controlling Views]
    H --> K[RLS Views]
    I --> L[FINREP / COREP CSVs]
    J --> M[KPI Reports]
    K --> N[Streamlit Dashboard]
    G --> O[Audit Log]
```

---

## 📂 Generated Reports

| Report             | Location                    | Description                          |
| ------------------ | --------------------------- | ------------------------------------ |
| FINREP F18         | `reports/finrep/`           | Credit quality buckets by sector     |
| COREP CR SA        | `reports/corep/`            | Risk-weighted assets under Basel III |
| NPL Ratio          | `reports/kpi_npl_ratio.csv` | Key regulatory KPI                   |
| Cost Center Profit | `reports/controlling/`      | Internal profitability               |

---

## 🔒 Row-Level Security

```sql
-- Regulator sees everything
SELECT * FROM v_loans_regulator;

-- Controlling sees only CC_1001–CC_1003
SELECT * FROM v_loans_controlling;

-- Risk sees anonymised data
SELECT * FROM v_loans_risk;
```

---

## 🐳 Docker Deployment

```bash
# Copy and edit environment variables first
cp .env.example .env

# Dev stack (PostgreSQL + pgAdmin + Redis)
docker compose --profile dev up -d

# Full production stack
docker compose up -d

# With monitoring (Prometheus + Grafana)
docker compose --profile monitoring up -d
```

Service endpoints:

| Service             | URL                                          |
| ------------------- | -------------------------------------------- |
| Streamlit Dashboard | http://localhost:8501                        |
| pgAdmin             | http://localhost:5050 _(dev profile)_        |
| Grafana             | http://localhost:3000 _(monitoring profile)_ |
| Prometheus          | http://localhost:9090 _(monitoring profile)_ |

---

## 🔍 Data Quality

```bash
cat data/dq_results/dq_report.csv
```

The pipeline aborts if the overall DQ score falls below the `dq_thresholds.completeness` value in `config.yaml` (default **98%**).

---

## 📖 Documentation

- **[Architecture & Data Flow](docs/architecture.md)** – ETL pipeline components and data transformation
- **[Data Vault Model](docs/data_vault_model.mmd)** – Hubs, Links, Satellites, point-in-time recovery
- **[Regulatory Report Definitions](docs/regulatory_report_definitions.md)** – FINREP F18, COREP CR SA, LCR, NPL formulas
- **[Controlling KPIs](docs/kpis.md)** – Cost-centre profitability, efficiency ratios
- **[Security & RLS](docs/security.md)** – Multi-role access control, data masking, RBAC
- **[Project Description (PDF)](docs/Project%20Description%20Document.pdf)** – Full technical overview

---

## 🎯 Skills Demonstrated

| Skill                   | Evidence                                                               |
| ----------------------- | ---------------------------------------------------------------------- |
| Security Implementation | bcrypt auth, session management, RBAC, timing-attack prevention        |
| Regulatory Reporting    | FINREP F18, COREP CR SA, LCR, NPL ratios, Basel III                    |
| Controlling & KPIs      | Cost-centre profitability, MoM growth, concentration risk              |
| Data Quality Framework  | 98% completeness gate, automated validation, exponential backoff retry |
| Row-Level Security      | Role-based views (Regulator / Controlling / Risk), data masking        |
| Multi-Database          | PostgreSQL (production), SQLite (development), Data Vault 2.0          |
| Data Vault 2.0          | Hubs, Links, Satellites, temporal data management                      |
| ETL Pipeline            | End-to-end pipeline with structured error handling and logging         |
| Comprehensive Testing   | Unit tests, parameterised tests, mock authentication, fixtures         |
| Monitoring & Alerting   | Prometheus metrics, Grafana dashboards                                 |
| Audit Trail             | Complete ETL audit log, data dictionary, Mermaid diagrams              |
| Docker Infrastructure   | Multi-stage build, container orchestration, Compose profiles           |
| Caching & Performance   | Redis, DB indexing, query optimisation                                 |

---

## 🤝 Contributing

PRs are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

Focus areas:

- Additional regulatory templates (AnaCredit, IRRBB, NSFR)
- More sophisticated DQ rules
- PostgreSQL RLS policies (native `CREATE POLICY`)
- Expanded test coverage
- Performance optimisations

---

## License

MIT – see [LICENSE](LICENSE) for details.

**Data**: 100% synthetic – no GDPR or confidentiality risks.  
**Time to demo**: < 5 minutes from clone to reports.
