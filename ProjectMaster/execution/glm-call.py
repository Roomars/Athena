#!/usr/bin/env python3
"""
GLM Delegation Engine — delega task di codifica a GLM via provider configurabile.

Provider supportati:
  nvidia      → NVIDIA NIM (GRATUITO, 40 RPM, 203K ctx) — build.nvidia.com  ← default
  zai         → Z.ai international api.z.ai (Coding Plan ~$10/mese)
  openrouter  → OpenRouter (200+ modelli, pay-per-use) — openrouter.ai

Uso:
  python3 execution/glm-call.py --prompt "..." --task T01 --agent frontend
  python3 execution/glm-call.py --prompt-file orchestration/glm-prompts/T01.md --task T01
  python3 execution/glm-call.py --probe                  # scopri modelli attivi
  python3 execution/glm-call.py --dry-run --prompt "..." # preview senza chiamare API

Output:
  orchestration/glm-output/<task>-<agent>.md
  exit 0 = successo | exit 1 = errore API | exit 2 = diagnostics generato
"""

import os
import sys
import json
import argparse
import datetime
from pathlib import Path
from typing import Optional
from urllib import request, error as urllib_error

# ─── Provider config ──────────────────────────────────────────────────────────
PROVIDERS = {
    "nvidia": {
        "base_url":      "https://integrate.api.nvidia.com/v1/chat/completions",
        "default_model": "z-ai/glm-5.1",
        "env_key":       "NVIDIA_API_KEY",
        "signup_url":    "https://build.nvidia.com",
        "free":          True,
        "models": [
            "z-ai/glm-5.1",
            "z-ai/glm-4.7",
            "z-ai/glm-4.5-air",
        ],
    },
    "zai": {
        "base_url":      "https://api.z.ai/api/paas/v4/chat/completions",
        "default_model": "glm-4-flash",
        "env_key":       "ZAI_API_KEY",
        "signup_url":    "https://z.ai",
        "free":          False,
        "models": [
            "glm-4-flash", "glm-4.7", "glm-4.7-flash",
            "glm-4.5-air", "glm-5.1",
        ],
    },
    "openrouter": {
        "base_url":      "https://openrouter.ai/api/v1/chat/completions",
        "default_model": "z-ai/glm-5.1",
        "env_key":       "OPENROUTER_API_KEY",
        "signup_url":    "https://openrouter.ai",
        "free":          False,
        "models": [
            "z-ai/glm-5.1",
            "z-ai/glm-4.7",
            "anthropic/claude-sonnet-4-6",
            "anthropic/claude-haiku-4-5",
            "openai/gpt-4o",
            "deepseek/deepseek-r1",
            "google/gemini-2.5-pro",
            "meta-llama/llama-3.3-70b-instruct",
        ],
    },
}

BASEDIR    = Path(__file__).parent.parent   # ProjectMaster/
STATE_FILE = BASEDIR / "orchestration/state.json"
OUTPUT_DIR = BASEDIR / "orchestration/glm-output"
DIAG_DIR   = BASEDIR / "diagnostics"

ERROR_CODES = {
    "1113": "Saldo insufficiente — ricaricare sul portale del provider",
    "1211": "Modello non trovato — usare --probe per vedere i modelli attivi",
    "1301": "Limite token superato — ridurre il prompt o usare modello con context più lungo",
    "1302": "Contenuto non consentito dalla policy del provider",
    "1401": "Chiave API non valida — verificare la chiave in .env",
    "1402": "Chiave API scaduta — generare una nuova chiave",
    "429":  "Rate limit raggiunto — attendere o ridurre la frequenza delle chiamate",
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_env():
    env_path = Path(".env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def get_api_key(provider_cfg: dict) -> str:
    env_var = provider_cfg["env_key"]
    key = os.environ.get(env_var, "")
    if not key:
        print(f"[ERRORE] {env_var} non trovata.")
        print(f"  Aggiungila a .env: {env_var}=la_tua_chiave")
        print(f"  Ottieni la chiave su: {provider_cfg['signup_url']}")
        if provider_cfg.get("free"):
            print("  ✓ Piano gratuito disponibile — nessuna carta richiesta")
        sys.exit(1)
    return key


def call_api(prompt: str, model: str, api_key: str, base_url: str) -> dict:
    system_msg = (
        "Sei un motore di generazione codice deterministico. "
        "Produci codice funzionante, privo di bug, pronto all'uso. "
        "Non aggiungere spiegazioni verbose — solo codice e commenti essenziali. "
        "Se hai dubbi su un requisito, scrivi un commento TODO invece di inventare."
    )
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens":  4096,
        "stream":      False,
    }).encode("utf-8")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    # OpenRouter richiede header aggiuntivi per identificare l'app
    if "openrouter.ai" in base_url:
        headers["HTTP-Referer"] = "https://github.com/devtemplate"
        headers["X-Title"]      = "DevTemplate GLM Delegation Engine"

    req = request.Request(base_url, data=payload, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib_error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        code = "?"
        try:
            code = str(json.loads(body).get("error", {}).get("code", e.code))
        except Exception:
            code = str(e.code)
        hint = ERROR_CODES.get(code, "")
        msg  = f"HTTP {e.code} (code {code}): {body}"
        if hint:
            msg += f"\n  → {hint}"
        raise RuntimeError(msg)
    except urllib_error.URLError as e:
        raise RuntimeError(f"Connessione fallita: {e.reason}")


def probe_models(provider_name: str, provider_cfg: dict, api_key: str):
    print(f"\n=== Model Probe — {provider_name} ===")
    ping = "Di' solo: OK"
    available = []
    for model in provider_cfg["models"]:
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": ping}],
            "max_tokens": 5,
        }).encode("utf-8")
        req = request.Request(
            provider_cfg["base_url"], data=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=15) as r:
                available.append(model)
                print(f"  [OK]  {model}")
        except urllib_error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            code = "?"
            try:
                code = str(json.loads(body).get("error", {}).get("code", e.code))
            except Exception:
                pass
            if code not in ("1211",):
                available.append(model)
                print(f"  [OK]  {model:<30} (code: {code} — {ERROR_CODES.get(code, '')})")
            else:
                print(f"  [---] {model:<30} non disponibile")
        except Exception as exc:
            print(f"  [ERR] {model:<30} {exc}")

    print(f"\nModelli attivi: {available or 'nessuno'}")
    return available


def update_state(task_id: str, outcome: str, output_path: Optional[str], error: Optional[str]):
    if not STATE_FILE.exists():
        return
    try:
        state = json.loads(STATE_FILE.read_text())
        state["last_action"] = {
            "timestamp":      datetime.datetime.now().strftime("%d-%m-%Y %H:%M"),
            "agent":          "glm-engine",
            "action":         f"GLM call for task {task_id}",
            "files_modified": [output_path] if output_path else [],
            "outcome":        outcome,
            "error_if_any":   error,
        }
        STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))
    except Exception:
        pass


def write_diagnostic(task_id: str, agent: str, error: str, provider: str):
    DIAG_DIR.mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    report_file = DIAG_DIR / f"{ts}-glm-{provider}-{task_id}.json"
    report = {
        "generated_at":            datetime.datetime.now().strftime("%d-%m-%Y %H:%M"),
        "task":                    task_id,
        "agent":                   agent,
        "provider":                provider,
        "error":                   error,
        "root_cause_hypothesis":   "Verificare chiave API, saldo, connessione, o nome modello",
        "suggested_next_action":   f"Eseguire: python3 execution/glm-call.py --probe --provider {provider}",
    }
    report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"[DIAG] Report: {report_file}")
    update_state(task_id, "failed", None, error)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    load_env()
    parser = argparse.ArgumentParser(
        description="GLM Delegation Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  # NVIDIA NIM (gratuito) — raccomandato
  python3 execution/glm-call.py --provider nvidia --prompt "Scrivi un CRUD per User" --task T01

  # Scopri modelli attivi sul provider
  python3 execution/glm-call.py --provider nvidia --probe

  # Preview prompt senza chiamare l'API
  python3 execution/glm-call.py --prompt-file orchestration/glm-prompts/T01.md --dry-run
        """,
    )
    parser.add_argument("--provider",     type=str, default="nvidia",
                        choices=list(PROVIDERS.keys()),
                        help="Provider API (default: nvidia — gratuito)")
    parser.add_argument("--model",        type=str, default=None,
                        help="Nome modello (default: modello consigliato del provider)")
    parser.add_argument("--prompt",       type=str, help="Prompt diretto")
    parser.add_argument("--prompt-file",  type=str, help="File .md con il prompt")
    parser.add_argument("--task",         type=str, default="T00")
    parser.add_argument("--agent",        type=str, default="unknown")
    parser.add_argument("--probe",        action="store_true",
                        help="Testa quali modelli sono attivi sull'account")
    parser.add_argument("--list-providers", action="store_true",
                        help="Mostra tutti i provider configurabili")
    parser.add_argument("--dry-run",      action="store_true",
                        help="Mostra prompt senza chiamare l'API")
    args = parser.parse_args()

    provider_cfg = PROVIDERS[args.provider]
    model = args.model or provider_cfg["default_model"]

    # ── Early-exit flags ──────────────────────────────────────────────────────
    if args.list_providers:
        print("\nProvider disponibili:")
        for name, cfg in PROVIDERS.items():
            free_tag = " ✓ GRATUITO" if cfg["free"] else ""
            default  = " ← default" if name == "nvidia" else ""
            print(f"  {name:<10} {cfg['signup_url']:<35} {cfg['env_key']}{free_tag}{default}")
            print(f"             Modello default: {cfg['default_model']}")
        sys.exit(0)

    if args.probe:
        api_key = get_api_key(provider_cfg)
        probe_models(args.provider, provider_cfg, api_key)
        sys.exit(0)

    # ── Carica prompt ─────────────────────────────────────────────────────────
    if args.prompt_file:
        pf = Path(args.prompt_file)
        if not pf.exists():
            print(f"[ERRORE] File non trovato: {args.prompt_file}")
            sys.exit(1)
        prompt = pf.read_text()
    elif args.prompt:
        prompt = args.prompt
    else:
        print("[ERRORE] Fornire --prompt oppure --prompt-file")
        sys.exit(1)

    if args.dry_run:
        print(f"\n[DRY RUN] Provider: {args.provider} | Modello: {model}")
        print("─" * 60)
        print(prompt[:600] + ("..." if len(prompt) > 600 else ""))
        print("─" * 60)
        sys.exit(0)

    # ── Chiamata API ──────────────────────────────────────────────────────────
    api_key = get_api_key(provider_cfg)
    print(f"\n=== GLM Delegation — {args.task} ===")
    print(f"  Provider : {args.provider}")
    print(f"  Modello  : {model}")
    print(f"  Agente   : {args.agent}")
    print(f"  Prompt   : {len(prompt)} caratteri")
    print()

    try:
        response = call_api(prompt, model, api_key, provider_cfg["base_url"])
    except RuntimeError as e:
        print(f"[ERRORE] {e}")
        write_diagnostic(args.task, args.agent, str(e), args.provider)
        sys.exit(1)

    try:
        content   = response["choices"][0]["message"]["content"]
        usage     = response.get("usage", {})
        tok_in    = usage.get("prompt_tokens", 0)
        tok_out   = usage.get("completion_tokens", 0)
    except (KeyError, IndexError) as e:
        err = f"Risposta API malformata: {e}"
        write_diagnostic(args.task, args.agent, err, args.provider)
        sys.exit(1)

    # ── Scrivi output ─────────────────────────────────────────────────────────
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{args.task}-{args.agent}.md"
    output_file.write_text(
        f"# GLM Output — {args.task}\n\n"
        f"**Provider:** {args.provider} | **Modello:** {model}\n"
        f"**Agente:** {args.agent} | **Generato:** {datetime.datetime.now().strftime('%d-%m-%Y %H:%M')}\n"
        f"**Token:** {tok_in} in / {tok_out} out\n\n"
        f"---\n\n"
        f"{content}\n\n"
        f"---\n\n"
        f"> ⚠ Output generato da GLM. Revisione obbligatoria prima dell'integrazione.\n",
        encoding="utf-8",
    )
    update_state(args.task, "success", str(output_file), None)

    print(f"[OK] Output → {output_file}")
    print(f"     Token usati: {tok_in} in + {tok_out} out")
    cost = "$0.00 (piano gratuito)" if provider_cfg["free"] else f"~${(tok_in * 0.00000098 + tok_out * 0.00000308):.4f}"
    print(f"     Costo: {cost}")
    print(f"\n⚠  Revisione obbligatoria: leggere {output_file} prima di integrare.")


if __name__ == "__main__":
    main()
