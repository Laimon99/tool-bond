# ROADMAP - Tool Bond Platform

## Obiettivo roadmap
Costruire un tool che funzioni sui file reali presenti in `../ex`, ma con architettura modulare gia pronta per essere riutilizzata su clienti diversi con customizzazioni separate.

Regola di esecuzione: **PoC first**. Prima far funzionare il prodotto, poi consolidare infrastruttura enterprise.

## Principi guida
- Prima valore reale: MVP funzionante su dataset attuale
- Modulare da subito: core e custom separati
- Zero fork per cliente: configurazioni e plugin
- PoC semplice: evitare overengineering (no profili/auth complessi in partenza)
- Audit e riproducibilita: livello minimo nel PoC, livello enterprise in fase successiva
- AI-assisted delivery: accelerare sviluppo con agenti IA, mantenendo quality gates umani

## Modello di prodotto (riuso)

### Core (stabile e riusabile)
- Ingestion dati (Excel/CSV)
- Manual input UI (form guidate)
- Validation layer
- Quant engine bond+FX
- Scenario manager
- Reporting base
- Persistenza minima PoC (file locali)

### Custom (variabile per cliente)
- Regole pricing specifiche
- Convenzioni (day count, calendar, settlement)
- Connector provider dati
- Form, campi e wizard input specifici
- Template report e branding
- Feature flags UI

## Struttura progetto target
```text
apps/
  web/                    # UI
  api/                    # orchestrazione
services/
  quant-engine/           # core di calcolo
  data-ingestion/         # parser file e mapping
storage/
  local/                  # persistenza file PoC
```

Evoluzione post-PoC:
- aggiunta worker async, DB, auth/RBAC, tenant-config, plugin per cliente.

## Note operative AI-assisted
- In ambito finance, i passaggi di validazione quant, sicurezza e accettazione business restano human-in-the-loop.
- Gli agenti IA accelerano implementazione, test generation, refactor e documentazione, ma non sostituiscono il sign-off funzionale.

## Fase 0 - Setup e allineamento
Obiettivo:
- Definire input/output ufficiali dell MVP
- Definire casi test basati sui file in `../ex`

Deliverable:
- schema dati iniziale
- checklist validazione file
- casi test canonici (attesi)

Done quando:
- il team finanza conferma che gli output attesi sono corretti e leggibili

## Fase 1 - MVP tecnico funzionante
Obiettivo:
- Tool funzionante end-to-end sui file reali

Scope:
- import guidato file
- inserimento manuale guidato da UI
- parser e validazioni
- calcolo NPV hedged bond TRY -> USD
- vista risultati e breakdown
- export report base
- persistenza locale semplice (file JSON/CSV)

Deliverable:
- prima versione usabile da utenti non tecnici
- test automatici base su calcolo e parser

Done quando:
- il team riesce a riprodurre i risultati principali senza usare Excel manuale

## Fase 2 - Qualita prodotto e UX enterprise
Obiettivo:
- migliorare esperienza utente e affidabilita

Scope:
- scenario comparison
- messaggi errore business-friendly
- tracciamento PoC migliorato (senza piattaforma auth completa)
- performance tuning su dataset reali

Deliverable:
- dashboard piu chiara
- report piu completi
- tracciabilita dei run

Done quando:
- utente finance e product riescono a spiegare output e ipotesi al cliente senza supporto tecnico

## Fase 3 - Skeleton multi-cliente
Obiettivo:
- estrarre il core riusabile e separare custom

Scope:
- introduzione database applicativo (PostgreSQL)
- introduzione auth/RBAC e profili
- tenant-config
- plugin interfaces (pricing, data, report)
- feature flags per moduli
- onboarding secondo tenant pilota

Deliverable:
- base platform riutilizzabile
- primo cliente configurato senza fork codice

Done quando:
- si attiva un nuovo cliente cambiando config/plugin, non riscrivendo il core

## Fase 4 - Industrializzazione e rollout
Obiettivo:
- readiness commerciale e operativa

Scope:
- CI/CD completo
- monitoraggio e alert
- security hardening
- packaging desktop opzionale (Tauri)

Deliverable:
- processo di delivery ripetibile
- runbook operativo

Done quando:
- rilascio stabile su piu clienti con effort ridotto

## KPI di successo
- tempo per creare un nuovo cliente ridotto drasticamente
- riduzione lavoro manuale Excel
- riproducibilita risultati (stesso input = stesso output)
- tempo medio di analisi e report inferiore al processo attuale

## Prossimo passo operativo consigliato
Partire subito da Fase 0/Fase 1 con un backlog tecnico minimo:
1. parser `Curve_swap.xlsx`
2. parser `Bond_curve.xlsx` e `Bond_tURCO.xlsx`
3. modulo `valuation_bond_fx`
4. endpoint API `run_valuation`
5. schermata web: scelta input (upload o manuale) -> validazione -> risultato -> export
6. persistenza locale PoC per input/output run
