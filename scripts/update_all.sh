#!/usr/bin/env bash
set -euo pipefail
bash scripts/update_off.sh
# Uncomment below if you want periodic CoFID refreshes as well:
# bash scripts/update_cofid.sh

echo "[ALL] Health:"
curl -s http://localhost:8000/api/health || true
