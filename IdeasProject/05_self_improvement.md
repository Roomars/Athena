# Athena — Self-Modification Engine

## Principio

Athena può proporre modifiche a se stessa — skills, core Python, e anche codice Swift.
Ogni modifica richiede conferma esplicita di Roby prima di essere applicata.
Ogni modifica è versionata con git. Ogni fallimento triggera rollback automatico.

---

## Tipi di modifica

| Tipo | Scope | Hot reload? | Tempo applicazione |
|---|---|---|---|
| Nuova skill | `/skills/*.py` | Sì (< 1s) | Immediato |
| Modifica skill esistente | `/skills/*.py` | Sì (< 1s) | Immediato |
| Modifica core Python | `/athena/core/` | No — restart daemon | ~3s |
| Modifica UI Swift | `/AthenaUI/` | No — xcodebuild | ~30-60s |
| Nuova dipendenza Python | `requirements.txt` | No — pip install + restart | ~30-60s |

---

## Ciclo completo self-modification

```
TRIGGER
Athena nota un limite, un bug, o riceve richiesta di miglioramento
        ↓
ANALISI (Qwen2.5 32B)
Legge il codice esistente rilevante
Identifica esattamente cosa cambiare e perché
        ↓
PROPOSTA
Genera diff/patch con spiegazione in italiano
Stima impatto: cosa cambia, rischi, benefici
Mostra a Roby nella UI con diff colorato
        ↓
CONFERMA (Roby)
"Sì" → procede
"No" → archivia la proposta in self/proposals/ per riferimento futuro
        ↓
BACKUP
git commit dello stato corrente ("backup pre-modifica: [descrizione]")
        ↓
APPLICAZIONE
Applica il diff al file
        ↓
TEST
Esegue test automatici del modulo modificato
Se skill: test unitario standard
Se core: pytest suite completa
Se Swift: xcodebuild + test
        ↓
VALUTAZIONE
✅ Test passano → git commit ("self-improve: [descrizione]")
              → hot reload / restart / rebuild
              → notifica a Roby: "Modifica applicata con successo"
❌ Test falliscono → git checkout HEAD (rollback)
              → notifica a Roby con log errore
              → tentativo 2 (max 3 totali)
              → dopo 3 fallimenti: archivia in self/failed/ + stop
```

---

## Formato proposta

Quando Athena mostra una proposta a Roby:

```
PROPOSTA MODIFICA — web_search.py

Motivo: La ricerca DuckDuckGo restituisce HTML grezzo senza parsing.
        Le risposte sono spesso inutilizzabili.

Cosa cambio: Aggiungo BeautifulSoup per estrarre solo il testo pulito
              dai risultati. Aggiungo anche un limite di 5 risultati max.

Impatto: Solo web_search.py. Nessuna modifica al core.
         Dipendenza nuova: beautifulsoup4 (già installata? verifica)

--- web_search.py (attuale)
+++ web_search.py (proposta)
@@ -12,7 +12,12 @@
-    response = requests.get(url)
-    return response.text
+    response = requests.get(url)
+    soup = BeautifulSoup(response.text, 'html.parser')
+    results = soup.find_all('div', class_='result')[:5]
+    return '\n'.join(r.get_text() for r in results)

Confermi? [Sì / No / Modifica]
```

---

## Self-reflection periodica

Ogni settimana (o su richiesta), Athena esegue un ciclo di auto-valutazione:

1. Legge il log delle conversazioni recenti
2. Identifica: errori ripetuti, risposte lente, skills mancanti
3. Genera un report "cosa potrei migliorare"
4. Propone le 3 modifiche più impattanti

Questo report viene mostrato a Roby in forma di briefing settimanale.

---

## Sicurezza e limiti

**Cosa Athena NON può modificare da sola (anche con conferma):**
- Il sistema di conferma stesso (self_modify.py non si auto-modifica)
- Le credenziali e le chiavi API
- La logica di backup/rollback
- Il profilo utente (roby.md) — solo con consenso esplicito separato

**Limite modifiche per sessione:** max 3 modifiche per sessione di auto-miglioramento.
Dopo 3, si ferma e aspetta la prossima sessione.

---

## Git come backbone

```bash
# Ogni stato è tracciabile
git log --oneline
# a3f2c1b self-improve: web_search aggiunge parsing HTML
# b8e9d4a self-improve: nuova skill calendar_summary
# c1a7f3e backup pre-modifica: core router refactor
# d4b2e8f init: Athena 2.0 baseline
```

Roby può sempre tornare a qualsiasi stato:
```bash
git checkout <hash>  # o Athena lo fa su richiesta
```

---

## Nota su modifiche Swift

Quando Athena propone una modifica Swift:
- xcodebuild richiede ~30-60 secondi
- Athena avvisa: "questa modifica richiede rebuild dell'app (~1 minuto)"
- Dopo rebuild: l'app Swift si riavvia automaticamente
- Il daemon Python rimane attivo durante il rebuild (nessuna interruzione conversazione)
