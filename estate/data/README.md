# data/

Qui dentro vanno i CSV con dati preconfigurati da caricare all'installazione del modulo.

Non è obbligatoria. La usiamo quando vogliamo che l'utente trovi già dei dati pronti appena installa il modulo, ad esempio le tipologie di immobile già compilate.

Questi file vengono caricati ogni volta che facciamo `-i` o `-u` del modulo.

Se vogliamo invece dati solo per test e sviluppo, quelli li dovremmo mettere nella cartella `demo/` e dichiarati sotto la chiave `demo` nel manifest — così non vengono caricati in produzione.

Ricordati di dichiarare i file nel manifest sotto `data`:

```python
'data': [
    'security/ir.model.access.csv',
    'data/estate.property.type.csv',
]
```

[esempio demo]
```python
'demo' : [
    'demo/*.csv',
]
```

## Problemi riscontrati nel caricamento dei dati XML (`estate_property.xml`)

---

### Problema 1 — Float con separatori di migliaia
Odoo non accetta valori `Float` con virgole come separatore. Usa il numero senza virgole.

```xml
<!-- ❌ --> <field name="expected_price">1,600,000.00</field>
<!-- ✅ --> <field name="expected_price">1600000.00</field>
```

---

### Problema 2 — Boolean `False` come testo stringa
Senza `eval=`, il valore è una stringa. In Python `bool("False")` è `True` (stringa non vuota), quindi il campo viene impostato al contrario.

```xml
<!-- ❌ --> <field name="garage">False</field>
<!-- ✅ --> <field name="garage" eval="False"/>
```

---

### Problema 3 — Integer con decimale
I campi `fields.Integer` non accettano il punto decimale. Odoo tenta `int('100000.00')` e fallisce con `ValueError`.

```xml
<!-- ❌ --> <field name="garden_area">100000.00</field>
<!-- ✅ --> <field name="garden_area">100000</field>
```

---

### Problema 4 — Formato data errato
Nel contesto `eval` degli XML Odoo **non esiste** `Date` (è `fields.Date` dell'ORM). Per date fisse usa una stringa semplice `YYYY-MM-DD`; per date dinamiche usa `datetime` con `relativedelta`.

```xml
<!-- ❌ --> <field name="date_availability" eval="Date.to_date('02-02-2027')"/>
<!-- ✅ --> <field name="date_availability">2027-02-02</field>
<!-- ✅ --> <field name="date_availability" eval="(datetime.now() - relativedelta(days=21)).strftime('%Y-%m-%d')"/>
```

---

### Problema 5 — `write()` override bloccante durante `-u`
Senza `noupdate="1"`, ogni `-u estate` fa richiamare `write()` su tutti i record dell'XML. Se il model ha un override di `write()` che blocca la modifica su record con `status='cancelled'` o `status='sold'`, il modulo crasha ad ogni aggiornamento.

`noupdate="1"` carica i record **solo alla prima installazione** (`-i`), ignorandoli negli aggiornamenti successivi (`-u`).

```xml
<!-- ❌ --> <data>
<!-- ✅ --> <data noupdate="1">
```
