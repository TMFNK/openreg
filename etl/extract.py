"""
Synthetic Banking Data Generator
GDPR-safe, Basel III/FINREP realistic data
"""

import pandas as pd
import numpy as np
import hashlib
from faker import Faker
from datetime import datetime, timedelta
import yaml
import logging
from tqdm import tqdm

fake = Faker()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyntheticBankDataGenerator:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.num_customers = self.config["synthetic_data"]["num_customers"]
        self.num_accounts = self.config["synthetic_data"]["num_accounts"]
        self.num_loans = self.config["synthetic_data"]["num_loans"]
        self.start_date = datetime.strptime(self.config["synthetic_data"]["start_date"], "%Y-%m-%d")
        self.end_date = datetime.strptime(self.config["synthetic_data"]["end_date"], "%Y-%m-%d")

    def generate_customers(self):
        """Generate customer hub (Hub_Customer)"""
        logger.info("Generating customers...")
        customers = []
        for i in tqdm(range(self.num_customers), desc="Customers"):
            customers.append(
                {
                    "customer_id": f"CUST_{i:08d}",
                    "customer_hash": hashlib.md5(f"CUST_{i:08d}".encode()).hexdigest(),
                    "record_source": "SYNTHETIC",
                    "load_datetime": datetime.now(),
                    "customer_type": np.random.choice(["RETAIL", "CORPORATE"], p=[0.8, 0.2]),
                    "country": np.random.choice(
                        ["DE", "FR", "IT", "ES", "NL"], p=[0.3, 0.2, 0.2, 0.15, 0.15]
                    ),
                    "sector": np.random.choice(
                        [
                            "MANUFACTURING",
                            "REAL_ESTATE",
                            "FINANCIAL",
                            "AGRICULTURE",
                            "SERVICES",
                            "CONSTRUCTION",
                            "RETAIL_TRADE",
                            None,
                        ],
                        p=[0.1, 0.15, 0.1, 0.05, 0.25, 0.1, 0.15, 0.1],
                    ),
                }
            )
        return pd.DataFrame(customers)

    def generate_accounts(self):
        """Generate account hub (Hub_Account)"""
        logger.info("Generating accounts...")
        accounts = []
        for i in tqdm(range(self.num_accounts), desc="Accounts"):
            accounts.append(
                {
                    "account_id": f"ACC_{i:08d}",
                    "account_hash": hashlib.md5(f"ACC_{i:08d}".encode()).hexdigest(),
                    "record_source": "SYNTHETIC",
                    "load_datetime": datetime.now(),
                    "account_type": np.random.choice(
                        ["CURRENT", "SAVINGS", "TERM_DEPOSIT"], p=[0.6, 0.3, 0.1]
                    ),
                    "currency": np.random.choice(["EUR", "USD"], p=[0.9, 0.1]),
                    "opening_date": fake.date_between(start_date=self.start_date, end_date=self.end_date),
                }
            )
        return pd.DataFrame(accounts)

    def generate_loans(self):
        """Generate loan hub with satellites (Hub_Loan + Sat_Loan_Details)"""
        logger.info("Generating loans...")
        loans = []
        for i in tqdm(range(self.num_loans), desc="Loans"):
            loan_id = f"LOAN_{i:08d}"
            origination_date = fake.date_between(start_date=self.start_date, end_date=self.end_date)
            maturity_date = origination_date + timedelta(days=np.random.randint(365, 3650))
            principal = round(np.random.lognormal(mean=12, sigma=1.5), 2)  # ~€160k avg

            # Basel risk parameters
            pd_rating = np.random.beta(2, 8)  # ~20% default probability
            lgd = np.random.uniform(0.25, 0.80)  # Loss Given Default
            ead = principal * np.random.uniform(0.95, 1.0)  # Exposure at Default

            loans.append(
                {
                    "loan_id": loan_id,
                    "loan_hash": hashlib.md5(loan_id.encode()).hexdigest(),
                    "record_source": "SYNTHETIC",
                    "load_datetime": datetime.now(),
                    "origination_date": origination_date,
                    "maturity_date": maturity_date,
                    "principal_amount": principal,
                    "outstanding_amount": principal * np.random.uniform(0.5, 1.0),
                    "interest_rate": np.random.uniform(0.01, 0.08),
                    "currency": "EUR",
                    "ltv_ratio": np.random.uniform(0.5, 1.1),  # Can exceed 100% for NPLs
                    "cost_center": f"CC_{np.random.randint(1000, 1050)}",
                    "pd_rating": pd_rating,
                    "lgd": lgd,
                    "ead": ead,
                    "risk_weight": np.random.choice([0.35, 0.75, 1.0, 1.5], p=[0.1, 0.5, 0.3, 0.1]),
                    "npl_status": np.random.choice([0, 1], p=[0.92, 0.08]),  # 8% NPL ratio
                    "sector": np.random.choice(
                        ["REAL_ESTATE", "MANUFACTURING", "SERVICES", "CONSTRUCTION"],
                        p=[0.4, 0.2, 0.25, 0.15],
                    ),
                }
            )
        return pd.DataFrame(loans)

    def generate_collateral(self, loans_df):
        """Generate collateral for loans (reduces EAD)"""
        logger.info("Generating collateral...")
        collateral = []
        for _, loan in tqdm(loans_df.iterrows(), total=len(loans_df), desc="Collateral"):
            if loan["ltv_ratio"] < 1.0:  # Only secured loans have collateral
                collateral.append(
                    {
                        "collateral_id": f"COL_{hashlib.md5(loan['loan_id'].encode()).hexdigest()[:8]}",
                        "loan_id": loan["loan_id"],
                        "collateral_type": np.random.choice(["REAL_ESTATE", "FINANCIAL_INSTRUMENTS", "CASH"]),
                        "market_value": loan["outstanding_amount"] * np.random.uniform(0.7, 0.9),
                        "haircut": np.random.uniform(0.1, 0.3),
                    }
                )
        return pd.DataFrame(collateral)

    def generate_transactions(self, accounts_df):
        """Generate realistic transaction history"""
        logger.info("Generating transactions...")
        transactions = []
        for _, account in tqdm(accounts_df.iterrows(), total=len(accounts_df), desc="Transactions"):
            num_txns = np.random.randint(50, 500)
            for _ in range(num_txns):
                txn_date = fake.date_between(start_date=account["opening_date"], end_date=self.end_date)
                transactions.append(
                    {
                        "transaction_id": f"TXN_{fake.uuid4()}",
                        "account_id": account["account_id"],
                        "transaction_date": txn_date,
                        "amount": round(np.random.normal(loc=0, scale=1000), 2),
                        "currency": account["currency"],
                        "counterparty_country": fake.country_code(),
                    }
                )
        return pd.DataFrame(transactions)

    def generate_gl_entries(self, loans_df, transactions_df):
        """Simplified General Ledger (HGB/IFRS)"""
        logger.info("Generating GL entries...")
        gl_entries = []

        # Loan origination entries
        for _, loan in loans_df.iterrows():
            # Debit: Loans receivable
            gl_entries.append(
                {
                    "gl_entry_id": f"GL_{hashlib.md5((loan['loan_id'] + '_DR').encode()).hexdigest()}",
                    "entry_date": loan["origination_date"],
                    "account": "1120_LOANS_RECEIVABLE",
                    "debit_credit": "DR",
                    "amount": loan["principal_amount"],
                    "cost_center": loan["cost_center"],
                }
            )
            # Credit: Cash
            gl_entries.append(
                {
                    "gl_entry_id": f"GL_{hashlib.md5((loan['loan_id'] + '_CR').encode()).hexdigest()}",
                    "entry_date": loan["origination_date"],
                    "account": "1000_CASH",
                    "debit_credit": "CR",
                    "amount": loan["principal_amount"],
                    "cost_center": loan["cost_center"],
                }
            )

        return pd.DataFrame(gl_entries)

    def save_all_datasets(self):
        """Generate and save all datasets"""

        # Generate
        customers_df = self.generate_customers()
        accounts_df = self.generate_accounts()
        loans_df = self.generate_loans()
        collateral_df = self.generate_collateral(loans_df)
        transactions_df = self.generate_transactions(accounts_df)
        gl_entries_df = self.generate_gl_entries(loans_df, transactions_df)

        # Save
        customers_df.to_csv("data/raw/hub_customer.csv", index=False)
        accounts_df.to_csv("data/raw/hub_account.csv", index=False)
        loans_df.to_csv("data/raw/hub_loan_sat_loan.csv", index=False)
        collateral_df.to_csv("data/raw/sat_collateral.csv", index=False)
        transactions_df.to_csv("data/raw/sat_transactions.csv", index=False)
        gl_entries_df.to_csv("data/raw/hub_gl_entries.csv", index=False)

        logger.info("✅ All datasets generated successfully!")
        return {
            "customers": customers_df,
            "accounts": accounts_df,
            "loans": loans_df,
            "collateral": collateral_df,
            "transactions": transactions_df,
            "gl_entries": gl_entries_df,
        }


if __name__ == "__main__":
    generator = SyntheticBankDataGenerator()
    generator.save_all_datasets()
