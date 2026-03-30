from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_compare

class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Estate Property"
    _order = "id desc"
    # _sql_constraints = [
    # ("expected_price_positive", "CHECK(expected_price > 0)", "Expected price must be greater than zero"),
    # ]
    
    
    name = fields.Char(required=True)
    property_tag_id = fields.Many2many("estate.property.tag", string="Tags")
    description = fields.Text(compute="_compute_offers_presence", store= True) 
    bedrooms = fields.Integer()
    living_area = fields.Integer(string="Living Areas (sqm)")
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer(string="Garden Areas (sqm)")
    garden_orientation = fields.Selection(
        selection = [
          ('north', 'North'),
          ('west', 'West'),
          ('south', 'South'),
          ('east', 'East'),
        ],
        string = 'Garden Orientation',
    )
    date_availability = fields.Date(
        string = "Availability Date",
        default = fields.Date.context_today,
        required = True,
        help = "Date from which the property is available",
        copy = False,
    )
    postcode = fields.Char()
    expected_price = fields.Float(required=True)
    
    # collegamento al child estate.property.offer
    offer_ids = fields.One2many("estate.property.offer", "property_id", string="Offers")
    
    # applied comuted methods to fileds
    total_area = fields.Integer(compute="_computed_total_areas", store= True, string="Total Areas (sqm)")
    
    best_price = fields.Float(  string="Best Offer",
                                compute="_compute_best_price",
                                store=True,
                                readonly=True)
    
    # field related to status that will be changed on button by function
    status = fields.Selection(  selection=[
                                            ('new', 'New'),
                                            ('sold', 'Sold'),
                                            ('cancelled', 'Cancelled'),
                                            ],
                                default="new", 
                                readonly=True)
    
    # filed of buyer and selling price both on readonly 
    buyer = fields.Char(readonly= True)
    selling_price = fields.Float(readonly= True)
    has_offer = fields.Boolean(compute="_comupte_has_offer", store = True)
    
    
    
    #METHODS -constraints-
    
    # garden area deve essere diversa da zero a compilazione dle form 
    @api.constrains("garden_area", "garden")
    def _check_garden_area(self):
        for record in self:
            if record.garden and record.garden_area <= 0:
                raise ValidationError("Garden area must be greater than zero !!!")
            
    # medesima cosa anche per price_expected deve essere diverso da 0.00
    @api.constrains("expected_price")
    def _check_expected_price(self):
        for record in self:
            if record.expected_price <= 0:
                raise ValidationError("Expected Price must be greather than zero !!!")
            
    # def check_offers(self):
    #     for record in self:
    #         for offer in record.offer_ids:
    #             offer.property_id
    #             offer.partner_id
    #             offer.price
    #             offer.status
    
    @api.constrains("selling_price", "expected_price")
    def _check_selling_price_minimum(self):
        for record in self:
            if record.selling_price and record.expected_price:
                min_allowed = record.expected_price * 0.90
                if float_compare(record.selling_price, min_allowed, precision_digits=2) < 0:
                    raise ValidationError(f"Selling Price [{record.selling_price:.2f}] can\'t be lower than 90% of Expected Price [{min_allowed:.2f}] ")
    
    
    # METHODS -computed-
    @api.depends("living_area", "garden_area")
    def _computed_total_areas(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area
    
    @api.depends("offer_ids.price")
    def _compute_best_price(self):
        for record in self:
            record.best_price = max(record.offer_ids.mapped("price"), default= 0.0)
            
    @api.depends("offer_ids.partner_id.name")
    def _compute_offers_presence(self):
        for record in self:
            unique_names = list(set(record.offer_ids.mapped("partner_id.name")))
            record.description = f"The Offer Partners names are: {', '.join(unique_names)}"
            
    @api.onchange("garden")
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = 'north'
    
    @api.depends("offer_ids.status")
    def _comupte_has_offer(self):
        for record in self:
            record.has_offer = True if any(s == 'new' for s in record.offer_ids.mapped('status')) and record.status == 'new' else False
    
    # METHODS -buttons in view-
    def set_status_to_sold(self):
        for record in self:
            if record.status == 'cancelled':
                raise UserError(r"Status is setted on Cancelled and can't be set to Sold")
            if not record.offer_ids.filtered(lambda x: x.status == 'accept'):
                raise UserError("At least one offer must be accepted before setting to Sold")
            else:
                record.status = 'sold'
        return True
    
    def set_status_to_cancel(self):
        for record in self:
            if record.status == 'sold':
                raise UserError(f"Status is set to: can not set to Cancelld")
            else:
                record.status = 'cancelled'
        return True
    
    # only for testing
    def reset_status(self):
        for record in self:
            if record.status in ('sold', 'cancelled'):
                record.status = 'new'
            for offer in record.offer_ids.filtered(lambda x: x.status in ('accept', 'refuse')):
                offer.status = 'new'
        return True
