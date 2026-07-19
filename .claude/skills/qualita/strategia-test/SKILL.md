---
name: strategia-test
description: Quando e come scrivere test: unit, integrazione, e2e. Piramide dei test, cosa testare e cosa no, copertura minima per tipo di progetto. Usa quando pianifichi la strategia di test di un progetto o decidi quale tipo di test scrivere.
---

# Strategia di Test

Guida pratica per decidere quali test scrivere, quando, e quanti.

## La piramide dei test

```
         /\
        /e2e\          pochi, lenti, costosi
       /------\
      / integr.\       medi
     /----------\
    /  unitari   \     tanti, veloci, economici
   /--------------\
```

**Regola pratica:** più il test è in alto nella piramide, meno ne scrivi.

## Cosa testare con ogni tipo

### Test unitari — veloci, isolati
- Funzioni pure con logica complessa
- Trasformazioni dati
- Validazioni
- Calcoli e algoritmi
- **Non testare:** getter/setter banali, costanti, framework

### Test di integrazione — comportamento reale
- API endpoint (input → output reale)
- Query database su DB reale (non mock)
- Autenticazione e autorizzazione
- Integrazione con servizi esterni (con stub, non mock)

### Test e2e — flussi utente completi
- Login e registrazione
- Flusso principale del prodotto (golden path)
- Checkout, pagamento, operazioni critiche
- **Non testare:** ogni singola variante — solo i flussi core

## Copertura minima per tipo di progetto

| Progetto | Unitari | Integrazione | e2e |
|---|---|---|---|
| API/Backend | 70% | Tutti gli endpoint | — |
| Frontend | 50% logica | Componenti chiave | 3-5 flussi |
| Full-stack | 60% | Endpoint + DB | Golden path |
| Libreria | 80%+ | Casi d'uso pubblici | — |

## Cosa NON testare

- Codice di terze parti (framework, librerie)
- Implementazioni banali senza logica
- UI statica senza comportamento
- Codice che cambia frequentemente (rallenta lo sviluppo)

## Quando i test diventano un problema

- Test che si rompono per ogni refactor → troppo accoppiati all'implementazione
- Test che durano 30+ minuti → blocca il CI, nessuno li esegue
- Mock ovunque → non testano il comportamento reale
- 100% di copertura come obiettivo → porta a test inutili

## Regola d'oro

Un test deve fallire per un motivo chiaro e specifico. Se non sai cosa stai testando, non scriverlo.
