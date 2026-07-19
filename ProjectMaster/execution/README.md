# Execution Layer

Questo layer contiene **script deterministici** invocati dagli agenti per compiere azioni reali e verificabili.

Gli script qui dentro sono l'unico modo in cui un agente può interagire con l'ambiente di esecuzione
(terminale, file system, test runner, build system). Non si eseguono comandi ad hoc — si usano questi script.

---

## Struttura

```
execution/
├── README.md           ← questo file
├── health-check.sh     ← verifica che l'ambiente sia pronto
├── run-tests.sh        ← esegue i test e cattura l'esito
└── validate-build.sh   ← verifica che il progetto compili senza errori
```

---

## Principi

1. **Deterministici** — stesso input, stesso output. Nessun side effect non documentato.
2. **Exit code significativo** — `0` = successo, `1` = fallimento. Gli agenti leggono l'exit code.
3. **Output catturabile** — stdout/stderr strutturati, leggibili sia da agenti che da umani.
4. **Idempotenti** — eseguibili più volte senza effetti collaterali.

---

## Verification Loop

Il ciclo di verifica obbligatorio prima di chiudere qualsiasi task di implementazione:

```bash
./execution/health-check.sh     # 1. Ambiente OK?
./execution/validate-build.sh   # 2. Compila?
./execution/run-tests.sh        # 3. Test passano?
```

Se uno dei tre fallisce (exit code ≠ 0), il task NON è completato.

---

## Personalizzazione per progetto

Ogni progetto adatta questi script al suo stack. Esempi:
- **Node.js**: `run-tests.sh` chiama `npm test`
- **Python**: `run-tests.sh` chiama `pytest --tb=short`
- **Go**: `run-tests.sh` chiama `go test ./...`

Non modificare la firma degli script (parametri, exit code, output format) — solo il corpo.
