from odoo import models, Command


class EstateProperty(models.Model):
    _inherit = "estate.property"

    def set_status_to_sold(self):
        self.env["account.move"].create([
            {
                "partner_id": record.offer_ids.filtered(lambda o: o.status == "accept").partner_id.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    Command.create({
                        "name": record.name,
                        "quantity": 1,
                        "price_unit": record.selling_price * 0.06,
                    }),
                    Command.create({
                        "name": "Administrative fees",
                        "quantity": 1,
                        "price_unit": 100.00,
                    }),
                ],
            }
            for record in self
        ])

        return super().set_status_to_sold()

    