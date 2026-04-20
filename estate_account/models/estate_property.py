from odoo import models, Command
from odoo.exceptions import UserError


class EstateProperty(models.Model):
    _inherit = "estate.property"

    def set_status_to_sold(self):
        result = super().set_status_to_sold()

        for record in self:
            sold_offer = record.offer_ids.filtered(lambda offer: offer.status == "sold")[:1]
            if not sold_offer:
                raise UserError("No accepted offer was found for invoicing this property.")

            self.env["account.move"].create({
                "partner_id": sold_offer.partner_id.id,
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
            })

        return result

    