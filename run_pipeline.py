"""
OpenReg ETL Orchestrator
One-command execution: python run_pipeline.py
"""

import logging
import sys
import os

import pandas as pd
import sqlite3
import yaml

from etl.extract import SyntheticBankDataGenerator
from etl.transform import DataTransformer
from etl.load import DataVaultLoader
from dq.dq_checks import DataQualityEngine
from utils.error_handling import DataQualityError, ConfigurationError


def _setup_logging() -> logging.Logger:
    """Configure logging AFTER the logs/ directory exists."""
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("logs/etl.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)


def _load_config(logger: logging.Logger) -> dict:
    """Load YAML config, falling back to safe defaults on error."""
    try:
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning("config.yaml not found – using built-in defaults.")
        return {}
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"Malformed config.yaml: {exc}") from exc


def _init_database(db_path: str) -> None:
    """Drop-and-recreate the SQLite database from schema."""
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    with open("sql/schema.sql", "r") as f:
        conn.executescript(f.read())
    conn.close()


def _apply_sql_file(db_path: str, sql_file: str) -> None:
    """Execute a SQL script file against the SQLite database."""
    conn = sqlite3.connect(db_path)
    with open(sql_file, "r") as f:
        conn.executescript(f.read())
    conn.close()


def main() -> None:
    """Execute the full ETL pipeline."""
    # ── 0. Directories & logging ────────────────────────────────────────────
    logger = _setup_logging()
    logger.info("🚀 Starting OpenReg Pipeline")

    for directory in (
        "data/raw",
        "data/processed",
        "data/dq_results",
        "reports/finrep",
        "reports/corep",
        "reports/controlling",
    ):
        os.makedirs(directory, exist_ok=True)

    # ── 1. Config ────────────────────────────────────────────────────────────
    config = _load_config(logger)
    db_path = (
        config.get("database", {}).get("sqlite", {}).get("path", "data/processed/openreg.db")
    )
    dq_threshold = (
        config.get("dq_thresholds", {}).get("completeness", 0.98)
    )

    # ── 2. Database init ─────────────────────────────────────────────────────
    _init_database(db_path)

    try:
        # ── 3. Extract ───────────────────────────────────────────────────────
        logger.info("1️⃣  Extract Phase")
        generator = SyntheticBankDataGenerator()
        datasets = generator.save_all_datasets()

        # ── 4. Transform ─────────────────────────────────────────────────────
        logger.info("2️⃣  Transform Phase")
        transformer = DataTransformer()
        datasets["customers"] = transformer.clean_customers(datasets["customers"])
        datasets["loans"] = transformer.clean_loans(datasets["loans"])

        # ── 5. Data Quality ──────────────────────────────────────────────────
        logger.info("3️⃣  Data Quality Phase")
        dq_engine = DataQualityEngine()
        overall_score, dq_report = dq_engine.run_all_checks(datasets)
        logger.info(f"DQ score: {overall_score:.2%}  (threshold: {dq_threshold:.2%})")

        if overall_score < dq_threshold:
            raise DataQualityError(
                f"DQ score {overall_score:.2%} is below threshold {dq_threshold:.2%}. Aborting."
            )

        # ── 6. Load to Data Vault ────────────────────────────────────────────
        logger.info("4️⃣  Load Phase")
        loader = DataVaultLoader()
        loader.run_full_load(datasets)

        # ── 7. Create Views ──────────────────────────────────────────────────
        logger.info("5️⃣  Creating Regulatory & Controlling Views")
        for sql_file in (
            "sql/regulatory_views.sql",
            "sql/controlling_views.sql",
            "sql/rls_views.sql",
        ):
            _apply_sql_file(db_path, sql_file)

        # ── 8. Generate Reports ──────────────────────────────────────────────
        logger.info("6️⃣  Generating Reports")
        conn = sqlite3.connect(db_path)
        report_queries = {
            "reports/finrep/finrep_f18_credit_quality.csv": "SELECT * FROM finrep_f18_credit_quality",
            "reports/corep/corep_cr_sa_exposure.csv": "SELECT * FROM corep_cr_sa_exposure",
            "reports/controlling/cost_center_profitability.csv": "SELECT * FROM controlling_cost_center_profit",
        }
        for csv_path, query in report_queries.items():
            pd.read_sql(query, conn).to_csv(csv_path, index=False)
            logger.info(f"   → {csv_path}")
        conn.close()

        logger.info("✅ Pipeline completed successfully!")
        logger.info("📊 Reports generated in reports/")
        logger.info("🔒 DQ report saved to data/dq_results/dq_report.csv")

    except DataQualityError as exc:
        logger.error(f"Data quality gate failed: {exc}")
        sys.exit(1)
    except Exception as exc:
        logger.error(f"Pipeline failed: {exc}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()