-- =============================================
-- POSTGRESQL SCHEMA - OpenReg Platform
-- Suitable for Enterprise Banking Use
-- =============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================
-- HUB TABLES (Data Vault 2.0)
-- =============================================

-- Customer Hub
CREATE TABLE IF NOT EXISTS hub_customer (
    customer_hash VARCHAR(64) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL UNIQUE,
    load_datetime TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    record_source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Account Hub
CREATE TABLE IF NOT EXISTS hub_account (
    account_hash VARCHAR(64) PRIMARY KEY,
    account_id VARCHAR(50) NOT NULL UNIQUE,
    load_datetime TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    record_source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Loan Hub
CREATE TABLE IF NOT EXISTS hub_loan (
    loan_hash VARCHAR(64) PRIMARY KEY,
    loan_id VARCHAR(50) NOT NULL UNIQUE,
    load_datetime TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    record_source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- GL Entries Hub
CREATE TABLE IF NOT EXISTS hub_gl_entries (
    gl_entry_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entry_date DATE NOT NULL,
    account VARCHAR(50) NOT NULL,
    debit_credit VARCHAR(2) CHECK (debit_credit IN ('DR', 'CR')),
    amount DECIMAL(18,2) NOT NULL,
    cost_center VARCHAR(20),
    load_datetime TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    record_source VARCHAR(50) DEFAULT 'GL_SYSTEM'
);

-- =============================================
-- LINK TABLES
-- =============================================

-- Customer-Account Links
CREATE TABLE IF NOT EXISTS link_customer_account (
    link_hash VARCHAR(64) PRIMARY KEY,
    customer_hash VARCHAR(64) REFERENCES hub_customer(customer_hash),
    account_hash VARCHAR(64) REFERENCES hub_account(account_hash),
    load_datetime TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    record_source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Account-Loan Links
CREATE TABLE IF NOT EXISTS link_account_loan (
    link_hash VARCHAR(64) PRIMARY KEY,
    account_hash VARCHAR(64) REFERENCES hub_account(account_hash),
    loan_hash VARCHAR(64) REFERENCES hub_loan(loan_hash),
    load_datetime TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    record_source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- SATELLITE TABLES
-- =============================================

-- Customer Details Satellite
CREATE TABLE IF NOT EXISTS sat_customer_details (
    customer_hash VARCHAR(64) REFERENCES hub_customer(customer_hash),
    load_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    record_source VARCHAR(50) NOT NULL,
    hash_diff VARCHAR(64) NOT NULL,
    customer_id VARCHAR(50),
    customer_type VARCHAR(20),
    country VARCHAR(2),
    sector VARCHAR(50),
    customer_rating VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (customer_hash, load_datetime)
);

-- Account Details Satellite
CREATE TABLE IF NOT EXISTS sat_account_details (
    account_hash VARCHAR(64) REFERENCES hub_account(account_hash),
    load_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    record_source VARCHAR(50) NOT NULL,
    hash_diff VARCHAR(64) NOT NULL,
    account_id VARCHAR(50),
    account_type VARCHAR(20),
    currency VARCHAR(3) DEFAULT 'EUR',
    opening_date DATE,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (account_hash, load_datetime)
);

-- Loan Details Satellite
CREATE TABLE IF NOT EXISTS sat_loan_details (
    loan_hash VARCHAR(64) REFERENCES hub_loan(loan_hash),
    load_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    record_source VARCHAR(50) NOT NULL,
    hash_diff VARCHAR(64) NOT NULL,
    loan_id VARCHAR(50),
    principal_amount DECIMAL(18,2),
    outstanding_amount DECIMAL(18,2),
    interest_rate DECIMAL(5,4),
    currency VARCHAR(3) DEFAULT 'EUR',
    origination_date DATE,
    maturity_date DATE,
    ltv_ratio DECIMAL(5,4),
    cost_center VARCHAR(20),
    pd_rating DECIMAL(5,4),
    lgd DECIMAL(5,4),
    ead DECIMAL(18,2),
    risk_weight DECIMAL(5,4),
    npl_status BOOLEAN DEFAULT FALSE,
    sector VARCHAR(50),
    last_payment_date DATE,
    next_payment_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (loan_hash, load_datetime)
);

-- Collateral Satellite
CREATE TABLE IF NOT EXISTS sat_collateral (
    loan_hash VARCHAR(64) REFERENCES hub_loan(loan_hash),
    load_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    record_source VARCHAR(50) NOT NULL,
    collateral_type VARCHAR(50),
    market_value DECIMAL(18,2),
    haircut DECIMAL(5,4),
    valuation_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (loan_hash, load_datetime)
);

-- Payment History Satellite
CREATE TABLE IF NOT EXISTS sat_payment_history (
    loan_hash VARCHAR(64) REFERENCES hub_loan(loan_hash),
    payment_date DATE NOT NULL,
    amount DECIMAL(18,2) NOT NULL,
    payment_type VARCHAR(20),
    load_datetime TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (loan_hash, payment_date)
);

-- =============================================
-- AUDIT & LOGGING TABLES
-- =============================================

-- ETL Audit Log
CREATE TABLE IF NOT EXISTS etl_audit_log (
    run_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    process_name VARCHAR(100) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'RUNNING',
    records_processed INTEGER DEFAULT 0,
    error_message TEXT,
    duration_seconds INTEGER GENERATED ALWAYS AS
        (EXTRACT(EPOCH FROM (end_time - start_time))) STORED,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User Access Audit Log
CREATE TABLE IF NOT EXISTS user_access_audit (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(200),
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Data Quality Audit Log
CREATE TABLE IF NOT EXISTS dq_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    check_name VARCHAR(100) NOT NULL,
    check_type VARCHAR(50) NOT NULL,
    threshold DECIMAL(5,4),
    actual_value DECIMAL(10,4),
    status VARCHAR(20),
    details JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- SECURITY TABLES
-- =============================================

-- User Management
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User Sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id VARCHAR(100) PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- =============================================
-- INDEXES FOR PERFORMANCE
-- =============================================

-- Hash indexes for Data Vault lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_hub_customer_customer_id ON hub_customer(customer_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_hub_account_account_id ON hub_account(account_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_hub_loan_loan_id ON hub_loan(loan_id);

-- Temporal indexes for satellites
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sat_customer_load_datetime ON sat_customer_details(load_datetime);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sat_loan_load_datetime ON sat_loan_details(load_datetime);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sat_collateral_load_datetime ON sat_collateral(load_datetime);

-- Business logic indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sat_loan_sector ON sat_loan_details(sector);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sat_loan_cost_center ON sat_loan_details(cost_center);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sat_loan_npl_status ON sat_loan_details(npl_status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sat_loan_origination_date ON sat_loan_details(origination_date);

-- Audit log indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_etl_audit_start_time ON etl_audit_log(start_time);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_etl_audit_status ON etl_audit_log(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_access_timestamp ON user_access_audit(timestamp);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dq_audit_timestamp ON dq_audit_log(timestamp);

-- =============================================
-- ROW LEVEL SECURITY POLICIES
-- =============================================

-- Enable RLS
ALTER TABLE sat_customer_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE sat_account_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE sat_loan_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE sat_collateral ENABLE ROW LEVEL SECURITY;
ALTER TABLE hub_gl_entries ENABLE ROW LEVEL SECURITY;

-- Create security policies (will be applied by application based on user role)

-- =============================================
-- VIEWS (Maintained for backward compatibility)
-- =============================================

-- Note: Views are created by application code to allow for dynamic RLS policies

-- =============================================
-- FUNCTIONS & TRIGGERS
-- =============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers for updated_at maintenance
CREATE TRIGGER update_hub_customer_updated_at
    BEFORE UPDATE ON hub_customer
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_hub_account_updated_at
    BEFORE UPDATE ON hub_account
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_hub_loan_updated_at
    BEFORE UPDATE ON hub_loan
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- PARTITIONING (For large tables - optional)
-- =============================================

-- Example: Partition hub_gl_entries by month (uncomment when needed)
-- CREATE TABLE hub_gl_entries_y2024m01 PARTITION OF hub_gl_entries
--     FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- =============================================
-- CONSTRAINTS & VALIDATIONS
-- =============================================

-- Ensure loan amounts are positive
ALTER TABLE sat_loan_details
ADD CONSTRAINT chk_positive_principal CHECK (principal_amount > 0);

ALTER TABLE sat_loan_details
ADD CONSTRAINT chk_positive_outstanding CHECK (outstanding_amount >= 0);

-- Ensure dates make sense
ALTER TABLE sat_loan_details
ADD CONSTRAINT chk_maturity_after_origination CHECK (maturity_date >= origination_date);

-- Ensure ratings are valid
ALTER TABLE sat_loan_details
ADD CONSTRAINT chk_pd_valid_range CHECK (pd_rating >= 0 AND pd_rating <= 1);

ALTER TABLE sat_loan_details
ADD CONSTRAINT chk_lgd_valid_range CHECK (lgd >= 0 AND lgd <= 1);
