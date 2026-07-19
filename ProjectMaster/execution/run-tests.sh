#!/usr/bin/env bash
# Esegue la suite di test del progetto e cattura l'esito.
# Exit 0 = tutti i test passati. Exit 1 = uno o più test falliti.
#
# Adatta la sezione "RUNNER" al tuo stack. Non modificare il resto.

set -uo pipefail

BASEDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP=$(date '+%d-%m-%Y %H:%M:%S')
LOG_FILE="$BASEDIR/orchestration/state/.last-test-run.log"

echo ""
echo "=== Test Run — $TIMESTAMP ==="
echo ""

# --- RUNNER: adatta al tuo stack ---
run_tests() {
  if [ -f "package.json" ]; then
    echo "Stack: Node.js"
    npm test 2>&1
    return $?
  fi

  if [ -f "pytest.ini" ] || [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
    echo "Stack: Python"
    python3 -m pytest --tb=short -q 2>&1
    return $?
  fi

  if [ -f "go.mod" ]; then
    echo "Stack: Go"
    go test ./... 2>&1
    return $?
  fi

  echo "ERRORE: Nessun test runner rilevato."
  echo "Configura la funzione run_tests() in execution/run-tests.sh"
  return 1
}
# --- FINE RUNNER ---

# Esegui e cattura output
mkdir -p orchestration/state
{
  echo "=== Test Run — $TIMESTAMP ==="
  run_tests
  EXIT_CODE=$?
  echo ""
  echo "Exit code: $EXIT_CODE"
  echo "=== Fine ==="
} | tee "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

echo ""
if [ "$EXIT_CODE" -eq 0 ]; then
  echo "Test SUPERATI. Log salvato in $LOG_FILE"
else
  echo "Test FALLITI (exit $EXIT_CODE). Vedi $LOG_FILE per i dettagli."
fi

exit "$EXIT_CODE"
