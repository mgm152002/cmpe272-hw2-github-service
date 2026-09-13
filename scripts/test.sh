#!/usr/bin/env sh
# Team member: Manoj Ganjigatte Manjunatha (@mgm152002)

set -eu
python_bin="${PYTHON:-python3}"
"${python_bin}" -m pytest
