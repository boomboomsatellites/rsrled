#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
sudo -E python3 -m src.main --output rgb_matrix --frames 1000 --sleep 0.05
