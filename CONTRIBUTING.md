# Contributing to OpenReg

Thank you for your interest in contributing to OpenReg!

## Development Environment Setup

```bash
# Clone the repository
git clone https://github.com/TMFNK/openreg.git
cd openreg

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Run the pipeline
python run_pipeline.py

# Run tests
pytest tests/ --tb=short
```

## Project Layout

```
openreg/
├── etl/                  # Extract, Transform, Load modules
│   ├── extract.py        # Synthetic data generation
│   ├── transform.py      # Data cleaning & normalization
│   └── load.py           # Data Vault loading
├── dq/                   # Data quality checks
│   └── dq_checks.py     # DQ engine
├── utils/                # Utilities
│   └── error_handling.py
├── dashboard/            # Streamlit dashboard
│   └── app.py
├── sql/                  # SQL schemas & views
├── tests/                # Test suite
├── config.yaml           # Configuration
└── run_pipeline.py       # Main pipeline
```

## Branching Convention

- `main` - Stable release branch
- `feature/*` - New features
- `fix/*` - Bug fixes
- `refactor/*` - Code improvements

## Pre-commit Checks

Before submitting a PR, run:

```bash
# Format code
black . --line-length=110

# Lint
flake8 . --max-line-length=110 --exclude=.venv,build

# Type check
mypy . --ignore-missing-imports

# Run tests
pytest tests/ --tb=short -v
```

## Commit Message Format

```
type(scope): description

[optional body]

Types:
  - feat: New feature
  - fix: Bug fix
  - docs: Documentation
  - style: Formatting
  - refactor: Code refactoring
  - test: Adding tests
  - chore: Maintenance
```

## Adding New Reports

1. Add SQL view to `sql/` directory
2. Register in `run_pipeline.py` report generation
3. Add tests in `tests/`

## Adding DQ Checks

1. Add check function to `dq/dq_checks.py`
2. Add threshold to `config.yaml` under `dq_thresholds`
3. Add tests

## Docker Development

```bash
# Start PostgreSQL + Redis
docker compose up -d postgresql redis

# Start with pgAdmin (dev profile)
docker compose --profile dev up

# Full stack with monitoring
docker compose --profile monitoring up
```

## PR Checklist

- [ ] Tests pass (`pytest tests/`)
- [ ] No flake8 errors
- [ ] Code formatted with black
- [ ] New tests added for features
- [ ] Documentation updated if needed
- [ ] No hardcoded secrets (use env vars)
