# Tool Bond Platform

## In breve
Tool Bond Platform e un prodotto per valutare investimenti in bond in valuta estera (es. bond in TRY) e capire il risultato finale in USD con copertura del rischio cambio.

Obiettivo pratico: trasformare file e analisi oggi sparsi in Excel/PDF in uno strumento unico, chiaro e ripetibile, usabile anche da team non tecnici.

Approccio attuale: **PoC first**. Prima facciamo funzionare bene il cuore del calcolo, poi aggiungiamo la base piattaforma (profili, auth, database completo multi-cliente).

## A chi serve
- Team finanza e investment
- Team product/design che deve spiegare il valore al cliente
- Team commerciale che prepara proposte e report

## Quale problema risolve
Oggi il processo tipico e:
- dati in piu file (storici bond, curve FX, documenti termsheet)
- passaggi manuali in Excel
- difficolta a riprodurre lo stesso risultato nel tempo

Il tool centralizza tutto e risponde a domande chiave:
- Quanto rende davvero il bond se copro il cambio?
- Quali ipotesi sto usando?
- Cosa cambia se modifico curve, prezzo o scenario?

## Cosa fara il primo MVP (sui file reali gia presenti)
Il primo MVP sara costruito per funzionare sui dataset attuali in `../ex`:
- `Bond_curve.xlsx`
- `bond_storico.xlsx`
- `Bond_tURCO.xlsx`
- `Curve_swap.xlsx`
- `FX POLLS_25-Feb-2026.xls.xlsx`
- `document.pdf`

Funzioni MVP:
1. Import guidato dei file
2. Inserimento manuale degli stessi dati da interfaccia (senza Excel)
3. Validazione automatica (date, colonne, valori mancanti, coerenza numerica)
4. Calcolo NPV in USD del bond TRY coperto FX
5. Breakdown leggibile dei risultati (cash flow, curva usata, ipotesi)
6. Export report (Excel/PDF)

Per il PoC non e previsto:
- sistema profili utenti completo;
- gestione auth/permessi enterprise;
- database complesso come prerequisito per partire.

## Come lo usera un utente non tecnico
1. Sceglie modalita input: upload file oppure inserimento manuale guidato
2. Controlla la schermata di validazione
3. Seleziona scenario (base o personalizzato)
4. Avvia il calcolo
5. Legge il risultato in dashboard + scarica il report

## Visione prodotto: piattaforma riciclabile per piu clienti
Il prodotto nasce con una struttura modulare:

### Core comune (riusabile)
- Motore di calcolo bond+FX
- Gestione scenari
- Input layer unificato (import file + inserimento manuale + API connector)
- Validazione dati
- Audit e tracciabilita
- Dashboard e report base

### Parti custom per cliente
- Regole di pricing specifiche
- Convenzioni e calendari
- Campi input, wizard e form specifici per cliente
- Template report personalizzati
- Integrazioni con provider o sistemi del cliente

Principio chiave: stesso scheletro, personalizzazioni separate. No fork del progetto per ogni cliente.

Nota: nel PoC alcune parti restano semplificate (ad esempio persistenza minima su file locali). Lo skeleton modulare viene comunque mantenuto per evolvere rapidamente alla versione piattaforma.

## Architettura (in parole semplici)
- Frontend web: interfaccia utente moderna
- Backend API: coordina dati e processi
- Motore quantitativo Python: esegue i calcoli finanziari
- Persistenza PoC: file locali JSON/CSV (semplice e veloce)
- Database (fase successiva): salva scenari, input, output e storico in modo enterprise

Stack tecnico PoC:
- Next.js + TypeScript (interfaccia)
- FastAPI (backend)
- Python quant engine (calcoli)

Stack evolutivo (dopo PoC):
- PostgreSQL/Timescale + Redis (dati e job)
- Auth/RBAC e funzioni multi-tenant

## Stato attuale
- Repo inizializzata
- Definizione funzionale e architetturale completata
- Prossimo passo: sviluppo MVP sui file reali + struttura multi-cliente

## Documento roadmap
La pianificazione completa e nel file [ROADMAP.md](./ROADMAP.md).
