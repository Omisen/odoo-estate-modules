from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_compare
from dateutil.relativedelta import relativedelta


class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Estate Property Offer"
    _order = "price desc"

    # ----- Fields ------
    property_type_id = fields.Many2one(
        "estate.property.type",
        string="Type",
        related="property_id.property_type_id",
        store=True,
    )
    price = fields.Float()
    status = fields.Selection(
        selection=[
            ("new", "New"),
            ("refuse", "Offer Refused"),
            ("accept", "Offer Accepted"),
            ("sold", "Sold"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="new",
        copy=False,
        readonly=True,
    )
    partner_id = fields.Many2one("res.partner", required=True)
    property_id = fields.Many2one("estate.property", required=True)
    validity = fields.Integer(default=7)
    date_deadline = fields.Date(
        string="Deadline Date",
        compute="_computed_date_deadline",
        inverse="_inverse_date_deadline",
        copy=False,
    )
    property_status = fields.Boolean(compute="_compute_property_status", store=True)

    # ----- Constraints -----
    @api.constrains("price")
    def _check_price(self):
        for record in self:
            if record.price <= 0:
                raise ValidationError("Price must be greater than zero.")

    @api.constrains("validity", "date_deadline")
    def _check_validity(self):
        for record in self:
            if record.validity < 0 and record.date_deadline.day < record.create_date.day:
                raise ValidationError(
                    "Validity must be greater than zero and deadline date "
                    "must not be before the creation date."
                )

    # ----- Computed ------
    @api.depends("property_id.status")
    def _compute_property_status(self):
        for record in self:
            record.property_status = record.property_id.status != "offer_recieved"

    @api.depends("validity")
    def _computed_date_deadline(self):
        for record in self:
            base = record.create_date.date() if record.create_date else fields.Date.today()
            record.date_deadline = base + relativedelta(days=record.validity)

    def _inverse_date_deadline(self):
        for record in self:
            if record.create_date and record.date_deadline:
                record.validity = (record.date_deadline - record.create_date.date()).days

    # ----- Button actions -----
    def set_offer_to_refuse(self):
        for record in self:
            if record.property_id.status in ["offer_accepted", "sold", "cancelled"]:
                raise UserError("Cannot refuse an offer on an accepted, sold, or cancelled property.")
            record.status = "refuse"
        return True

    def set_offer_to_accept(self):
        for record in self:
            if record.property_id.status in ["offer_accepted", "sold", "cancelled"]:
                raise UserError("An offer has already been finalized for this property.")
            other_offers = record.property_id.offer_ids.filtered(
                lambda offer: offer.id != record.id and offer.status != "refuse"
            )
            other_offers.write({"status": "cancelled"})
            record.status = "accept"
            record.property_id.buyer = record.partner_id.name
            record.property_id.selling_price = record.price
            record.property_id.status = "offer_accepted"
        return True

    # ----- CRUD ------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            prop = self.env["estate.property"].browse(vals.get("property_id"))
            offer_price = vals.get("price", 0)

            if prop.status in ["offer_accepted", "sold", "cancelled"]:
                raise ValidationError(
                    "Cannot create a new offer for a property that is accepted, sold, or cancelled."
                )

            if prop.expected_price and prop.selling_price:
                min_price = prop.expected_price * 0.90
                if float_compare(prop.selling_price, min_price, precision_digits=2) < 0:
                    raise ValidationError(
                        f"Selling Price [{prop.selling_price:.2f}] can't be lower "
                        f"than 90% of Expected Price [{min_price:.2f}]."
                    )

            best_price = max(prop.offer_ids.mapped("price"), default=0)
            if offer_price < best_price:
                raise ValidationError(
                    f"Cannot create offer with price {offer_price:.2f}.\n"
                    f"Best existing offer is {best_price:.2f}."
                )

            prop.status = "offer_recieved"

        return super().create(vals_list)
