# Errori Appresi — Athena

Ogni errore ha un codice progressivo ERR-N. Mai cancellare — solo aggiungere.

---

### ERR-1 — titleBarStyle Overlay ha rotto drag e resize
**Data:** 04-06-2026
**Contesto:** Aggiunta della modalità Overlay alla finestra Tauri per imitare lo stile Claude Desktop.
**Errore:** La finestra non poteva essere spostata né ridimensionata dall'utente.
**Causa:** Overlay rimuove la titlebar nativa. Il drag richiede CSS `-webkit-app-region: drag` + permesso Tauri. Entrambi aggiunti ma mai testati sul `.app` reale — solo `cargo check`.
**Soluzione:** Rimosso titleBarStyle Overlay, ripristinata titlebar nativa.
**Regola:** Ogni modifica a comportamento/aspetto della finestra va testata sul `.app` buildata prima di dichiarare completato. `cargo check` verifica solo che il Rust compili.

---

## Formato

```
### ERR-1 — [titolo breve]
**Data:** DD-MM-AAAA
**Contesto:** [cosa si stava facendo]
**Errore:** [cosa è andato storto]
**Causa:** [perché è successo]
**Soluzione:** [cosa ha risolto]
**Regola:** [mai fare X / sempre fare Y]
```
