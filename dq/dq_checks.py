"""
Data Quality Engine with Audit Trail
"""

from typing import Dict, Tuple

import pandas as pd
import yaml
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DataQualityEngine:
    def __init__(
        self, rules_path: str = "dq/dq_rules.yaml", completeness_threshold: float = 0.95
    ):
        self.completeness_threshold = completeness_threshold
        try:
            with open(rules_path, "r") as f:
                self.rules = yaml.safe_load(f)
        except FileNotFoundError:
            self.rules = {
                "completeness_threshold": 0.95,
                "ltv_max_threshold": 1.2,
                "accounting_tolerance": 0.01,
            }
        self.results = []

    def _check_completeness(self, df: pd.DataFrame, column: str) -> float:
        """Check completeness of a specific column"""
        if df is None or column not in df.columns:
            return 0.0
        total = len(df)
        if total == 0:
            return 1.0
        complete = df[column].notna().sum()
        return float(complete) / float(total)

    def _check_ltv_bounds(self, df: pd.DataFrame, max_ltv: float = 1.5) -> int:
        """Check LTV ratio bounds"""
        if df is None or "ltv_ratio" not in df.columns:
            return 0
        return int((df["ltv_ratio"] > max_ltv).sum())

    def _check_pd_range(
        self, df: pd.DataFrame, min_pd: float = 0.0, max_pd: float = 1.0
    ) -> int:
        """Check PD rating range"""
        if df is None or "pd_rating" not in df.columns:
            return 0
        return int(((df["pd_rating"] < min_pd) | (df["pd_rating"] > max_pd)).sum())

    def _check_lgd_range(self, df: pd.DataFrame) -> int:
        """Check LGD range [0, 1]"""
        if df is None or "lgd" not in df.columns:
            return 0
        return int(((df["lgd"] < 0.0) | (df["lgd"] > 1.0)).sum())

    def _check_accounting_balance(
        self,
        customers: pd.DataFrame,
        accounts: pd.DataFrame,
        loans: pd.DataFrame,
    ) -> float:
        """Check accounting balance - returns difference"""
        total_accounts = 0 if accounts is None else len(accounts)
        total_loans = 0 if loans is None else len(loans)
        return float(abs(total_accounts - total_loans))

    def check_completeness(self, df: pd.DataFrame, table_name: str) -> bool:
        """Rule 1: Completeness > threshold"""
        threshold = self.rules.get("completeness_threshold", 0.95)
        completeness = (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100

        passed = completeness >= threshold * 100
        self.results.append(
            {
                "table_name": table_name,
                "check_name": "completeness",
                "score": completeness,
                "threshold": threshold * 100,
                "passed": passed,
                "checked_at": datetime.now(),
            }
        )
        logger.info(
            f"DQ Completeness for {table_name}: {completeness:.2f}% {'✅' if passed else '❌'}"
        )
        return passed

    def check_ltv_bounds(self, loans_df: pd.DataFrame) -> bool:
        """Rule 2: LTV ratio validation (Basel: typically <= 120%)"""
        threshold = self.rules.get("ltv_max_threshold", 1.2)
        violations = loans_df[loans_df["ltv_ratio"] > threshold]

        passed = len(violations) == 0
        self.results.append(
            {
                "table_name": "loans",
                "check_name": "ltv_bounds",
                "score": len(loans_df) - len(violations),
                "threshold": threshold,
                "passed": passed,
                "checked_at": datetime.now(),
            }
        )
        logger.info(
            f"LTV violations: {len(violations)} / {len(loans_df)} {'✅' if passed else '❌'}"
        )
        return passed

    def check_referential_integrity(
        self,
        child_df: pd.DataFrame,
        parent_df: pd.DataFrame,
        child_key: str,
        parent_key: str,
        table_name: str,
    ) -> bool:
        """Rule 3: RI check"""
        orphans = child_df[~child_df[child_key].isin(parent_df[parent_key])]

        passed = len(orphans) == 0
        self.results.append(
            {
                "table_name": table_name,
                "check_name": "referential_integrity",
                "score": len(child_df) - len(orphans),
                "threshold": 100,
                "passed": passed,
                "checked_at": datetime.now(),
            }
        )
        logger.info(f"RI violations: {len(orphans)} orphans {'✅' if passed else '❌'}")
        return passed

    def check_accounting_balance(self, gl_df: pd.DataFrame) -> bool:
        """Rule 4: Double-entry validation"""
        assets = gl_df[gl_df["debit_credit"] == "DR"]["amount"].sum()
        liabilities_equity = gl_df[gl_df["debit_credit"] == "CR"]["amount"].sum()
        diff = abs(assets - liabilities_equity)

        passed = diff < self.rules.get("accounting_tolerance", 0.01)
        self.results.append(
            {
                "table_name": "gl_entries",
                "check_name": "accounting_balance",
                "score": diff,
                "threshold": self.rules.get("accounting_tolerance", 0.01),
                "passed": passed,
                "checked_at": datetime.now(),
            }
        )
        logger.info(f"Accounting balance diff: {diff:.2f} {'✅' if passed else '❌'}")
        return passed

    def run_all_checks(self, datasets: Dict[str, pd.DataFrame]) -> Tuple[float, Dict]:
        """Execute full DQ suite"""
        logger.info("Running Data Quality checks...")

        dq_report: Dict = {"completeness": {}, "bounds_check": {}}

        customers = datasets.get("customers")
        loans = datasets.get("loans")
        gl_entries = datasets.get("gl_entries")

        # Completeness checks
        if customers is not None:
            comp = self._check_completeness(customers, "customer_id")
            dq_report["completeness"]["customers_customer_id"] = comp

        # Loan bounds and PD/LGD checks
        ltv_viol = pd_viol = lgd_viol = 0
        if loans is not None:
            ltv_viol = self._check_ltv_bounds(loans, max_ltv=1.5)
            pd_viol = self._check_pd_range(loans, min_pd=0.001, max_pd=0.99)
            lgd_viol = self._check_lgd_range(loans)
            dq_report["bounds_check"].update(
                {
                    "ltv_violations": ltv_viol,
                    "pd_violations": pd_viol,
                    "lgd_violations": lgd_viol,
                }
            )

        # Accounting balance: handle missing gl_entries gracefully
        if gl_entries is not None:
            self.check_accounting_balance(gl_entries)
            balance_diff = 0.0
        else:
            balance_diff = 0.0
        dq_report["bounds_check"]["accounting_balance_diff"] = balance_diff

        # Calculate score
        score = 1.0
        score -= 0.01 * (ltv_viol + pd_viol + lgd_viol)
        if customers is not None:
            comp_value = dq_report["completeness"].get("customers_customer_id", 1.0)
            score -= 0.01 * (1.0 - comp_value)
        score = max(0.0, min(1.0, score))

        # Also run the original style checks for logging
        for name, df in datasets.items():
            df.name = name
            self.check_completeness(df, name)

        if loans is not None:
            self.check_ltv_bounds(loans)

        # Save results
        import os

        os.makedirs("data/dq_results", exist_ok=True)
        results_df = pd.DataFrame(self.results)
        results_df.to_csv("data/dq_results/dq_report.csv", index=False)

        overall_score = (
            sum(r["passed"] for r in self.results) / len(self.results)
            if self.results
            else score
        )
        logger.info(f"📊 Overall DQ Score: {overall_score:.2%}")

        return float(overall_score), dq_report
