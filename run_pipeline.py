"""
OpenReg ETL Orchestrator
One-command execution: python run_pipeline.py
"""
import logging
import sys
import pandas as pd
import os
from etl.extract import SyntheticBankDataGenerator
from etl.transform import DataTransformer
from etl.load import DataVaultLoader
from dq.dq_checks import DataQualityEngine
import sqlite3

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/etl.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    """Execute full pipeline"""
    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting OpenReg Pipeline")

    # Create required directories
    os.makedirs('data/raw', exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)
    os.makedirs('data/dq_results', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('reports/finrep', exist_ok=True)
    os.makedirs('reports/corep', exist_ok=True)
    os.makedirs('reports/controlling', exist_ok=True)

    # Initialize database schema (fresh start)
    if os.path.exists('data/processed/openreg.db'):
        os.remove('data/processed/openreg.db')

    conn = sqlite3.connect('data/processed/openreg.db')
    with open('sql/schema.sql', 'r') as f:
        conn.executescript(f.read())
    conn.close()

    try:
        # Step 1: Extract
        logger.info("1️⃣ Extract Phase")
        generator = SyntheticBankDataGenerator()
        datasets = generator.save_all_datasets()
        
        # Step 2: Transform & DQ
        logger.info("2️⃣ Transform Phase")
        transformer = DataTransformer()
        datasets['customers'] = transformer.clean_customers(datasets['customers'])
        datasets['loans'] = transformer.clean_loans(datasets['loans'])
        
        # Step 3: Data Quality
        logger.info("3️⃣ Data Quality Phase")
        dq_engine = DataQualityEngine()
        overall_score, dq_report = dq_engine.run_all_checks(datasets)
        
        if overall_score < 0.95:
            logger.error(f"DQ score {overall_score:.2%} below threshold. Aborting.")
            sys.exit(1)
        
        # Step 4: Load to Data Vault
        logger.info("4️⃣ Load Phase")
        loader = DataVaultLoader()
        loader.run_full_load(datasets)
        
        # Step 5: Create Views
        logger.info("5️⃣ Creating Regulatory & Controlling Views")
        conn = sqlite3.connect('data/processed/openreg.db')
        
        with open('sql/regulatory_views.sql', 'r') as f:
            conn.executescript(f.read())
        
        with open('sql/controlling_views.sql', 'r') as f:
            conn.executescript(f.read())
        
        with open('sql/rls_views.sql', 'r') as f:
            conn.executescript(f.read())
        
        conn.close()
        
        # Step 6: Generate Reports
        logger.info("6️⃣ Generating Reports")
        conn = sqlite3.connect('data/processed/openreg.db')
        
        # FINREP
        finrep = pd.read_sql("SELECT * FROM finrep_f18_credit_quality", conn)
        finrep.to_csv('reports/finrep/finrep_f18_credit_quality.csv', index=False)
        
        # COREP
        corep = pd.read_sql("SELECT * FROM corep_cr_sa_exposure", conn)
        corep.to_csv('reports/corep/corep_cr_sa_exposure.csv', index=False)
        
        # Controlling
        controlling = pd.read_sql("SELECT * FROM controlling_cost_center_profit", conn)
        controlling.to_csv('reports/controlling/cost_center_profitability.csv', index=False)
        
        conn.close()
        
        logger.info("✅ Pipeline completed successfully!")
        logger.info("📊 Reports generated in reports/")
        logger.info("🔒 DQ report saved to data/dq_results/dq_report.csv")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
