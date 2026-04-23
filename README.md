# Estate Modules

Two Odoo 18 modules built for learning purposes:
- **Estate** — full real estate management: listings, offers, property types and tags, OWL dashboard, custom widgets, PDF report.
- **Estate Account** — extends Estate to auto-generate a customer invoice draft on sale and expose an "Open Invoice" button.

---

## Structure

```
estate/
├── models/
│   ├── estate_property.py        # core model
│   ├── estate_property_offer.py  # offers
│   ├── estate_property_type.py   # property types
│   ├── estate_property_tag.py    # tags
│   └── res_users.py              # user extension
├── views/                        # list, form, kanban, search, menus
├── security/ir.model.access.csv
├── data/                         # seed: types, tags, properties, sequence
├── demo/                         # demo offers
├── report/                       # QWeb PDF report
└── static/src/components/
    ├── dashboard/                # OWL dashboard (client action)
    ├── status_badge_widget/      # custom status badge
    └── offer_count_badge_widget/ # offer counter badge

estate_account/
├── models/estate_property.py     # _inherit: invoice creation on sale
└── views/estate_property_views.xml  # adds "Open Invoice" button
```

---

## Models

### `estate.property`
Core listing model. Key fields: `name`, `status`, `expected_price`, `selling_price`, `buyer`, `best_price` (computed), `offer_count` (computed), `total_area` (computed), `offer_ids`, `property_type_id`, `property_tag_id`, `salesperson_id`, `ref` (sequence).

**Constraints:** `expected_price > 0`, `garden_area > 0` when garden enabled, `selling_price >= expected_price × 90%`.

**CRUD overrides:**
- `unlink()` — blocked unless status is `new` or `cancelled`.
- `write()` — structural fields locked when `offer_accepted / sold / cancelled`; bypassable via `context['bypass_reset']`.

### `estate.property.offer`
One offer per record. `price`, `partner_id`, `validity`, `date_deadline` (compute + inverse), `status`.

**`create()`** checks: property not closed, new price ≥ best existing offer, auto-sets property to `offer_recieved`.

**Actions:** `set_offer_to_accept()` (refuses all others, sets buyer/selling_price), `set_offer_to_refuse()`.

### `estate.property.type`
Category with drag-handle sequence. Smart button shows filtered offer count.

### `estate.property.tag`
Name + color index used by `many2many_tags` widget.

### `res.users` (extension)
Adds `property_ids` One2many — shows assigned properties (excluding cancelled) on the user form.

---

## State Machine

```
[new] → [offer_recieved] → [offer_accepted] → [sold]
                ▲                  │
                └── reopen_offers()┘
[any] → [cancelled] → reopen_offers() → [offer_recieved]
```

- Cannot sell without an accepted offer.
- Cannot cancel a sold property.
- Structural fields are write-protected from `offer_accepted` onward.
- `unlink` allowed only in `new` / `cancelled`.

---

## Security

All internal users (`base.group_user`) have full CRUD on all four models. No record rules — learning project. Debug-only menu items (dashboard, all offers) are restricted to `base.group_no_one`.

---

## OWL Components

| Component | Registry key | Purpose |
|---|---|---|
| `EstateDashboard` | client action | KPIs + charts loaded via `Promise.all` ORM queries |
| `StatusBadgeWidget` | `estate_status_badge` | Colored badge for `status` field in form header |
| `OfferCountBadgeWidget` | `estate_offer_count_badge` | Singular/plural offer counter in form header |

---

## PDF Report

Triggered by "Preview Report" button (visible when `sold`). Contains property info, pricing, and full offer table. Uses an `AbstractModel` bridge to pass the recordset to the QWeb template.

---

## Data

| File | Type | Content |
|---|---|---|
| `estate.property.type.csv` | seed | Initial property types |
| `estate.property.tag.csv` | seed | Initial tags with colors |
| `estate_property.xml` | seed | Sample properties |
| `estate_sequence.xml` | seed (`noupdate=1`) | `ir.sequence` for `PROP/YYYY/NNNN` refs |
| `estate.property.offer.xml` | demo | Sample offers |

---

## estate_account

Extends `estate.property` via `_inherit`. When `set_status_to_sold()` runs:
1. Calls `super()` (base estate logic).
2. Creates a draft `out_invoice` with two lines: agent commission (6% of selling price) + admin fee (€100).
3. Stores the reference in `invoice_id` (Many2one → `account.move`).

An "Open Invoice" button (visible only when `sold`) opens the draft invoice via `action_open_invoice()`.
