#!/usr/bin/env bash
set -euo pipefail

DUMP_DIR="seeds/data"
DUMP_PATH="${DUMP_DIR}/off.jsonl.gz"

mkdir -p "${DUMP_DIR}"

echo "[OFF] Downloading latest OFF dump…"
curl -L -o "${DUMP_PATH}.tmp" https://static.openfoodfacts.org/data/openfoodfacts-products.jsonl.gz
mv "${DUMP_PATH}.tmp" "${DUMP_PATH}"

echo "[OFF] Streaming import (zero RAM spike)…"
docker compose run --rm api \
  python -m seeds.import_off \
  --file /app/seeds/data/off.jsonl.gz \
  --country UK \
  --limit 0

echo "[OFF] Rebuilding label map…"
docker compose run --rm api python -m tools.build_label_map

echo "[OFF] Vacuum DB…"
docker compose exec -T api sh -lc "python - <<'PY'
import sqlite3
con=sqlite3.connect('data/gains_food.db')
con.execute('VACUUM')
con.close()
print('VACUUM complete')
PY"
