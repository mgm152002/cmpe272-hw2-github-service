#!/usr/bin/env sh
# Team member: Manoj Ganjigatte Manjunatha (@mgm152002)

set -eu
until curl --fail --silent "${BASE_URL:-http://localhost:8000}/healthz" >/dev/null; do
  sleep 1
done
