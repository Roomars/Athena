#!/usr/bin/env bash
# One-click dev environment startup.
# Avvia backend, frontend e monitoring in parallelo.
# Verifica che la UI risponda (Status 200) prima di segnalare "pronto".
#
# Adatta le sezioni BACKEND / FRONTEND / MONITOR al tuo stack.

set -uo pipefail

BASEDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_FILE="$BASEDIR/orchestration/state.json"
TIMEOUT=30

log() { echo "[$(date '+%H:%M:%S')] $1"; }
err() { echo "[$(date '+%H:%M:%S')] ERROR: $1" >&2; }

update_state() {
  if command -v python3 &>/dev/null && [ -f "$STATE_FILE" ]; then
    python3 -c "
import json, sys
with open('$STATE_FILE') as f: s = json.load(f)
s['environment']['dev_server_running'] = $1
s['environment']['dev_server_url'] = '$2'
with open('$STATE_FILE', 'w') as f: json.dump(s, f, indent=2)
" 2>/dev/null || true
  fi
}

cleanup() {
  log "Shutdown in corso..."
  update_state false ""
  kill 0 2>/dev/null
}
trap cleanup EXIT INT TERM

echo ""
echo "=== Dev Environment Startup — $(date '+%d-%m-%Y %H:%M') ==="
echo ""

# --- BACKEND: adatta al tuo stack ---
start_backend() {
  if [ -f "package.json" ] && grep -q '"start"' package.json 2>/dev/null; then
    log "Avvio backend (Node.js)..."
    npm start &
    BACKEND_PID=$!
  elif [ -f "manage.py" ]; then
    log "Avvio backend (Django)..."
    python3 manage.py runserver &
    BACKEND_PID=$!
  elif [ -f "main.py" ] || [ -f "app.py" ]; then
    log "Avvio backend (FastAPI/Flask)..."
    python3 -m uvicorn main:app --reload 2>/dev/null || python3 app.py &
    BACKEND_PID=$!
  else
    log "Nessun backend rilevato — skip."
    BACKEND_PID=""
  fi
}

# --- FRONTEND: adatta al tuo stack ---
start_frontend() {
  if [ -f "package.json" ] && grep -q '"dev"' package.json 2>/dev/null; then
    log "Avvio frontend (npm run dev)..."
    npm run dev &
    FRONTEND_PID=$!
    FRONTEND_URL="http://localhost:3000"
  else
    log "Nessun frontend rilevato — skip."
    FRONTEND_PID=""
    FRONTEND_URL=""
  fi
}

start_backend
start_frontend

# --- Attendi che i server siano pronti ---
MAIN_URL="${FRONTEND_URL:-http://localhost:3000}"
log "Attesa avvio server su $MAIN_URL (max ${TIMEOUT}s)..."

ELAPSED=0
HTTP_STATUS=0
while [ "$ELAPSED" -lt "$TIMEOUT" ]; do
  if command -v curl &>/dev/null; then
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$MAIN_URL" 2>/dev/null || echo "0")
  fi
  [ "$HTTP_STATUS" = "200" ] && break
  sleep 2
  ELAPSED=$((ELAPSED + 2))
done

echo ""
if [ "$HTTP_STATUS" = "200" ]; then
  log "Server PRONTO — $MAIN_URL risponde con Status 200"
  update_state true "$MAIN_URL"
  echo ""
  echo "=== Ambiente di sviluppo attivo ==="
  echo "  URL: $MAIN_URL"
  echo "  Premi Ctrl+C per fermare tutti i processi."
  echo ""
  wait
else
  err "Server non ha risposto entro ${TIMEOUT}s (ultimo status: ${HTTP_STATUS:-timeout})"
  update_state false ""
  exit 1
fi
