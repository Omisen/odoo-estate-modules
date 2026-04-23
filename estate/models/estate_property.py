from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_compare


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Estate Property"
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ----- Fields ------
    name = fields.Char(required=True)
    property_type_id = fields.Many2one("estate.property.type", string="Property Type")
    property_tag_id = fields.Many2many("estate.property.tag", string="Tags")
    description = fields.Text(string="Description")
    bedrooms = fields.Integer(string="Rooms")
    living_area = fields.Integer(string="Living Area (sqm)")
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer(string="Garden Area (sqm)")
    field_area = fields.Integer(string="Filed Area (sqm)")
    garden_orientation = fields.Selection(
        selection=[
            ("north", "North"),
            ("west", "West"),
            ("south", "South"),
            ("east", "East"),
            ("all_arround", "All Arround")
        ],
        string="Orientation",
    )
    date_availability = fields.Date(
        string="Availability Date",
        default=fields.Date.context_today,
        required=True,
        help="Date from which the property is available",
        copy=False,
    )
    postcode = fields.Char()
    expected_price = fields.Float(required=True, tracking=True)
    offer_ids = fields.One2many("estate.property.offer", "property_id", string="Offers")
    total_area = fields.Integer(
        compute="_computed_total_areas",
        store=True,
        string="Total Area (sqm)")
    best_price = fields.Float(
        string="Best Offer",
        compute="_compute_best_price",
        store=True,
        readonly=True)
    status = fields.Selection(
        selection=[
            ("new", "New"),
            ("offer_recieved", "Offer Received"),
            ("offer_accepted", "Offer Accepted"),
            ("sold", "Sold"),
            ("cancelled", "Cancelled"),
        ],
        default="new",
        readonly=True,
        tracking=True,
    )
    buyer = fields.Many2one(
        "res.partner",
        string="Buyer",
        readonly=True,
        copy=False,
        tracking= True,)
    selling_price = fields.Float(readonly=True, tracking=True)
    salesperson_id = fields.Many2one(
        "res.users",
        string="Salesperson",
        default=lambda self: self.env.user,
    )
    offer_count = fields.Integer(
        string="Offer Count",
        compute="_compute_offer_count",
        store=True,
        readonly=True)
    property_type_category = fields.Selection(related="property_type_id.category", store=False)
    
    # ----- Constraints -----
    @api.constrains("garden_area", "garden")
    def _check_garden_area(self):
        for record in self:
            if record.garden:
                if record.property_type_category == "land":
                    if record.field_area <= 0:
                        raise ValidationError("Field area must be greater than zero.")
                else:
                    if record.garden_area <= 0:
                        raise ValidationError("Garden area must be greater than zero.")

    @api.constrains("expected_price")
    def _check_expected_price(self):
        for record in self:
            if record.expected_price <= 0:
                raise ValidationError("Expected price must be greater than zero.")

    @api.constrains("selling_price", "expected_price")
    def _check_selling_price_minimum(self):
        for record in self:
            if record.selling_price and record.expected_price:
                min_allowed = record.expected_price * 0.90
                if float_compare(record.selling_price, min_allowed, precision_digits=2) < 0:
                    raise ValidationError(
                        f"Selling Price [{record.selling_price:.2f}] can't be lower "
                        f"than 90% of Expected Price [{min_allowed:.2f}]."
                    )

    # ----- Computed -----
    @api.depends("living_area", "garden_area", "field_area", "property_type_id.category")
    def _computed_total_areas(self):
        for record in self:
            category = record.property_type_category
            if category == "land":
                record.total_area = record.field_area
            elif category == "commercial":
                record.total_area = record.living_area
            else:
                record.total_area = record.living_area + record.garden_area

    @api.depends("offer_ids.price")
    def _compute_best_price(self):
        for record in self:
            record.best_price = max(record.offer_ids.mapped("price"), default=0.0)


    @api.onchange("garden")
    def _onchange_garden(self):
        if self.garden:
            if self.property_type_category == "land":
                self.field_area = 500
                self.garden_area = 0
                self.garden_orientation = "all_arround"
            else:
                self.garden_area = 100
                self.garden_orientation = "north"
        else:
            self.field_area = 0
            self.garden_area = 0
            self.garden_orientation = False

    @api.depends("offer_ids")
    def _compute_offer_count(self):
        for record in self:
            record.offer_count = len(record.offer_ids)

    # ----- Button actions -----
    def set_status_to_sold(self):
        for record in self:
            if record.status == "cancelled":
                raise UserError("Cannot set a cancelled property to Sold.")
            if record.status == "sold":
                raise UserError("This property is already sold.")

            accepted_offer = record.offer_ids.filtered(lambda offer: offer.status == "accept")[:1]
            if not accepted_offer:
                raise UserError("You must accept an offer before marking the property as sold.")

            accepted_offer.status = "sold"
            record.write({
                "buyer": accepted_offer.partner_id.id,
                "selling_price": accepted_offer.price,
                "status": "sold",
            })
        return True

    def set_status_to_cancel(self):
        for record in self:
            if record.status == "sold":
                raise UserError("Cannot cancel a sold property.")
            record.status = "cancelled"
            record.offer_ids.filtered(lambda offer: offer.status != "sold").write({"status": "cancelled"})
        return True

    #NOTE this is a reset button only for debug or testing purpouses in prod must be deleted or moved in test dir
    def action_reset_to_offer_received(self):
        for record in self:
            if record.status not in ("sold", "cancelled"):
                raise UserError(
                    "You can use this action only when the property is sold or cancelled."
                )

            record.offer_ids.write({"status": "new"})
            record.with_context(bypass_reset=True).write({
                "status": "offer_recieved",
                "buyer": False,
                "selling_price": 0.0,
            })
        return True

    def reopen_offers(self):
        for record in self:
            if record.status == "sold":
                raise UserError("You cannot reopen offers for a sold property.")
            if record.status not in ("offer_accepted", "cancelled"):
                raise UserError("Offers can only be reopened from accepted or cancelled status.")

            accepted_offer = record.offer_ids.filtered(lambda offer: offer.status == "accept")[:1]
            if not accepted_offer and record.buyer and record.selling_price:
                accepted_offer = record.offer_ids.filtered(
                    lambda offer: offer.partner_id == record.buyer
                    and float_compare(offer.price, record.selling_price, precision_digits=2) == 0
                )[:1]

            if accepted_offer:
                accepted_offer.status = "accept"

            record.offer_ids.filtered(
                lambda offer: offer != accepted_offer and offer.status in ("refuse", "cancelled")
            ).write({"status": "refuse"})

            record.with_context(bypass_reset=True).write({
                "status": "offer_recieved" if record.offer_ids else "new",
                "buyer": False,
                "selling_price": 0.0,
            })
        return True

    # ----- CRUD -----
    def unlink(self):
        for record in self:
            record.offer_ids.unlink()
        for record in self:
            if record.status not in ["new", "cancelled"]:
                raise UserError(
                    f"Cannot delete property '{record.name}' because it is in '{record.status}' state."
                )
        return super().unlink()

    def write(self, vals):
        protected = {
            "name", "expected_price", "postcode", "bedrooms",
            "living_area", "garage", "garden", "garden_area",
            "garden_orientation", "date_availability",
        }
        if self.env.context.get("bypass_reset"):
            return super().write(vals)
        for record in self:
            if record.status in ["offer_accepted", "sold", "cancelled"] and set(vals) & protected:
                raise UserError(
                    f"Cannot modify property '{record.name}' because it is in '{record.status}' state."
                )
        return super().write(vals)
