#!/usr/bin/env bash
# build-mac.sh — compila Athena.app per macOS
set -e
cd "$(dirname "$0")"

# Assicura che ~/.cargo/bin sia nel PATH (rustup non lo aggiunge negli shell non-interattivi)
export PATH="$HOME/.cargo/bin:/opt/homebrew/bin:$PATH"
[ -f "$HOME/.cargo/env" ] && source "$HOME/.cargo/env"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC}  $1"; }
die()  { echo -e "${RED}✗${NC}  $1"; exit 1; }
step() { echo -e "\n${GREEN}→${NC} $1"; }

# ── 1. Dipendenze ────────────────────────────────────────────────────────────

step "Controllo dipendenze…"

command -v rustc &>/dev/null || die "Rust non trovato. Installa: https://rustup.rs"
ok "Rust $(rustc --version | awk '{print $2}')"

if ! cargo tauri --version &>/dev/null 2>&1; then
    step "Installo Tauri CLI…"
    cargo install tauri-cli --version "^2" --locked
fi
ok "Tauri CLI $(cargo tauri --version)"

# Python venv per il backend
if [ ! -d ".venv" ]; then
    step "Creo venv Python…"
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
ok "Backend Python pronto"

# ── 2. Genera icone PNG ──────────────────────────────────────────────────────

step "Generazione icone…"

# Prova a installare cairosvg per la generazione SVG→PNG
pip install -q cairosvg 2>/dev/null || warn "cairosvg non disponibile, uso fallback"

python3 scripts/gen_icons.py

# Genera tutti i formati icon (32x32, 128x128, .icns, .ico) dal 512x512 sorgente
step "Generazione formati icona Tauri…"
cargo tauri icon src-tauri/icons/app-icon.png

ok "Icone generate"

# ── 3. Build Tauri ───────────────────────────────────────────────────────────

step "Build Athena.app (release)…"
echo "   Potrebbe richiedere qualche minuto la prima volta."

cargo tauri build

# ── 4. Output ────────────────────────────────────────────────────────────────

APP_PATH="$(find src-tauri/target/release/bundle/macos -name 'Athena.app' 2>/dev/null | head -1)"

echo ""
echo -e "${GREEN}══════════════════════════════════════${NC}"
echo -e "${GREEN}  Athena.app compilata con successo!${NC}"
echo -e "${GREEN}══════════════════════════════════════${NC}"
echo ""

if [ -n "$APP_PATH" ]; then
    ok ".app:  $APP_PATH"
    echo ""
    echo "   Per installarla in /Applications:"
    echo "   cp -r \"$APP_PATH\" /Applications/"
    echo ""
    echo "   Per aprirla subito:"
    echo "   open \"$APP_PATH\""
fi

echo ""
echo "   L'app appare solo nella menu bar (niente Dock)."
echo "   Assicurati che Ollama sia in esecuzione prima di avviarla."
echo ""
