# OpenReg Architecture

## Design Principles

1. **Auditability**: Every data point has `load_datetime` and `record_source`
2. **Immutability**: Data Vault satellites never update, only insert
3. **Reproducibility**: `run_id` tracks every ETL execution
4. **Compliance**: RLS enforced at database view layer
5. **Quality**: DQ gates prevent bad data from loading
6. **Security**: bcrypt password hashing, role-based access control, session management
7. **Reliability**: Structured logging, retry mechanisms, enterprise-grade error handling
8. **Scalability**: Support for SQLite (development) and PostgreSQL (production)

## Component Flow

1. **Synthetic Generator**: Creates GDPR-safe data with realistic distributions
2. **Data Transformer**: Applies business rules and hash diffs
3. **DQ Engine**: 4 checks (completeness, bounds, RI, accounting)
4. **Data Vault Loader**: Append-only loading to SQLite or PostgreSQL databases
5. **Reporting Layer**: SQL views decouple consumption from storage
6. **Authentication Layer**: Secure login/logout with role verification
7. **Dashboard**: Streamlit app with protected access and role-based views

## Infrastructure

### Development Environment

- **Database**: SQLite via Python sqlite3
- **Configuration**: YAML-based settings with validation
- **Testing**: Comprehensive unit test suite with pytest

### Production Environment

- **Database**: PostgreSQL 15 with Docker Compose
- **Caching**: Redis layer for performance optimization
- **Monitoring**: Prometheus/Grafana stack for metrics and alerting
- **Administration**: pgAdmin web interface for database management
- **Deployment**: Docker Compose with backup and recovery procedures

## Security & Reliability

### Security Features

- **Authentication**: bcrypt password hashing with salt
- **Session Management**: Secure password verification and logout
- **Authorization**: Three-tier role-based access control
  - Regulator: Full access to all regulatory views
  - Controller: Access to FINREP and Controlling reports
  - Risk Officer: Limited to risk management views
- **Data Protection**: Input validation, sanitization, timing attack prevention

### Reliability Features

- **Error Handling**: Custom exception classes, retry with exponential backoff
- **Logging**: Structured logging with structlog and JSON formatting
- **Monitoring**: Performance metrics, configuration validation
- **Consistency**: Hash-based business keys, temporal data management, referential integrity
