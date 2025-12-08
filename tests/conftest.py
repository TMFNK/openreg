"""
OpenReg Test Configuration
Shared fixtures and setup for pytest
"""
import pytest
import pandas as pd
import sqlite3
import os
import tempfile
from pathlib import Path

@pytest.fixture
def sample_customer_data():
    """Sample customer data for testing"""
    return pd.DataFrame({
        'customer_id': ['CUST001', 'CUST002', 'CUST003'],
        'customer_type': ['Corporate', 'Retail', 'Corporate'],
        'country': ['DE', 'FR', 'GB'],
        'sector': ['Manufacturing', 'Retail', 'Technology']
    })

@pytest.fixture
def sample_loan_data():
    """Sample loan data for testing"""
    return pd.DataFrame({
        'loan_id': ['LOAN001', 'LOAN002', 'LOAN003'],
        'customer_id': ['CUST001', 'CUST002', 'CUST003'],
        'principal_amount': [100000.0, 50000.0, 75000.0],
        'outstanding_amount': [95000.0, 48000.0, 72000.0],
        'interest_rate': [0.045, 0.035, 0.055],
        'currency': ['EUR', 'EUR', 'GBP'],
        'origination_date': ['2023-01-15', '2023-02-20', '2023-03-10'],
        'maturity_date': ['2028-01-15', '2028-02-20', '2028-03-10'],
        'ltv_ratio': [0.65, 0.55, 0.75],
        'cost_center': ['CC_1001', 'CC_1002', 'CC_1001'],
        'pd_rating': [0.02, 0.015, 0.035],
        'lgd': [0.25, 0.20, 0.35],
        'ead': [95000.0, 48000.0, 72000.0],
        'risk_weight': [0.35, 0.25, 0.50],
        'npl_status': [False, False, True],
        'sector': ['Manufacturing', 'Retail', 'Technology']
    })

@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    # Create temporary file
    temp_fd, temp_path = tempfile.mkstemp(suffix='.db')

    try:
        # Initialize schema
        conn = sqlite3.connect(temp_path)
        schema_path = Path(__file__).parent.parent / 'sql' / 'schema.sql'

        if schema_path.exists():
            with open(schema_path, 'r') as f:
                conn.executescript(f.read())
        conn.close()

        yield temp_path

    finally:
        # Cleanup
        os.close(temp_fd)
        if os.path.exists(temp_path):
            os.unlink(temp_path)

@pytest.fixture
def db_connection(temp_db):
    """Database connection fixture"""
    conn = sqlite3.connect(temp_db)
    yield conn
    conn.close()

@pytest.fixture
def config_data():
    """Sample configuration data"""
    return {
        'database': {
            'type': 'sqlite',
            'sqlite': {
                'path': ':memory:'
            }
        },
        'dq_thresholds': {
            'completeness': 0.98,
            'ltv_max': 1.2,
            'pd_range': [0.001, 0.99],
            'lgd_range': [0.0, 1.0]
        },
        'rls': {
            'controlling_cost_centers': ['CC_1001', 'CC_1002']
        }
    }
