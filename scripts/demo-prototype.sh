#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m intention_commerce.cli --scenario success
python3 -m intention_commerce.cli --scenario insufficient
python3 -m intention_commerce.cli --scenario timeout
