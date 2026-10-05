#!/usr/bin/env bash
# Match the existing CI pytest command and README lint scope.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
.venv/bin/python -m pytest --cov=pyspt --cov-report=term-missing
.venv/bin/python -m ruff check src/ tests/
