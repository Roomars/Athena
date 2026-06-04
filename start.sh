#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

# Controlla Python
if ! command -v python3 &>/dev/null; then
  echo "❌ Python3 non trovato. Installalo con: brew install python"
  exit 1
fi

# Controlla che Ollama sia in esecuzione
if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
  echo "⚠️  Ollama non risponde su :11434. Avvialo con: ollama serve"
  exit 1
fi

# Crea venv se non esiste
if [ ! -d ".venv" ]; then
  echo "→ Creo ambiente virtuale…"
  python3 -m venv .venv
fi

source .venv/bin/activate

# Installa dipendenze
echo "→ Installo dipendenze…"
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "⚡ Athena in avvio su http://localhost:8000"
echo "   Premi Ctrl+C per fermare."
echo ""

uvicorn core.app:app --host 0.0.0.0 --port 8000 --reload
