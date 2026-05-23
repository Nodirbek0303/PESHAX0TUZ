#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="$ROOT/backend/app/data"

echo "SmartCross AI - ma'lumotlarni nolga tushirish..."
mkdir -p "$DATA_DIR"
echo '{"cameras": []}' > "$DATA_DIR/camera_registry.json"
echo '{"entries": []}' > "$DATA_DIR/location_catalog.json"
echo "OK: camera_registry.json va location_catalog.json nolga tushirildi."
