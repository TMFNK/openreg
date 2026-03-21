import pandas as pd
import numpy as np
import hashlib
import yaml
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataTransformer:
    def __init__(self, dq_rules_path="dq/dq_rules.yaml"):
        with open(dq_rules_path, "r") as f:
            self.dq_rules = yaml.safe_load(f)

    def calculate_hash_diff(self, row, columns):
        """Data Vault hash diff calculation"""
        concatenated = "".join([str(row[col]) for col in sorted(columns)])
        return hashlib.md5(concatenated.encode()).hexdigest()

    def clean_customers(self, customers_df):
        """Transform customer data with validations"""
        logger.info("Cleaning customers dataset...")

        # Remove duplicates
        customers_df = customers_df.drop_duplicates(subset=["customer_id"])

        # Handle missing values
        customers_df["sector"] = customers_df["sector"].fillna("UNKNOWN")

        # Calculate hash_diff for Data Vault
        satellite_columns = ["customer_type", "country", "sector"]
        customers_df["hash_diff"] = customers_df.apply(
            lambda row: self.calculate_hash_diff(row, satellite_columns), axis=1
        )

        return customers_df

    def clean_loans(self, loans_df):
        """Transform loan data with validations"""
        logger.info("Cleaning loans dataset...")

        # Remove duplicates
        loans_df = loans_df.drop_duplicates(subset=["loan_id"])

        # Handle missing values
        loans_df["sector"] = loans_df["sector"].fillna("UNKNOWN")

        # Standardize currency codes
        loans_df["currency"] = loans_df["currency"].str.upper()

        # Calculate hash_diff for Data Vault
        satellite_columns = [
            "principal_amount",
            "outstanding_amount",
            "interest_rate",
            "ltv_ratio",
            "pd_rating",
            "lgd",
            "ead",
            "risk_weight",
        ]
        loans_df["hash_diff"] = loans_df.apply(
            lambda row: self.calculate_hash_diff(row, satellite_columns), axis=1
        )

        return loans_df

    def create_links(self, customers_df, accounts_df, loans_df):
        """Create Data Vault link tables"""
        logger.info("Creating link tables...")

        # Link Customer-Account (many-to-many)
        customer_account_links = []
        for _, account in accounts_df.iterrows():
            # Randomly assign 1-2 customers per account
            linked_customers = customers_df.sample(n=np.random.randint(1, 3))
            for _, customer in linked_customers.iterrows():
                link_hash = hashlib.md5(
                    f"{customer['customer_hash']}{account['account_hash']}".encode()
                ).hexdigest()
                customer_account_links.append(
                    {
                        "link_hash": link_hash,
                        "customer_hash": customer["customer_hash"],
                        "account_hash": account["account_hash"],
                        "load_datetime": datetime.now(),
                        "record_source": "SYNTHETIC",
                    }
                )

        # Link Account-Loan (one-to-one for simplicity)
        account_loan_links = []
        loan_sample = loans_df.sample(min(len(loans_df), len(accounts_df)))
        for (_, loan), (_, account) in zip(loan_sample.iterrows(), accounts_df.iterrows()):
            link_hash = hashlib.md5(f"{account['account_hash']}{loan['loan_hash']}".encode()).hexdigest()
            account_loan_links.append(
                {
                    "link_hash": link_hash,
                    "account_hash": account["account_hash"],
                    "loan_hash": loan["loan_hash"],
                    "load_datetime": datetime.now(),
                    "record_source": "SYNTHETIC",
                }
            )

        return pd.DataFrame(customer_account_links), pd.DataFrame(account_loan_links)

    def validate_accounting_equation(self, gl_df):
        """Check Assets = Liabilities + Equity"""
        assets = gl_df[gl_df["account"].str.startswith("1")]["amount"].sum()
        liabilities = gl_df[gl_df["account"].str.startswith("2")]["amount"].sum()
        equity = gl_df[gl_df["account"].str.startswith("3")]["amount"].sum()

        balance_diff = abs(assets - (liabilities + equity))
        tolerance = self.dq_rules.get("accounting_tolerance", 0.01)

        if balance_diff > tolerance:
            logger.warning(f"Accounting equation mismatch: {balance_diff:.2f}")
            return False
        return True
