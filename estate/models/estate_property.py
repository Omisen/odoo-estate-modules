from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_compare


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Estate Property"
    _order = "id desc"

    # ----- Fields ------
    name = fields.Char(required=True)
    property_type_id = fields.Many2one("estate.property.type", string="Property Type")
    property_tag_id = fields.Many2many("estate.property.tag", string="Tags")
    description = fields.Text(compute="_compute_offers_presence", store=True)
    bedrooms = fields.Integer(string="Rooms")
    living_area = fields.Integer(string="Living Area (sqm)")
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer(string="Garden Area (sqm)")
    garden_orientation = fields.Selection(
        selection=[
            ("north", "North"),
            ("west", "West"),
            ("south", "South"),
            ("east", "East"),
        ],
        string="Garden Orientation",
    )
    date_availability = fields.Date(
        string="Availability Date",
        default=fields.Date.context_today,
        required=True,
        help="Date from which the property is available",
        copy=False,
    )
    postcode = fields.Char()
    expected_price = fields.Float(required=True)
    offer_ids = fields.One2many("estate.property.offer", "property_id", string="Offers")
    total_area = fields.Integer(compute="_computed_total_areas", store=True, string="Total Area (sqm)")
    best_price = fields.Float(string="Best Offer", compute="_compute_best_price", store=True, readonly=True)
    status = fields.Selection(
        selection=[
            ("new", "New"),
            ("offer_recieved", "Offer Received"),
            ("sold", "Sold"),
            ("cancelled", "Cancelled"),
        ],
        default="new",
        readonly=True,
    )
    buyer = fields.Char(readonly=True)
    selling_price = fields.Float(readonly=True)
    salesperson_id = fields.Many2one(
        "res.users",
        string="Salesperson",
        default=lambda self: self.env.user,
    )
    offer_count = fields.Integer(string="Offer Count", compute="_compute_offer_count", store=True, readonly=True)

    # ----- Constraints -----
    @api.constrains("garden_area", "garden")
    def _check_garden_area(self):
        for record in self:
            if record.garden and record.garden_area <= 0:
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
    @api.depends("living_area", "garden_area")
    def _computed_total_areas(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area

    @api.depends("offer_ids.price")
    def _compute_best_price(self):
        for record in self:
            record.best_price = max(record.offer_ids.mapped("price"), default=0.0)


    @api.depends("offer_ids.partner_id.name")
    def _compute_offers_presence(self):
        for record in self:
            unique_names = list(set(record.offer_ids.mapped("partner_id.name")))
            record.description = f"Offer partners: {', '.join(unique_names)}"

    @api.onchange("garden")
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = "north"

    @api.depends("offer_ids")
    def _compute_offer_count(self):
        for record in self:
            record.offer_count = len(record.offer_ids)
            
    # ----- Button actions -----
    def set_status_to_sold(self):
        for record in self:
            if record.status == "cancelled":
                raise UserError("Cannot set a cancelled property to Sold.")
            if not record.offer_ids.filtered(lambda x: x.status == "accept"):
                raise UserError("At least one offer must be accepted before setting to Sold.")
            record.status = "sold"
        return True

    def set_status_to_cancel(self):
        for record in self:
            if record.status == "sold":
                raise UserError("Cannot cancel a sold property.")
            record.status = "cancelled"
        return True

    def reset_status(self):
        for record in self:
            if record.status in ("sold", "cancelled", "offer_recieved"):
                new_status = "offer_recieved" if record.offer_ids else "new"
                record.with_context(bypass_reset=True).write({"status": new_status})
            for offer in record.offer_ids.filtered(lambda x: x.status in ("accept", "refuse")):
                offer.status = "new"
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
            if record.status in ["sold", "cancelled"] and set(vals) & protected:
                raise UserError(
                    f"Cannot modify property '{record.name}' because it is in '{record.status}' state."
                )
        return super().write(vals)
