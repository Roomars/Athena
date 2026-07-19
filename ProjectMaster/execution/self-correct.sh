#!/usr/bin/env bash
# Self-Correction Loop — primitiva CLI per retry autonomo.
#
# Uso: ./execution/self-correct.sh "<comando test>" "<agente>" "<task-slug>"
#
# Esegue il comando, cattura l'output, corregge in loop fino a MAX_RETRIES.
# Se tutti i tentativi falliscono, genera un report in /diagnostics.
# Exit 0 = successo entro i retry. Exit 1 = blocco, report generato.

set -uo pipefail

BASEDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_CMD="${1:-}"
AGENT="${2:-unknown}"
TASK_SLUG="${3:-task}"
MAX_RETRIES=3
STATE_FILE="$BASEDIR/orchestration/state.json"
DIAG_DIR="$BASEDIR/diagnostics"

if [ -z "$TEST_CMD" ]; then
  echo "Uso: $0 '<comando>' '<agente>' '<task-slug>'"
  exit 1
fi

TIMESTAMP=$(date '+%Y-%m-%d-%H%M')
LOG_DIR="$BASEDIR/orchestration/state"
mkdir -p "$LOG_DIR" "$DIAG_DIR"

# Aggiorna state.json in modo sicuro
update_state_retry() {
  local retry="$1"
  local active="$2"
  if command -v python3 &>/dev/null && [ -f "$STATE_FILE" ]; then
    python3 - <<PYEOF 2>/dev/null || true
import json
with open('$STATE_FILE') as f: s = json.load(f)
s['self_correction']['active'] = $active
s['self_correction']['current_retry'] = $retry
with open('$STATE_FILE', 'w') as f: json.dump(s, f, indent=2)
PYEOF
  fi
}

write_diagnostic() {
  local report_file="$DIAG_DIR/${TIMESTAMP}-${AGENT}-${TASK_SLUG}.json"
  python3 - <<PYEOF 2>/dev/null || true
import json, sys
cycles = []
$(for i in $(seq 1 $MAX_RETRIES); do
  echo "cycles.append({'attempt': $i, 'error': open('$LOG_DIR/.retry-$i.log').read().strip() if __import__('os').path.exists('$LOG_DIR/.retry-$i.log') else 'n/a', 'outcome': 'failed'})"
done)
report = {
  'generated_at': '$(date "+%d-%m-%Y %H:%M")',
  'task': '$TASK_SLUG',
  'agent': '$AGENT',
  'retries': $MAX_RETRIES,
  'test_command': '$TEST_CMD',
  'cycles': cycles,
  'root_cause_hypothesis': 'Analisi manuale richiesta — vedi logs in orchestration/state/',
  'suggested_next_action': 'Leggere i log di errore, correggere manualmente, poi eseguire: ./execution/run-tests.sh',
  'files_involved': []
}
with open('$report_file', 'w') as f: json.dump(report, f, indent=2)
print(f'Report generato: $report_file')
PYEOF
  if command -v python3 &>/dev/null && [ -f "$STATE_FILE" ]; then
    python3 - <<PYEOF 2>/dev/null || true
import json
with open('$STATE_FILE') as f: s = json.load(f)
s['self_correction']['active'] = False
s['self_correction']['current_retry'] = 0
s['self_correction']['report_path'] = '$report_file'
with open('$STATE_FILE', 'w') as f: json.dump(s, f, indent=2)
PYEOF
  fi
}

echo ""
echo "=== Self-Correction Loop — $AGENT / $TASK_SLUG ==="
echo "Comando: $TEST_CMD"
echo "Max retry: $MAX_RETRIES"
echo ""

ATTEMPT=0
while [ "$ATTEMPT" -lt "$MAX_RETRIES" ]; do
  ATTEMPT=$((ATTEMPT + 1))
  RETRY_LOG="$LOG_DIR/.retry-${ATTEMPT}.log"

  echo "--- Tentativo $ATTEMPT/$MAX_RETRIES ---"
  update_state_retry "$ATTEMPT" "true"

  if eval "$TEST_CMD" > "$RETRY_LOG" 2>&1; then
    echo "[OK] Test superato al tentativo $ATTEMPT."
    update_state_retry "0" "false"
    # Pulisci log temporanei
    rm -f "$LOG_DIR"/.retry-*.log
    exit 0
  fi

  echo "[FAIL] Errore al tentativo $ATTEMPT. Log:"
  tail -20 "$RETRY_LOG" | sed 's/^/  /'
  echo ""

  if [ "$ATTEMPT" -lt "$MAX_RETRIES" ]; then
    echo "  → Analisi causa e correzione in corso..."
    echo "  (L'agente deve correggere il codice prima del prossimo tentativo)"
    echo ""
    # Pausa breve per permettere all'agente di leggere il log e agire
    sleep 1
  fi
done

echo "=== BLOCCO: $MAX_RETRIES tentativi esauriti ==="
write_diagnostic
echo ""
echo "Azione richiesta: leggere il report in $DIAG_DIR/ e sbloccare manualmente."
exit 1
