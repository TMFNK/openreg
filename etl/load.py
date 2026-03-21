import sqlite3
import pandas as pd
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class DataVaultLoader:
    def __init__(self, db_path='data/processed/openreg.db'):
        self.conn = sqlite3.connect(db_path)
        self.run_id = str(uuid.uuid4())
        
    def log_etl_start(self, process_name):
        """Audit logging"""
        logger.info(f"Starting ETL: {process_name} | Run ID: {self.run_id}")
        self.conn.execute("""
            INSERT INTO etl_audit_log (run_id, process_name, start_time, status)
            VALUES (?, ?, ?, 'STARTED')
        """, (self.run_id, process_name, datetime.now()))
        self.conn.commit()

    def log_etl_end(self, process_name, status, records_processed=0, error_msg=None):
        """Audit logging"""
        self.conn.execute("""
            UPDATE etl_audit_log 
            SET end_time = ?, status = ?, records_processed = ?, error_message = ?
            WHERE run_id = ?
        """, (datetime.now(), status, records_processed, error_msg, self.run_id))
        self.conn.commit()
        logger.info(f"ETL {process_name} completed with status: {status}")

    def load_hub(self, df, hub_name):
        """Load Data Vault hub"""
        self.log_etl_start(f"load_hub_{hub_name}")
        try:
            df.to_sql(f'hub_{hub_name}', self.conn, if_exists='append', index=False)
            self.log_etl_end(f"load_hub_{hub_name}", 'SUCCESS', len(df))
        except Exception as e:
            self.log_etl_end(f"load_hub_{hub_name}", 'FAILED', error_msg=str(e))
            raise

    def load_satellite(self, df, sat_name):
        """Load Data Vault satellite"""
        self.log_etl_start(f"load_sat_{sat_name}")
        try:
            df.to_sql(f'sat_{sat_name}', self.conn, if_exists='append', index=False)
            self.log_etl_end(f"load_sat_{sat_name}", 'SUCCESS', len(df))
        except Exception as e:
            self.log_etl_end(f"load_sat_{sat_name}", 'FAILED', error_msg=str(e))
            raise

    def load_link(self, df, link_name):
        """Load Data Vault link"""
        self.log_etl_start(f"load_link_{link_name}")
        try:
            df.to_sql(f'link_{link_name}', self.conn, if_exists='append', index=False)
            self.log_etl_end(f"load_link_{link_name}", 'SUCCESS', len(df))
        except Exception as e:
            self.log_etl_end(f"load_link_{link_name}", 'FAILED', error_msg=str(e))
            raise

    def run_full_load(self, datasets):
        """Execute full pipeline"""
        logger.info("Starting full Data Vault load...")
        
        # Load hubs
        self.load_hub(datasets['customers'][['customer_hash', 'customer_id', 'load_datetime', 'record_source']], 
                     'customer')
        self.load_hub(datasets['accounts'][['account_hash', 'account_id', 'load_datetime', 'record_source']], 
                     'account')
        self.load_hub(datasets['loans'][['loan_hash', 'loan_id', 'load_datetime', 'record_source']], 
                     'loan')
        
        # Load satellites
        self.load_satellite(datasets['loans'], 'loan_details')
        self.load_satellite(datasets['customers'], 'customer_details')

        # Load collateral satellite (needs additional columns)
        self.log_etl_start("load_sat_collateral")
        try:
            collateral_df = datasets['collateral'].copy()
            loans_lookup = dict(zip(datasets['loans']['loan_id'], datasets['loans']['loan_hash']))
            collateral_df['loan_hash'] = collateral_df['loan_id'].map(loans_lookup)
            collateral_df['load_datetime'] = datetime.now()
            collateral_df['record_source'] = 'SYNTHETIC'
            collateral_df = collateral_df[['loan_hash', 'load_datetime', 'record_source', 'collateral_type', 'market_value', 'haircut']]
            collateral_df.to_sql('sat_collateral', self.conn, if_exists='append', index=False)
            self.log_etl_end("load_sat_collateral", 'SUCCESS', len(collateral_df))
        except Exception as e:
            self.log_etl_end("load_sat_collateral", 'FAILED', error_msg=str(e))
            raise
        
        # Load links
        from etl.transform import DataTransformer
        transformer = DataTransformer()
        cust_acc_links, acc_loan_links = transformer.create_links(datasets['customers'], datasets['accounts'], datasets['loans'])
        self.load_link(cust_acc_links, 'customer_account')
        self.load_link(acc_loan_links, 'account_loan')
        
        # Load GL entries
        datasets['gl_entries'].to_sql('hub_gl_entries', self.conn, if_exists='append', index=False)
        
        logger.info("✅ Full load completed successfully!")
