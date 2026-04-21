from odoo import fields, models, Command
from odoo.exceptions import UserError


class EstateProperty(models.Model):
    _inherit = "estate.property"

    invoice_id = fields.Many2one("account.move", string="Invoice", copy=False, readonly=True)

    def set_status_to_sold(self):
        result = super().set_status_to_sold()

        for record in self:
            sold_offer = record.offer_ids.filtered(lambda offer: offer.status == "sold")[:1]
            if not sold_offer:
                raise UserError("No accepted offer was found for invoicing this property.")

            invoice = self.env["account.move"].create({
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
            record.invoice_id = invoice

        return result

    def action_open_invoice(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Invoice",
            "res_model": "account.move",
            "res_id": self.invoice_id.id,
            "view_mode": "form",
            "target": "current",
        }

    