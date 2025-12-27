#!/bin/bash
# sinov tick を定期実行するスクリプト

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."
.venv/bin/sinov tick >> logs/cron.log 2>&1
