"""
Unit tests for Data Quality Checks
Tests critical business logic for regulatory compliance
"""

import pytest
import pandas as pd
from dq.dq_checks import DataQualityEngine


class TestDataQualityEngine:
    """Test suite for data quality validation"""

    def test_completeness_check_pass(self, sample_customer_data):
        """Test completeness check passes for complete data"""
        dq_engine = DataQualityEngine()
        completeness = dq_engine._check_completeness(
            sample_customer_data, "customer_id"
        )
        assert completeness == 1.0

    def test_completeness_check_fail(self, sample_customer_data):
        """Test completeness check fails for incomplete data"""
        incomplete_data = sample_customer_data.copy()
        incomplete_data.loc[0, "customer_id"] = None

        dq_engine = DataQualityEngine()
        completeness = dq_engine._check_completeness(incomplete_data, "customer_id")

        expected_completeness = 2 / 3  # 2 out of 3 records complete
        assert completeness == pytest.approx(expected_completeness, rel=1e-2)

    def test_ltv_bounds_check_pass(self, sample_loan_data):
        """Test LTV bounds check passes within valid range"""
        dq_engine = DataQualityEngine()
        violations = dq_engine._check_ltv_bounds(sample_loan_data, max_ltv=1.5)
        assert violations == 0

    def test_ltv_bounds_check_fail(self, sample_loan_data):
        """Test LTV bounds check fails when LTV exceeds maximum"""
        high_ltv_data = sample_loan_data.copy()
        high_ltv_data.loc[0, "ltv_ratio"] = 1.8  # Above threshold

        dq_engine = DataQualityEngine()
        violations = dq_engine._check_ltv_bounds(high_ltv_data, max_ltv=1.5)
        assert violations == 1

    def test_pd_rating_range_check(self, sample_loan_data):
        """Test PD rating stays within valid range"""
        dq_engine = DataQualityEngine()
        violations = dq_engine._check_pd_range(
            sample_loan_data, min_pd=0.001, max_pd=0.99
        )
        assert violations == 0

    def test_pd_rating_out_of_range(self, sample_loan_data):
        """Test PD rating range check detects violations"""
        invalid_pd_data = sample_loan_data.copy()
        invalid_pd_data.loc[0, "pd_rating"] = 1.5  # Above maximum

        dq_engine = DataQualityEngine()
        violations = dq_engine._check_pd_range(
            invalid_pd_data, min_pd=0.001, max_pd=0.99
        )
        assert violations == 1

    def test_lgd_range_check(self, sample_loan_data):
        """Test LGD stays within valid range [0,1]"""
        dq_engine = DataQualityEngine()
        violations = dq_engine._check_lgd_range(sample_loan_data)
        assert violations == 0

    def test_lgd_out_of_range(self, sample_loan_data):
        """Test LGD range check detects negative values"""
        invalid_lgd_data = sample_loan_data.copy()
        invalid_lgd_data.loc[0, "lgd"] = -0.1  # Negative value

        dq_engine = DataQualityEngine()
        violations = dq_engine._check_lgd_range(invalid_lgd_data)
        assert violations == 1

    def test_accounting_balance_check(self):
        """Test that accounting balances are maintained"""
        dq_engine = DataQualityEngine()

        # Mock datasets that should balance
        customers = pd.DataFrame({"customer_id": ["C1", "C2"]})
        accounts = pd.DataFrame(
            {"customer_id": ["C1", "C2"], "account_id": ["A1", "A2"]}
        )
        loans = pd.DataFrame({"customer_id": ["C1", "C2"], "loan_id": ["L1", "L2"]})

        balance_diff = dq_engine._check_accounting_balance(customers, accounts, loans)
        assert balance_diff == 0.0

    def test_accounting_balance_imbalance(self):
        """Test detection of accounting imbalances"""
        dq_engine = DataQualityEngine()

        # Create imbalance - more accounts than loans
        customers = pd.DataFrame({"customer_id": ["C1"]})
        accounts = pd.DataFrame(
            {"customer_id": ["C1", "C1"], "account_id": ["A1", "A2"]}
        )
        loans = pd.DataFrame({"customer_id": ["C1"], "loan_id": ["L1"]})

        balance_diff = dq_engine._check_accounting_balance(customers, accounts, loans)
        assert balance_diff == 1.0  # One account without loan

    def test_comprehensive_dq_check_valid_data(
        self, sample_customer_data, sample_loan_data
    ):
        """Test full DQ check pipeline with valid data"""
        dq_engine = DataQualityEngine()

        datasets = {"customers": sample_customer_data, "loans": sample_loan_data}

        overall_score, dq_report = dq_engine.run_all_checks(datasets)

        # Valid data should pass with high score
        assert overall_score >= 0.95
        assert isinstance(dq_report, dict)
        assert "completeness" in dq_report
        assert "bounds_check" in dq_report

    def test_dq_check_with_incomplete_data(self):
        """Test DQ check fails appropriately with incomplete data"""
        dq_engine = DataQualityEngine()

        # Create data with missing values that should trigger DQ failures
        incomplete_customers = pd.DataFrame(
            {
                "customer_id": [None, "C2"],  # Missing customer_id
                "customer_type": ["Retail", "Corporate"],
                "sector": ["Retail", "Tech"],
            }
        )

        invalid_loans = pd.DataFrame(
            {
                "loan_id": ["L1", "L2"],
                "pd_rating": [1.5, 0.02],  # PD > 1 (invalid)
                "lgd": [0.3, -0.1],  # Negative LGD (invalid)
                "ltv_ratio": [1.5, 0.6],  # LTV > max allowed
            }
        )

        datasets = {"customers": incomplete_customers, "loans": invalid_loans}

        overall_score, dq_report = dq_engine.run_all_checks(datasets)

        # Should fail DQ checks
        assert overall_score < 0.95
        assert dq_report["completeness"]["customers_customer_id"] < 1.0

    @pytest.mark.parametrize(
        "threshold,target_score", [(0.98, 0.98), (0.95, 0.95), (0.99, 0.99)]
    )
    def test_configurable_completeness_thresholds(self, threshold, target_score):
        """Test that completeness thresholds are configurable"""
        dq_engine = DataQualityEngine(completeness_threshold=threshold)

        # Create data with exactly the threshold completeness
        n_complete = int(100 * threshold)
        n_total = 100

        test_data = pd.DataFrame(
            {
                "test_id": [f"ID{i}" for i in range(n_complete)]
                + [None] * (n_total - n_complete)
            }
        )

        completeness = dq_engine._check_completeness(test_data, "test_id")
        assert completeness == pytest.approx(target_score, rel=1e-2)


class TestRegulatoryCalculations:
    """Test regulatory calculation functions"""

    def test_risk_weight_calculation(self, sample_loan_data):
        """Test that risk weights are calculated correctly"""
        # Risk weight should be within expected bounds [0,1]
        assert all(0 <= rw <= 1 for rw in sample_loan_data["risk_weight"])

    def test_ead_calculation(self, sample_loan_data):
        """Test EAD (Exposure at Default) calculations"""
        # EAD should be close to outstanding amount for retail loans
        ead_values = sample_loan_data["ead"]
        outstanding_values = sample_loan_data["outstanding_amount"]

        # EAD should typically be >= outstanding amount
        assert all(
            ead >= outstanding
            for ead, outstanding in zip(ead_values, outstanding_values)
        )

    def test_pd_lgd_el_relationship(self, sample_loan_data):
        """Test relationship between PD, LGD, and Expected Loss"""
        # Expected Loss (EL) = PD * LGD * EAD
        # This is fundamental to regulatory calculations

        expected_el = (
            sample_loan_data["pd_rating"]
            * sample_loan_data["lgd"]
            * sample_loan_data["ead"]
        )

        # All expected loss values should be non-negative
        assert all(el >= 0 for el in expected_el)

        # Expected loss should be significant but not exceed EAD
        assert all(el <= ead for el, ead in zip(expected_el, sample_loan_data["ead"]))
