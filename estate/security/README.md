# security/

Qui dentro va il file `ir.model.access.csv`.

Questo file è obbligatorio. Senza di esso Odoo non fa accedere a nessun modello del modulo e lancia errore

Il CSV definisce i permessi per ogni modello: chi può leggere, scrivere, creare ed eliminare record e se lasciamo il campo gruppo vuoto, il permesso vale per tutti gli utenti

## Ricordati di dichiararlo nel manifest sotto `data`:

```python
'data': [
    'security/ir.model.access.csv',
]
```