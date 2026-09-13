#!/usr/bin/env sh
# Team member: Manoj Ganjigatte Manjunatha (@mgm152002)

set -eu
python_bin="${PYTHON:-python3}"
"${python_bin}" -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
