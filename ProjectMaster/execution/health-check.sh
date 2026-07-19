#!/usr/bin/env bash
# Verifica che l'ambiente di sviluppo sia pronto.
# Exit 0 = tutto OK. Exit 1 = problemi trovati.
# Funziona da qualsiasi directory grazie a BASEDIR.

set -euo pipefail

BASEDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$BASEDIR/.." && pwd)"

PASS=0
FAIL=0
WARNINGS=()

check() {
  local label="$1"
  local cmd="$2"
  if eval "$cmd" &>/dev/null; then
    echo "  [OK]  $label"
    ((PASS++)) || true
  else
    echo "  [FAIL] $label"
    ((FAIL++)) || true
  fi
}

warn() {
  local msg="$1"
  WARNINGS+=("$msg")
  echo "  [WARN] $msg"
}

echo ""
echo "=== Health Check — $(date '+%d-%m-%Y %H:%M') ==="
echo ""

# --- Runtime (adatta al tuo stack) ---
echo "Runtime:"
check "Node.js installato"  "command -v node"
check "npm installato"      "command -v npm"
check "Python 3 installato" "command -v python3"
check "git installato"      "command -v git"

# --- Dipendenze progetto ---
echo ""
echo "Dipendenze:"
if [ -f "$ROOT/package.json" ]; then
  check "node_modules presente" "[ -d '$ROOT/node_modules' ]"
else
  warn "Nessun package.json trovato — skip node_modules check"
fi

if [ -f "$ROOT/requirements.txt" ]; then
  check "pip installato" "command -v pip3"
fi

# --- Struttura ProjectMaster ---
echo ""
echo "Struttura ProjectMaster:"
check "CLAUDE.md presente"              "[ -f '$ROOT/CLAUDE.md' ]"
check "sessione.md presente"            "[ -f '$ROOT/sessione.md' ]"
check "ProjectMaster/directives/"       "[ -d '$BASEDIR/directives' ]"
check "ProjectMaster/orchestration/"    "[ -d '$BASEDIR/orchestration' ]"
check "ProjectMaster/execution/"        "[ -d '$BASEDIR/execution' ]"
check "ProjectMaster/knowledge/"        "[ -d '$BASEDIR/knowledge' ]"
check "ProjectMaster/diagnostics/"      "[ -d '$BASEDIR/diagnostics' ]"

# --- Riepilogo ---
echo ""
echo "=== Riepilogo ==="
echo "  Passati:  $PASS"
echo "  Falliti:  $FAIL"
[ ${#WARNINGS[@]} -gt 0 ] && printf "  Warning:  %s\n" "${WARNINGS[@]}"
echo ""

if [ "$FAIL" -gt 0 ]; then
  echo "Health check FALLITO. Risolvi i problemi sopra prima di procedere."
  exit 1
else
  echo "Health check SUPERATO. Ambiente pronto."
  exit 0
fi
