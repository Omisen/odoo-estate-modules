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