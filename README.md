# Modulo Estate — Documentazione Completa

> **Estate** è un modulo Odoo 18 sviluppato a scopo formativo che implementa un sistema di gestione immobiliare completo: annunci, offerte, tipologie e tag di proprietà, con dashboard OWL custom, widget personalizzati e report PDF.

---

## Indice

1. [Panoramica Generale](#1-panoramica-generale)
2. [Architettura e Struttura del Progetto](#2-architettura-e-struttura-del-progetto)
3. [Modelli (Backend Logic)](#3-modelli-backend-logic)
   - [EstateProperty](#31-estateproperty)
   - [EstatePropertyOffer](#32-estatepropertyoffer)
   - [EstatePropertyType](#33-estatepropertytype)
   - [EstatePropertyTag](#34-estatepropertytag)
   - [ResUsers (extension)](#35-resusers-extension)
4. [Flusso di Stato (State Machine)](#4-flusso-di-stato-state-machine)
5. [Sicurezza e Accessi](#5-sicurezza-e-accessi)
6. [Interfaccia Utente (UI/UX)](#6-interfaccia-utente-uiux)
   - [Viste della Proprietà](#61-viste-della-proprietà)
   - [Viste Offerta](#62-viste-offerta)
   - [Viste Tipo e Tag](#63-viste-tipo-e-tag)
   - [Menu e Navigazione](#64-menu-e-navigazione)
7. [Componenti OWL (Frontend)](#7-componenti-owl-frontend)
   - [Dashboard](#71-dashboard)
   - [StatusBadgeWidget](#72-statusbadgewidget)
   - [OfferCountBadgeWidget](#73-offercountbadgewidget)
8. [Report PDF](#8-report-pdf)
9. [Dati Predefiniti (Demo & Seed)](#9-dati-predefiniti-demo--seed)
10. [Scelte Architetturali](#10-scelte-architetturali)
11. [Diagramma Relazioni tra Modelli](#11-diagramma-relazioni-tra-modelli)

---

## 1. Panoramica Generale

| Attributo | Valore |
|---|---|
| Nome tecnico | `estate` |
| Versione | 1.0 |
| Licenza | LGPL-3 |
| Dipendenze | `base`, `web` |
| Tipo | Applicazione standalone (`application: True`) |
| App name | **Real Estate** |

Il modulo espone una voce di menu **Real Estate** nel backend Odoo e gestisce l'intero ciclo di vita di un annuncio immobiliare: dalla pubblicazione, alla raccolta e gestione delle offerte, fino alla vendita o alla cancellazione.

---

## 2. Architettura e Struttura del Progetto

```
estate/
├── __manifest__.py              # Definizione modulo, dipendenze, assets
├── __init__.py
├── models/
│   ├── estate_property.py       # Core: annuncio immobiliare
│   ├── estate_property_offer.py # Offerte sui singoli annunci
│   ├── estate_property_type.py  # Tipologia (es. Casa, Appartamento)
│   ├── estate_property_tag.py   # Tag liberi colorati
│   └── res_users.py             # Estensione utente: lista proprietà
├── views/
│   ├── estate_property_views.xml          # List, Form, Kanban, Search
│   ├── estate_property_offer_view.xml     # List e Form offerte
│   ├── estate_property_type_views.xml     # List e Form tipologie
│   ├── estate_property_tag_views.xml      # List e Form tag
│   ├── res_users_view.xml                 # Scheda utente estesa
│   ├── estate_dashboard_action.xml        # Action client per OWL dashboard
│   └── estate_menus.xml                   # Struttura menu
├── security/
│   └── ir.model.access.csv      # ACL (tutti gli utenti interni: CRUD completo)
├── data/
│   ├── estate.property.type.csv # Seed: tipologie iniziali
│   ├── estate.property.tag.csv  # Seed: tag iniziali
│   └── estate_property.xml      # Seed: proprietà di esempio
├── demo/
│   └── estate.property.offer.xml # Demo: offerte di esempio
├── report/
│   ├── estate_property_report.py  # AbstractModel per il report
│   └── estate_property_report.xml # Qweb template + record ir.actions.report
└── static/src/components/
    ├── dashboard/                 # OWL Dashboard completa
    ├── status_badge_widget/       # Widget campo Selection con stile custom
    └── offer_count_badge_widget/  # Widget contatore offerte
```

---

## 3. Modelli (Backend Logic)

### 3.1 EstateProperty

**Modello principale** (`estate.property`). Rappresenta un annuncio immobiliare.

#### Campi principali

| Campo | Tipo | Note |
|---|---|---|
| `name` | Char | Obbligatorio — titolo annuncio |
| `property_type_id` | Many2one → `estate.property.type` | Categoria |
| `property_tag_id` | Many2many → `estate.property.tag` | Tag colorati |
| `salesperson_id` | Many2one → `res.users` | Default: utente corrente |
| `status` | Selection | Macchina a stati (vedi §4) |
| `expected_price` | Float | Obbligatorio, > 0 |
| `selling_price` | Float | Readonly, valorizzato all'accettazione |
| `buyer` | Char | Readonly, valorizzato all'accettazione |
| `best_price` | Float | Computed (max tra le offerte) |
| `offer_count` | Integer | Computed e stored |
| `total_area` | Integer | Computed: `living_area + garden_area` |
| `offer_ids` | One2many → `estate.property.offer` | Offerte ricevute |
| `description` | Text | Computed (store=True): lista partner delle offerte |

#### Computed fields di rilievo

- **`_compute_best_price`** — dipende da `offer_ids.price`; usa `max()` con fallback `0.0`.
- **`_computed_total_areas`** — somma `living_area + garden_area`, stored per performance.
- **`_compute_offers_presence`** — genera una stringa descrittiva con i nomi univoci dei partner che hanno fatto offerta, stored su DB.
- **`_compute_offer_count`** — `len(offer_ids)`, stored.

#### Vincoli (`@api.constrains`)

| Vincolo | Regola |
|---|---|
| `_check_garden_area` | Se `garden=True` → `garden_area > 0` |
| `_check_expected_price` | `expected_price > 0` |
| `_check_selling_price_minimum` | `selling_price >= expected_price * 0.90` |

#### Onchange

- **`_onchange_garden`** — quando si attiva il giardino: imposta `garden_area=10` e `garden_orientation="north"` come valori predefiniti rapidi.

#### Azioni (Button)

| Metodo | Descrizione |
|---|---|
| `set_status_to_sold()` | Richiede un'offerta accettata → passa a `sold`, scrive `buyer` e `selling_price` |
| `set_status_to_cancel()` | Cancella la proprietà e tutte le offerte non vendute |
| `reopen_offers()` | Da `offer_accepted` o `cancelled`: riapre la negoziazione |
| `action_reset_to_offer_received()` | Debug only (`group_no_one`): reimposta tutto a `offer_recieved` |

#### Override CRUD

- **`unlink()`** — impedisce la cancellazione di proprietà non in stato `new` o `cancelled`.
- **`write()`** — blocca la modifica dei campi strutturali (nome, prezzo, caratteristiche fisiche) quando la proprietà è in stato `offer_accepted`, `sold` o `cancelled`. Bypassabile via context `bypass_reset=True` per le azioni interne di reset.

---

### 3.2 EstatePropertyOffer

**Modello offerta** (`estate.property.offer`). Ogni record è un'offerta su una proprietà.

#### Campi principali

| Campo | Tipo | Note |
|---|---|---|
| `price` | Float | Obbligatorio, > 0 |
| `partner_id` | Many2one → `res.partner` | Offerente, obbligatorio |
| `property_id` | Many2one → `estate.property` | Proprietà, obbligatorio |
| `property_type_id` | Many2one (related) | Tipo della proprietà, stored |
| `status` | Selection | `new/refuse/accept/sold/cancelled` |
| `validity` | Integer | Validità in giorni (default: 7) |
| `date_deadline` | Date | Computed + inverse da `validity` |
| `property_status` | Boolean | Computed: `True` se la proprietà NON è in `offer_recieved` |

#### Computed + Inverse

- **`_computed_date_deadline`** — `create_date + validity giorni` (usa `relativedelta`).
- **`_inverse_date_deadline`** — scrivendo la deadline: ricalcola `validity` in giorni.
- **`_compute_property_status`** — flag utile in vista per nascondere/mostrare i pulsanti accept/refuse.

#### Logica `create` (`@api.model_create_multi`)

Prima di creare un'offerta vengono eseguiti controlli:
1. La proprietà non deve essere in stato `offer_accepted`, `sold` o `cancelled`.
2. Il prezzo della nuova offerta deve essere ≥ della migliore offerta esistente.
3. La proprietà viene portata automaticamente in stato `offer_recieved`.

#### Azioni

| Metodo | Descrizione |
|---|---|
| `set_offer_to_accept()` | Rifiuta tutte le altre offerte, accetta questa, aggiorna `buyer` e `selling_price` sulla proprietà |
| `set_offer_to_refuse()` | Porta l'offerta in `refuse` se la proprietà è ancora in `offer_recieved` |

---

### 3.3 EstatePropertyType

**Modello categoria** (`estate.property.type`). Ordinato per nome, con handle di sequenza.

| Campo | Tipo | Note |
|---|---|---|
| `name` | Char | Obbligatorio |
| `sequence` | Integer | Ordine visuale (drag handle) |
| `property_ids` | One2many → `estate.property` | Proprietà di questa categoria |
| `offer_ids` | One2many → `estate.property.offer` | Tutte le offerte (via related) |
| `offer_count` | Integer | Computed: count delle offerte |

La form del tipo espone un **smart button** che naviga alla lista offerte filtrata per tipo (`domain="[('property_type_id', '=', active_id)]"`).

---

### 3.4 EstatePropertyTag

**Modello tag** (`estate.property.tag`). Semplice.

| Campo | Tipo | Note |
|---|---|---|
| `name` | Char | Obbligatorio |
| `color` | Integer | Indice colore Odoo (usato in `many2many_tags`) |

---

### 3.5 ResUsers (extension)

Estende `res.users` aggiungendo:

```python
property_ids = fields.One2many(
    "estate.property", "salesperson_id",
    domain="[('status', 'in', ['new', 'offer_recieved', 'offer_accepted', 'sold'])]"
)
```

Questo permette di visualizzare le proprietà assegnate a un agente direttamente nella sua scheda utente, escludendo le proprietà cancellate.

---

## 4. Flusso di Stato (State Machine)

La proprietà segue una macchina a stati con transizioni controllate:

```
        ┌─────────────────────────────────────────────────────┐
        │                                                     │
        ▼                                                     │
     [new]                                                    │
        │                                                     │
        │  (ricezione offerta, automatica in create offer)    │
        ▼                                                     │
  [offer_recieved] ◄──── reopen_offers() ────────────────┐   │
        │                                                 │   │
        │  (set_offer_to_accept su un'offerta)            │   │
        ▼                                                 │   │
  [offer_accepted] ────── reopen_offers() ───────────────┘   │
        │                                                     │
        │  (set_status_to_sold, richiede accepted offer)      │
        ▼                                                     │
     [sold] ─────── (non reversibile in produzione)           │
                                                              │
  [qualsiasi] ────── set_status_to_cancel() ──────────────►[cancelled]
                                     │
                                     └── reopen_offers()  ───►[offer_recieved]
```

**Regole chiave:**
- Non si può vendere senza un'offerta accettata.
- Non si può cancellare una proprietà già venduta.
- I campi strutturali sono bloccati in scrittura da `offer_accepted` in poi.
- La cancellazione (`unlink`) è consentita solo in stato `new` o `cancelled`.

---

## 5. Sicurezza e Accessi

Il file `ir.model.access.csv` assegna a **tutti gli utenti interni** (`base.group_user`) permessi CRUD completi su tutti e quattro i modelli:

| Modello | Read | Write | Create | Delete |
|---|---|---|---|---|
| `estate.property` | ✅ | ✅ | ✅ | ✅ |
| `estate.property.type` | ✅ | ✅ | ✅ | ✅ |
| `estate.property.tag` | ✅ | ✅ | ✅ | ✅ |
| `estate.property.offer` | ✅ | ✅ | ✅ | ✅ |

> Scelta formativa: nessun record rule o group differenziato. In produzione si aggiungerebbero ACL per separare agenti da manager.

Alcune voci di menu (dashboard OWL, lista offerte globale) sono visibili solo al gruppo `base.group_no_one` (modalità debug), funzionando da area riservata agli sviluppatori.

---

## 6. Interfaccia Utente (UI/UX)

### 6.1 Viste della Proprietà

**List View** — mostra le proprietà con badge colorato dello stato:
- 🔵 Blu → `offer_recieved`
- 🟡 Giallo → `offer_accepted`
- 🟢 Verde → `sold`
- 🔴 Rosso → `cancelled`

Le colonne visibili sono: stato, nome, tipo, CAP, prezzo atteso, data disponibilità.

**Form View** — struttura a sezioni:
- **Header**: bottoni contestuali (Mark as Sold, Cancel, Reopen Offers, Reset debug), badge conta offerte, badge stato.
- **Titolo**: nome proprietà + tag colorati + agente responsabile.
- **Property Details**: tipo, CAP, data disponibilità, area totale (dx: prezzi).
- **Notebook con 3 pagine**:
  - *Indoor*: camere, area abitabile, garage, descrizione generata.
  - *Outdoor*: giardino, area giardino (condizionale), orientamento.
  - *Offers*: lista inline delle offerte con pulsanti accept/refuse contestuali.

I campi strutturali sono `readonly` quando `status in ('offer_accepted', 'sold', 'cancelled')` — la UI riflette direttamente le protezioni backend.

**Kanban View** — raggruppata per `property_type_id` (non-draggable):
- Card: badge stato, nome in evidenza, prezzi contestuali (expected / best / selling in base allo stato).
- Footer: tag colorati.

**Search View** — ricerca per nome, CAP, agente, tipo. Filtri rapidi:
- My Properties (filtro per `salesperson_id = uid`)
- Available, Has Garden, Offer Accepted, Sold
- Ricerca per area (uguale / maggiore di)
- Group By: stato, agente, CAP

---

### 6.2 Viste Offerta

**List View** — ordinata per prezzo decrescente (`_order = "price desc"`):
- Riga rossa se `status == 'refuse'`, verde se `status == 'accept'`.
- Pulsanti Accept/Refuse inline con visibilità condizionale su `property_status`.

**Form View** — per editing diretto di un'offerta con stessi controlli.

Due action separate:
- `action_estate_property_offer` — filtrata per tipo (dalla form del tipo).
- `action_estate_property_offer_all` — tutte le offerte (debug only).

---

### 6.3 Viste Tipo e Tag

**Type Form** — ha smart button con contatore offerte. La tab mostra la lista delle proprietà legate (read-only, con colori per stato).

**Tag** — lista semplice con nome. Il colore è gestito via widget `many2many_tags` nelle viste della proprietà.

---

### 6.4 Menu e Navigazione

```
Real Estate (root)
├── Advertisements
│   ├── Properties          → list/form/kanban estate.property
│   └── Dashboard (debug)   → OWL component
└── Settings
    └── Estate
        ├── Types           → estate.property.type
        ├── Tags            → estate.property.tag
        └── All Offers (debug) → estate.property.offer
    └── General
        └── Odoo Settings
```

---

## 7. Componenti OWL (Frontend)

### 7.1 Dashboard

**File**: `static/src/components/dashboard/`

Componente OWL standalone registrato come **client action** (`estate.dashboard_action`) e accessibile dal menu Advertisements (solo modalità debug).

#### Architettura del componente

```
EstateDashboard (Component)
├── setup()
│   ├── useService("orm")        → query al DB
│   ├── useService("action")     → navigazione tra view
│   └── useState({ ... })        → stato reattivo
└── onWillStart(async)           → carica i dati prima del render
```

#### Dati caricati (in parallelo con `Promise.all`)

| Dato | Query |
|---|---|
| Proprietà `new` | `searchCount` su `estate.property` |
| Proprietà in offerta/accettate | `searchCount` stato `offer_recieved` + `offer_accepted` |
| Proprietà vendute | `searchCount` stato `sold` |
| Offerte pending | `searchCount` su `estate.property.offer` stato `new` |
| Prezzo medio di vendita | `searchRead` su proprietà sold + calcolo media |
| Trend prezzi offerte | `searchRead` su offerte, ordinato per `create_date` asc |

La currency viene letta dalla company corrente (`session.user_companies.current_company`) per formattare i prezzi con `formatCurrency`.

#### Pattern tecnici usati

- **`useState`** (equivalente di React state) → stato reattivo per il rendering.
- **`onWillStart`** → lifecycle hook per precaricamento asincrono dati.
- **`Promise.all`** → parallelizzazione delle query per minimizzare il tempo di caricamento.
- **Navigazione** → `actionService.doAction(...)` per aprire le viste Odoo dal dashboard.

---

### 7.2 StatusBadgeWidget

**File**: `static/src/components/status_badge_widget/`

Widget campo personalizzato per il campo `status` di `estate.property`. Registrato nel registry Odoo come `estate_status_badge`, supporta tipo `selection`.

#### Logica

```javascript
get value()      // legge il valore raw dal record
get label()      // risolve il valore tecnico in etichetta human-readable
                 // usando record.fields[name].selection
get badgeClass() // mappa il valore a una classe CSS specifica per colore
```

| Stato | Classe CSS |
|---|---|
| `new` | `o_estate_status_badge--new` |
| `offer_recieved` | `o_estate_status_badge--offer-recieved` |
| `offer_accepted` | `o_estate_status_badge--offer-accepted` |
| `sold` | `o_estate_status_badge--sold` |
| `cancelled` | `o_estate_status_badge--cancelled` |

Il widget viene usato nella form header con `widget="estate_status_badge"` e nella list view della proprietà con `widget="badge"` (Odoo built-in).

---

### 7.3 OfferCountBadgeWidget

**File**: `static/src/components/offer_count_badge_widget/`

Widget per il campo `offer_count` (Integer). Registrato come `estate_offer_count_badge`.

Mostra il numero di offerte con label singolare/plurale automatico:
- `1` → "1 Offer"
- `N` → "N Offers"

Visibile nell'header della form solo quando lo stato è tra `offer_recieved` e `offer_accepted`.

---

## 8. Report PDF

Il modulo include un report PDF (e anteprima HTML) stampabile dalla form di una proprietà venduta.

**Attivazione**: bottone "Preview Report" visibile solo quando `status == 'sold'`. Il PDF è disponibile anche dal menu Stampa (action binding su `estate.property`).

**Struttura del report** (template Qweb):

1. **Header** — Nome proprietà + CAP + badge stato.
2. **General Information** — Tipo, tag, agente, data disponibilità, prezzi (expected / best / selling), acquirente.
3. **Property Features** — Camere, aree, garage, giardino (condizionale).
4. **Offers** — Tabella con tutti i dettagli delle offerte (partner, prezzo, validità, deadline, stato).

Il `AbstractModel` `report.estate.report_property_estate_template` funge da bridge tra il record e il template, passando i `docs` (recordset `estate.property`).

---

## 9. Dati Predefiniti (Demo & Seed)

### Seed (caricati sempre all'installazione)

| File | Contenuto |
|---|---|
| `estate.property.type.csv` | Tipologie iniziali (es. House, Apartment, ...) |
| `estate.property.tag.csv` | Tag iniziali con colori |
| `estate_property.xml` | Proprietà di esempio |

### Demo (solo con dati demo attivi)

| File | Contenuto |
|---|---|
| `estate.property.offer.xml` | Offerte di esempio sulle proprietà demo |

---

## 10. Scelte Architetturali

### Computed fields con `store=True`

Campi come `best_price`, `offer_count`, `total_area` e `description` sono stored su DB. Questo migliora le performance di ricerca e filtraggio a discapito di un overhead in scrittura.

### Protezione a doppio livello (UI + Backend)

I campi vengono bloccati sia nella vista (`readonly="status in (...)"`) sia nel metodo `write()` del modello. Questo garantisce che nessuna chiamata RPC diretta possa aggirare le protezioni UI.

### Context `bypass_reset`

Per le operazioni interne di reset (reset a `offer_recieved`, riapertura offerte), le azioni passano `context={'bypass_reset': True}` prima di chiamare `write()`, bypassando il controllo di protezione in modo esplicito e tracciabile.

### Inverse field su `date_deadline`

Il campo `date_deadline` usa un meccanismo **compute + inverse**: si può impostare sia la validità in giorni (che calcola la data), sia la data direttamente (che ricalcola i giorni). Questo offre flessibilità UX senza duplicazione di dati.

### Ordine dei modelli

- `estate.property` → `_order = "id desc"` (più recenti prima)
- `estate.property.offer` → `_order = "price desc"` (offerte migliori in cima)
- `estate.property.type` e `estate.property.tag` → `_order = "name"` (alfabetico)

### OWL Dashboard come client action

Invece di una view standard, la dashboard è implementata come componente OWL registrato come `ir.actions.client`. Questo permette piena libertà nel layout, nelle query customizzate e nella navigazione, senza i vincoli delle view Odoo tradizionali.

### Widget custom vs badge nativo

- Nel **list view** il campo `status` usa il widget `badge` nativo Odoo (semplice, standard).
- Nel **form header** usa il widget `estate_status_badge` custom per avere pieno controllo visivo del badge di stato.

---

## 11. Diagramma Relazioni tra Modelli

```
res.users (Odoo built-in)
    │
    │ salesperson_id (Many2one)
    ▼
estate.property  ◄──────────────────────────────┐
    │                                            │
    │ property_type_id (Many2one)                │
    ▼                                            │
estate.property.type                             │
    │                                            │
    │ offer_ids (One2many, via related)           │
    ▼                                            │
estate.property.offer ──────────────────────────┘
    │  property_id (Many2one)
    │
    │ partner_id (Many2one)
    ▼
res.partner (Odoo built-in)

estate.property
    │
    │ property_tag_id (Many2many)
    ▼
estate.property.tag
```

---
