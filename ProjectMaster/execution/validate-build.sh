#!/usr/bin/env bash
# Verifica che il progetto compili senza errori.
# Exit 0 = build OK. Exit 1 = errori di build.
#
# Adatta la sezione "BUILD COMMAND" al tuo stack.

set -uo pipefail

TIMESTAMP=$(date '+%d-%m-%Y %H:%M:%S')

echo ""
echo "=== Build Validation — $TIMESTAMP ==="
echo ""

# --- BUILD COMMAND: adatta al tuo stack ---
run_build() {
  if [ -f "package.json" ]; then
    # Controlla se esiste uno script "build"
    if node -e "require('./package.json').scripts.build" 2>/dev/null | grep -q '.'; then
      echo "Stack: Node.js — npm run build"
      npm run build 2>&1
      return $?
    fi
    # Altrimenti typecheck
    if [ -f "tsconfig.json" ]; then
      echo "Stack: TypeScript — tsc --noEmit"
      npx tsc --noEmit 2>&1
      return $?
    fi
    echo "Nessuno script build configurato in package.json. Skip."
    return 0
  fi

  if [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
    echo "Stack: Python — syntax check"
    python3 -m compileall -q . 2>&1
    return $?
  fi

  if [ -f "go.mod" ]; then
    echo "Stack: Go — go build"
    go build ./... 2>&1
    return $?
  fi

  echo "Nessun sistema di build rilevato. Skip."
  return 0
}
# --- FINE BUILD COMMAND ---

run_build
EXIT_CODE=$?

echo ""
if [ "$EXIT_CODE" -eq 0 ]; then
  echo "Build SUPERATA."
else
  echo "Build FALLITA (exit $EXIT_CODE). Correggi gli errori prima di procedere."
fi

exit "$EXIT_CODE"
