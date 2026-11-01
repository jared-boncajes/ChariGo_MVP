#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/flask --app app:create_app init-db
.venv/bin/flask --app app:create_app seed
