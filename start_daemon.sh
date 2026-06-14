#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
exec .venv/bin/uvicorn brain.main:app --host 127.0.0.1 --port 8765 --log-level warning
