# Agenti in standby

Questa cartella contiene agenti non attivi nel routing principale MisterLab.

## Progetto OCR (in pausa)

| File | Ruolo nel pipeline |
|---|---|
| `document-structure-analyzer.md` | Analisi layout documento pre-OCR |
| `ocr-preprocessing-optimizer.md` | Ottimizzazione immagine pre-estrazione |
| `ocr-quality-assurance.md` | Validazione output OCR finale |
| `text-comparison-validator.md` | Confronto testo estratto vs originale |

**Stato:** sviluppo iniziato, in pausa. Da riprendere in fase futura.
**Non referenziati** in `CLAUDE.md` routing — non verranno caricati automaticamente.

## Agenti generici (non MisterLab)

| File | Note |
|---|---|
| `frontend-developer.md` | Frontend generico — sostituito da `agents/frontend.md` |
| `mobile-developer.md` | React Native / Flutter — fuori scope MisterLab |
| `python-pro.md` | Python generico — fuori scope MisterLab |

Questi file possono essere eliminati in qualsiasi momento senza perdita funzionale.