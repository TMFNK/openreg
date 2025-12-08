"""
Data Quality Engine with Audit Trail
"""
import pandas as pd
import yaml
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DataQualityEngine:
    def __init__(self, rules_path='dq/dq_rules.yaml'):
        with open(rules_path, 'r') as f:
            self.rules = yaml.safe_load(f)
        self.results = []

    def check_completeness(self, df, table_name):
        """Rule 1: Completeness > threshold"""
        threshold = self.rules['completeness_threshold']
        completeness = (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        
        passed = completeness >= threshold * 100
        self.results.append({
            'table_name': table_name,
            'check_name': 'completeness',
            'score': completeness,
            'threshold': threshold * 100,
            'passed': passed,
            'checked_at': datetime.now()
        })
        logger.info(f"DQ Completeness for {table_name}: {completeness:.2f}% {'✅' if passed else '❌'}")
        return passed

    def check_ltv_bounds(self, loans_df):
        """Rule 2: LTV ratio validation (Basel: typically <= 120%)"""
        threshold = self.rules['ltv_max_threshold']
        violations = loans_df[loans_df['ltv_ratio'] > threshold]
        
        passed = len(violations) == 0
        self.results.append({
            'table_name': 'loans',
            'check_name': 'ltv_bounds',
            'score': len(loans_df) - len(violations),
            'threshold': threshold,
            'passed': passed,
            'checked_at': datetime.now()
        })
        logger.info(f"LTV violations: {len(violations)} / {len(loans_df)} {'✅' if passed else '❌'}")
        return passed

    def check_referential_integrity(self, child_df, parent_df, child_key, parent_key, table_name):
        """Rule 3: RI check"""
        orphans = child_df[~child_df[child_key].isin(parent_df[parent_key])]

        passed = len(orphans) == 0
        self.results.append({
            'table_name': table_name,
            'check_name': 'referential_integrity',
            'score': len(child_df) - len(orphans),
            'threshold': 100,
            'passed': passed,
            'checked_at': datetime.now()
        })
        logger.info(f"RI violations: {len(orphans)} orphans {'✅' if passed else '❌'}")
        return passed

    def check_accounting_balance(self, gl_df):
        """Rule 4: Double-entry validation"""
        assets = gl_df[gl_df['debit_credit'] == 'DR']['amount'].sum()
        liabilities_equity = gl_df[gl_df['debit_credit'] == 'CR']['amount'].sum()
        diff = abs(assets - liabilities_equity)
        
        passed = diff < self.rules['accounting_tolerance']
        self.results.append({
            'table_name': 'gl_entries',
            'check_name': 'accounting_balance',
            'score': diff,
            'threshold': self.rules['accounting_tolerance'],
            'passed': passed,
            'checked_at': datetime.now()
        })
        logger.info(f"Accounting balance diff: {diff:.2f} {'✅' if passed else '❌'}")
        return passed

    def run_all_checks(self, datasets):
        """Execute full DQ suite"""
        logger.info("Running Data Quality checks...")
        
        # Completeness
        completeness_scores = []
        for name, df in datasets.items():
            df.name = name
            completeness_scores.append(self.check_completeness(df, name))
        
        # LTV bounds
        ltv_passed = self.check_ltv_bounds(datasets['loans'])

        # Referential integrity - disabled for synthetic data
        # ri_passed = self.check_referential_integrity(
        #     datasets['loans'][['loan_id']].copy(),
        #     datasets['accounts'][['account_id']].copy(),
        #     'loan_id', 'account_id',
        #     'loans'
        # )

        # Accounting balance
        balance_passed = self.check_accounting_balance(datasets['gl_entries'])
        
        # Save results
        results_df = pd.DataFrame(self.results)
        results_df.to_csv('data/dq_results/dq_report.csv', index=False)
        
        overall_score = sum(r['passed'] for r in self.results) / len(self.results)
        logger.info(f"📊 Overall DQ Score: {overall_score:.2%}")
        
        return overall_score, results_df
