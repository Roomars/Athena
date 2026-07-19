---
name: glm-delegate
description: "Delega task di codifica ripetitivi o boilerplate a GLM-5.1 via NVIDIA NIM (gratuito) o OpenRouter, riservando Claude al monitoraggio qualità e alle decisioni architetturali. Usa quando il task è ben definito, a basso rischio, e produce output verificabile."
---

# GLM Delegation — Codifica a Costo Zero

Usa GLM-5.1 via NVIDIA NIM (gratuito) per generare codice grezzo.
Claude monitora, valida e integra.

---

## Provider disponibili

| Provider | Chiave | Modello | Costo | Quando usarlo |
|---|---|---|---|---|
| `nvidia` | `NVIDIA_API_KEY` | `z-ai/glm-5.1` | **$0** | Default — sempre |
| `openrouter` | `OPENROUTER_API_KEY` | qualsiasi | pay-per-use | Quando serve un modello specifico |
| `zai` | `ZAI_API_KEY` | `glm-5.1` | ~$10/mese | Se già abbonati al Coding Plan |

**Setup NVIDIA NIM (gratuito):**
1. Registrarsi su build.nvidia.com (no carta di credito)
2. Generare una chiave `nvapi-...`
3. Aggiungere `NVIDIA_API_KEY=nvapi-...` in `.env`

---

## Quando delegare a GLM

**Delegare sempre a GLM (--provider nvidia):**
- CRUD su entità esistenti
- Scaffold di componenti/pagine su pattern già nel progetto
- Migration DB su schema già definito
- Test unitari per funzioni già scritte
- Serializer, DTO, validator, enum, costanti
- Interfacce TypeScript da schema JSON/OpenAPI

**Tenere in Claude:**
- Architettura di sistema, scelta pattern
- Logica di business critica o non ovvia
- Codice security-sensitive (auth, permessi, crittografia)
- Bug fix complessi
- Qualsiasi cosa non verificabile automaticamente

---

## Procedura

### Step 1 — Prepara il prompt

Crea `orchestration/glm-prompts/[task-id].md`:

```markdown
# Task: [descrizione sintetica]

## Contesto
[Incolla SOLO le parti rilevanti da knowledge/ e file esistenti — max 2000 token]

## Richiesta
Genera [tipo di file] per [entità] seguendo questo pattern:

[esempio di file simile già nel progetto]

## Vincoli
- Linguaggio: [TypeScript / Python / ecc.]
- NON inventare logica non specificata — scrivi TODO se mancano info
```

### Step 2 — Delega

```bash
# NVIDIA NIM (gratuito — default)
python3 execution/glm-call.py \
  --provider nvidia \
  --prompt-file orchestration/glm-prompts/T01.md \
  --task T01 --agent frontend

# OpenRouter con modello specifico
python3 execution/glm-call.py \
  --provider openrouter --model deepseek/deepseek-r1 \
  --prompt-file orchestration/glm-prompts/T01.md \
  --task T01 --agent backend
```

Output in: `orchestration/glm-output/T01-[agente].md`

### Step 3 — Review obbligatoria (Claude Reviewer — Haiku)

Leggere `orchestration/glm-output/[task].md` e verificare:

- [ ] Segue le convenzioni del progetto?
- [ ] Nessuna invenzione non richiesta?
- [ ] I `TODO` segnalati sono stati notati?
- [ ] Nessuna vulnerabilità ovvia?

### Step 4 — Verifica integration

```bash
./execution/self-correct.sh "npm test -- --testPathPattern=[file]" "reviewer" "T01"
```

---

## Risparmio token stimato

| Task | Claude prima | Claude con GLM | Risparmio |
|---|---|---|---|
| CRUD 4 endpoint | ~12.000 tok | ~2.000 tok | 83% |
| Scaffold componente UI | ~6.000 tok | ~1.500 tok | 75% |
| Suite 10 test unitari | ~8.000 tok | ~1.800 tok | 78% |
| Migration DB | ~4.000 tok | ~800 tok | 80% |

GLM-5.1 via NVIDIA NIM = $0. Claude usa solo Haiku per review. Costo netto quasi zero.

---

## Limitazioni

- GLM non conosce il tuo progetto → il prompt deve essere autosufficiente
- Qualità inferiore a Opus su ragionamento complesso → non delegare architettura
- Output sempre in `orchestration/glm-output/` → mai direttamente in `src/`
- Review non opzionale → codice GLM non revisionato non va in produzione
