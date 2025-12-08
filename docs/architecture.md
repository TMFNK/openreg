# OpenReg Architecture

## Design Principles

1. **Auditability**: Every data point has `load_datetime` and `record_source`
2. **Immutability**: Data Vault satellites never update, only insert
3. **Reproducibility**: `run_id` tracks every ETL execution
4. **Compliance**: RLS enforced at database view layer
5. **Quality**: DQ gates prevent bad data from loading

## Component Flow

1. **Synthetic Generator**: Creates GDPR-safe data with realistic distributions
2. **Data Transformer**: Applies business rules and hash diffs
3. **DQ Engine**: 4 checks (completeness, bounds, RI, accounting)
4. **Data Vault Loader**: Append-only loading to SQLite
5. **Reporting Layer**: SQL views decouple consumption from storage
