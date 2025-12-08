-- =============================================
-- DATA VAULT 2.0 SCHEMA - OpenReg Platform
-- =============================================

-- HUBS
CREATE TABLE IF NOT EXISTS hub_customer (
    customer_hash VARCHAR(32) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    load_datetime TIMESTAMP NOT NULL,
    record_source VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS hub_account (
    account_hash VARCHAR(32) PRIMARY KEY,
    account_id VARCHAR(50) NOT NULL,
    load_datetime TIMESTAMP NOT NULL,
    record_source VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS hub_loan (
    loan_hash VARCHAR(32) PRIMARY KEY,
    loan_id VARCHAR(50) NOT NULL,
    load_datetime TIMESTAMP NOT NULL,
    record_source VARCHAR(50) NOT NULL
);

-- LINKS
CREATE TABLE IF NOT EXISTS link_customer_account (
    link_hash VARCHAR(32) PRIMARY KEY,
    customer_hash VARCHAR(32) REFERENCES hub_customer(customer_hash),
    account_hash VARCHAR(32) REFERENCES hub_account(account_hash),
    load_datetime TIMESTAMP NOT NULL,
    record_source VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS link_account_loan (
    link_hash VARCHAR(32) PRIMARY KEY,
    account_hash VARCHAR(32) REFERENCES hub_account(account_hash),
    loan_hash VARCHAR(32) REFERENCES hub_loan(loan_hash),
    load_datetime TIMESTAMP NOT NULL,
    record_source VARCHAR(50) NOT NULL
);

-- SATELLITES
CREATE TABLE IF NOT EXISTS sat_customer_details (
    customer_hash VARCHAR(32) REFERENCES hub_customer(customer_hash),
    load_datetime TIMESTAMP NOT NULL,
    record_source VARCHAR(50) NOT NULL,
    hash_diff VARCHAR(32) NOT NULL,
    customer_id VARCHAR(50),
    customer_type VARCHAR(20),
    country VARCHAR(2),
    sector VARCHAR(50),
    PRIMARY KEY (customer_hash, load_datetime)
);

CREATE TABLE IF NOT EXISTS sat_loan_details (
    loan_hash VARCHAR(32) REFERENCES hub_loan(loan_hash),
    load_datetime TIMESTAMP NOT NULL,
    record_source VARCHAR(50) NOT NULL,
    hash_diff VARCHAR(32) NOT NULL,
    loan_id VARCHAR(50),
    principal_amount DECIMAL(18,2),
    outstanding_amount DECIMAL(18,2),
    interest_rate DECIMAL(5,4),
    currency VARCHAR(3),
    origination_date DATE,
    maturity_date DATE,
    ltv_ratio DECIMAL(5,4),
    cost_center VARCHAR(20),
    pd_rating DECIMAL(5,4),
    lgd DECIMAL(5,4),
    ead DECIMAL(18,2),
    risk_weight DECIMAL(5,4),
    npl_status BOOLEAN,
    sector VARCHAR(50),
    PRIMARY KEY (loan_hash, load_datetime)
);

CREATE TABLE IF NOT EXISTS sat_collateral (
    loan_hash VARCHAR(32) REFERENCES hub_loan(loan_hash),
    load_datetime TIMESTAMP NOT NULL,
    record_source VARCHAR(50) NOT NULL,
    collateral_type VARCHAR(50),
    market_value DECIMAL(18,2),
    haircut DECIMAL(5,4),
    PRIMARY KEY (loan_hash, load_datetime)
);

-- GL Entries for auditability
CREATE TABLE IF NOT EXISTS hub_gl_entries (
    gl_entry_id VARCHAR(64) PRIMARY KEY,
    entry_date DATE NOT NULL,
    account VARCHAR(50) NOT NULL,
    debit_credit VARCHAR(2) CHECK (debit_credit IN ('DR', 'CR')),
    amount DECIMAL(18,2) NOT NULL,
    cost_center VARCHAR(20)
);

-- Audit log table
CREATE TABLE IF NOT EXISTS etl_audit_log (
    run_id VARCHAR(36),
    process_name VARCHAR(50),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(20),
    records_processed INTEGER,
    error_message TEXT,
    PRIMARY KEY (run_id, process_name)
);
