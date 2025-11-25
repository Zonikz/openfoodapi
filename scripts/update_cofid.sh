#!/usr/bin/env bash
set -euo pipefail

echo "[CoFID] Importing…"
docker compose run --rm api python -m seeds.import_cofid

echo "[CoFID] Rebuilding label map…"
docker compose run --rm api python -m tools.build_label_map
