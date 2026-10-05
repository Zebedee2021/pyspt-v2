#!/usr/bin/env bash
# Run from any directory; use an isolated environment and existing dev extras.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pip check
