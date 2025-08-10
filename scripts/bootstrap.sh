#!/usr/bin/env bash
set -euo pipefail
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
if [ ! -f .env ]; then
  cp .env.example .env
fi
pre-commit install
