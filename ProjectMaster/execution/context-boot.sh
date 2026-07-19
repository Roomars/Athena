#!/usr/bin/env bash
# Context Boot — stampa lo stato completo della sessione in un unico output compatto.
# Chiamare all'inizio di ogni sessione invece di leggere 4-5 file separati.
# Ottimizza i token: un solo tool call invece di multipli Read.

set -uo pipefail

BASEDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

STATE_FILE="$BASEDIR/orchestration/state.json"
JOURNAL_FILE="$BASEDIR/orchestration/state/journal.md"
CANONICAL_FILE="$BASEDIR/orchestration/state/canonical.md"
DIAG_DIR="$BASEDIR/diagnostics"
KNOWLEDGE_DIR="$BASEDIR/knowledge"
PLANS_DIR="$BASEDIR/orchestration/plans"

SEP="─────────────────────────────────────────"

echo ""
echo "╔════════════════════════════════════════╗"
echo "║         CONTEXT BOOT — $(date '+%d-%m-%Y %H:%M')     ║"
echo "╚════════════════════════════════════════╝"
echo ""

# --- 1. Long-Horizon State ---
echo "[ STATE ]  $SEP"
if [ -f "$STATE_FILE" ]; then
  python3 - <<PYEOF 2>/dev/null || cat "$STATE_FILE"
import json
with open('$STATE_FILE') as f: s = json.load(f)
proj = s.get('project', {})
sess = s.get('session', {})
prog = s.get('progress', {})
last = s.get('last_action', {})
env  = s.get('environment', {})
sc   = s.get('self_correction', {})

print(f"  Progetto     : {proj.get('name') or 'non impostato'}")
print(f"  Fase         : {proj.get('phase') or 'init'}")
print(f"  Sessione     : {'ATTIVA' if sess.get('active') else 'non attiva'}")
print(f"  Obiettivo    : {sess.get('objective') or '—'}")
print(f"  Piano attivo : {sess.get('active_plan') or '—'}")
print(f"  Dev server   : {'SÌ → ' + str(env.get('dev_server_url')) if env.get('dev_server_running') else 'no'}")
print(f"  Ultimo test  : exit {env.get('last_test_exit_code') if env.get('last_test_exit_code') is not None else '?'}")

in_prog = prog.get('in_progress_task')
if in_prog:
    print(f"\n  ⚠ TASK INTERROTTO: {in_prog}")
    print(f"    → Riprendere da questo punto, non ricominciare da zero")

blocked = prog.get('blocked_tasks', [])
if blocked:
    print(f"\n  🔴 TASK BLOCCATI: {', '.join(str(b) for b in blocked)}")

if sc.get('active'):
    print(f"\n  ↻ SELF-CORRECTION ATTIVO: tentativo {sc.get('current_retry')}/{sc.get('max_retries')}")

if last.get('action'):
    print(f"\n  Ultima azione : [{last.get('agent')}] {last.get('action')} → {last.get('outcome')}")
    if last.get('error_if_any'):
        print(f"  Ultimo errore : {last['error_if_any']}")
PYEOF
else
  echo "  state.json non trovato — prima sessione del progetto"
fi

# --- 2. Diagnostics aperti ---
echo ""
echo "[ DIAGNOSTICS ]  $SEP"
if [ -d "$DIAG_DIR" ]; then
  OPEN_REPORTS=$(find "$DIAG_DIR" -maxdepth 1 -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
  if [ "$OPEN_REPORTS" -gt "0" ]; then
    echo "  ⛔ $OPEN_REPORTS REPORT APERTO/I — risolvere prima di procedere:"
    find "$DIAG_DIR" -maxdepth 1 -name "*.json" | while read -r f; do
      echo "     → $(basename "$f")"
    done
  else
    echo "  OK — nessun blocco attivo"
  fi
else
  echo "  OK — nessun diagnostics trovato"
fi

# --- 3. Knowledge Hub ---
echo ""
echo "[ KNOWLEDGE ]  $SEP"
if [ -d "$KNOWLEDGE_DIR" ]; then
  FILES=$(find "$KNOWLEDGE_DIR" -type f \( -name "*.md" -o -name "*.json" \) | sort)
  if [ -n "$FILES" ]; then
    echo "$FILES" | while read -r f; do
      SIZE=$(wc -l < "$f" 2>/dev/null || echo "?")
      echo "  • $(basename "$f")  ($SIZE righe)"
    done
  else
    echo "  — nessun documento (aggiungere PRD.md, api_specs.json, ecc.)"
  fi
else
  echo "  — knowledge/ non trovata"
fi

# --- 4. Piani attivi ---
echo ""
echo "[ PLANS ]  $SEP"
if [ -d "$PLANS_DIR" ]; then
  PLANS=$(find "$PLANS_DIR" -name "*.json" ! -name "_template.json" 2>/dev/null | sort -r | head -5)
  if [ -n "$PLANS" ]; then
    echo "$PLANS" | while read -r f; do
      STATUS=$(python3 -c "import json; d=json.load(open('$f')); print(d.get('plan',{}).get('status','?'))" 2>/dev/null || echo "?")
      echo "  • $(basename "$f")  [$STATUS]"
    done
  else
    echo "  — nessun piano trovato"
  fi
else
  echo "  — plans/ non trovata"
fi

# --- 5. Ultimo journal entry ---
echo ""
echo "[ JOURNAL — ultima voce ]  $SEP"
if [ -f "$JOURNAL_FILE" ]; then
  LAST=$(grep -n "^## \[" "$JOURNAL_FILE" | tail -1)
  if [ -n "$LAST" ]; then
    LINE=$(echo "$LAST" | cut -d: -f1)
    sed -n "${LINE},$((LINE+6))p" "$JOURNAL_FILE"
  else
    echo "  — nessuna voce registrata"
  fi
else
  echo "  — journal.md non trovato"
fi

echo ""
echo "[ PRONTO ]  $SEP"
echo "  Orchestratore: leggi il riepilogo sopra e riprendi il lavoro."
echo "  Se task interrotto: riprendi da quello. Se diagnostics aperti: risolvi prima."
echo ""
