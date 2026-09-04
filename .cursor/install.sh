#!/usr/bin/env bash
# Idempotent Cloud Agent setup for the Plan-1 trading agent.
# Creates an isolated virtualenv (.venv, already gitignored) and installs the
# pinned runtime dependencies plus pytest for the test suite.
set -euo pipefail

# python3 venv support is not guaranteed in every base image; install it once.
if ! python3 -c "import venv, ensurepip" >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq python3-venv
fi

if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt pytest
