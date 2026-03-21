# Security & Row-Level Security

## Overview

This document details the security architecture and row-level security (RLS) implementation in the OpenReg platform, designed to comply with banking regulatory requirements while enabling appropriate data access for different user roles.

## Security Principles

### Data Classification

The platform implements a three-tier data classification system:

- **Public**: Aggregated KPIs, anonymized statistics
- **Internal**: Customer-level data, transaction details
- **Restricted**: Sensitive PII, regulatory reports

## Enhanced Security Implementation

### Authentication System

- **Password Hashing**: bcrypt with salt for secure credential storage
- **Session Management**: Secure login/logout with session verification
- **Dashboard Protection**: Streamlit app requires authentication to prevent unauthorized access
- **Timing Attack Prevention**: Secure password comparison to avoid timing-based attacks
- **Password Complexity**: Guidelines for secure password requirements

### Role-Based Access Control (RBAC)

Implemented with three distinct user roles:

- **Regulator**: Full access to FINREP, COREP, Controlling, and Risk views
- **Controller**: Access to FINREP and Controlling views
- **Risk Officer**: Access only to Risk management views

### Additional Security Features

- **Input Validation and Sanitization**: Prevents injection attacks and malformed data
- **Configuration Validation**: Required parameters checked for security compliance
- **Audit Logging and User Access Tracking**: Row-level security policies in PostgreSQL
- **Production Monitoring**: Alerts for security violations and unusual patterns

### Authentication Framework

- **Multi-factor Authentication (MFA)**: Available for enhanced security (future implementation)
- **Role-Based Access Control (RBAC)**: Implemented with enforced business functions
- **Audit Logging**: All access attempts logged with user tracking

## Row-Level Security Architecture

### Role Definitions

The platform implements three primary user roles with corresponding data access levels:

#### 1. Regulator Role

**Purpose**: External regulatory oversight and compliance monitoring
**Access Level**: Complete read access to all data
**Data Scope**: All tables, views, and historical data

```sql
-- Create regulator view with full access
CREATE VIEW v_loans_regulator AS
SELECT * FROM dv.h_loan
JOIN dv.s_loan_customer ON dv.h_loan.hk_loan = dv.s_loan_customer.hk_loan
JOIN dv.s_loan_financial ON dv.h_loan.hk_loan = dv.s_loan_financial.hk_loan;
```

#### 2. Controlling Role

**Purpose**: Internal financial controlling and management accounting
**Access Level**: Read access to anonymized customer data
**Data Scope**: CC_1001-1003 cost centers only

```sql
-- Create controlling view with filtered access
CREATE VIEW v_loans_controlling AS
SELECT
    loan_id,
    cost_center,
    CASE
        WHEN cost_center IN ('CC_1001', 'CC_1002', 'CC_1003')
        THEN customer_name -- Show real names for allowed cost centers
        ELSE 'ANONYMIZED'  -- Hide names for other cost centers
    END as customer_name_masked,
    balance,
    interest_rate
FROM v_loans_full
WHERE cost_center IN ('CC_1001', 'CC_1002', 'CC_1003');
```

#### 3. Risk Role

**Purpose**: Credit risk analysis and portfolio management
**Access Level**: Read access to aggregated statistical data
**Data Scope**: Anonymized statistical summaries only

```sql
-- Create risk view with statistical aggregation
CREATE VIEW v_loans_risk AS
SELECT
    sector,
    risk_rating,
    COUNT(*) as loan_count,
    ROUND(AVG(balance), 2) as avg_balance,
    ROUND(AVG(interest_rate), 3) as avg_rate,
    ROUND(STDDEV(balance), 2) as balance_stddev
FROM v_loans_full
GROUP BY sector, risk_rating;
```

## Security Implementation

### Data Masking & Anonymization

#### Dynamic Data Masking

Sensitive fields are masked based on user role:

```python
# Example data masking function
def mask_customer_data(df, role):
    if role == 'regulator':
        return df  # Full access

    elif role == 'controlling':
        # Mask PII but keep business-relevant data
        df['customer_name'] = df['customer_name'].apply(mask_name)
        df['customer_id'] = df['customer_id'].apply(hash_id)
        return df.loc[df['cost_center'].isin(['CC_1001', 'CC_1002', 'CC_1003'])]

    elif role == 'risk':
        # Return aggregated statistical data only
        return df.groupby(['sector', 'risk_rating']).agg({
            'balance': ['count', 'mean', 'std'],
            'interest_rate': 'mean'
        })
```

#### Tokenization

High-sensitivity data fields use format-preserving tokenization:

- Customer IDs → Hashed equivalents
- Account numbers → Format-masked versions
- PII fields → Irreversible anonymization

### Encryption Standards

#### At-Rest Encryption

- **Database**: AES-256 encryption for SQLite database files
- **Backups**: Encrypted using industry-standard algorithms
- **Logs**: Sensitive portions encrypted before storage

#### In-Transit Encryption

- **API Communications**: TLS 1.3 encryption
- **Database Connections**: Encrypted pipelines
- **File Transfers**: SFTP/SCP with key authentication

### Access Control Lists (ACLs)

#### File System Level

```yaml
# config.yaml ACL example
security:
  file_permissions:
    reports:
      regulator: read
      controlling: read
      risk: read
    dashboard:
      regulator: read
      controlling: read/write
      risk: read
    config:
      regulator: none
      controlling: none
      risk: none
```

### Audit & Compliance

#### Audit Logging

All data access is tracked in the `etl_audit_log` table:

```sql
-- Audit log structure
CREATE TABLE etl_audit_log (
    timestamp TIMESTAMP,
    user_id VARCHAR(50),
    user_role VARCHAR(20),
    operation VARCHAR(10), -- SELECT, INSERT, UPDATE, DELETE
    table_name VARCHAR(100),
    record_count INTEGER,
    query_hash VARCHAR(64), -- For detecting unusual patterns
    ip_address VARCHAR(45),
    session_id VARCHAR(64)
);
```

#### Compliance Features

- **GDPR Compliance**: Data retention policies and right to erasure
- **SOX Compliance**: Segregation of duties and audit trails
- **Basel III**: Appropriate risk-based access controls

### Security Monitoring

#### Intrusion Detection

- **Query Anomaly Detection**: Machine learning models flag unusual query patterns
- **Access Pattern Analysis**: Automated alerts for policy violations
- **DDOS Protection**: Rate limiting on API endpoints

#### Security Dashboards

The Streamlit dashboard includes security monitoring:

- Failed login attempts
- Unusual data access patterns
- Role-based usage statistics
- Compliance violation alerts

## Data Breach Response

### Incident Response Plan

1. **Detection**: Automated monitoring alerts security team
2. **Assessment**: Determine scope and impact of breach
3. **Containment**: Shut down affected systems, isolate data
4. **Recovery**: Restore from secure backups
5. **Notification**: Regulatory reporting and stakeholder communication

### Data Backup Strategy

- **Daily Full Backups**: Encrypted off-site storage
- **Point-in-Time Recovery**: 15-minute granularity for critical data
- **Immutable Backups**: Ransomware protection through versioning

## Implementation Notes

### Performance Considerations

- RLS views use indexed columns to minimize performance impact
- Cached role evaluations to reduce computation overhead
- Connection pooling for efficient database access

### Testing & Validation

- Automated security testing in CI/CD pipeline
- Penetration testing quarterly
- Security awareness training for development team

### Future Enhancements

- **Multi-cloud Encryption**: Hybrid key management
- **AI-Powered Anomaly Detection**: Advanced threat detection
- **Zero-Knowledge Proofs**: Privacy-preserving analytics
