from odoo import models,fields,api
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from odoo.tools.float_utils import float_compare

class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Estate Property Offer"
    _order = "price desc"
    
    property_type_id = fields.Many2one("estate.property.type", string="Type", related="property_id.property_type_id", store=True)
    price = fields.Float()
    status = fields.Selection(  selection= [
                                            ('new', 'New'),
                                            ('refuse', 'Offer Refuse'),
                                            ('accept', 'Offer Accepted'),
                                            ('sold', 'Sold'),
                                            ('cancelled', 'Cancelled')
                                            ],
                              
                                copy= False,
                                readonly=True,
                                default= 'new',
                                string= "Status")
    
    partner_id = fields.Many2one("res.partner", required= True)
    
    # collegamento al model estate.property
    property_id = fields.Many2one("estate.property", required= True)
    
    validity = fields.Integer(default=7)
    date_deadline = fields.Date(
                                string = "Deadline Date",
                                compute="_computed_date_deadline",
                                inverse="_inverse_date_deadline",
                                copy = False,
                                )
    property_status = fields.Boolean(compute="_compute_property_status",store=True)

    
    @api.constrains("price")
    def _check_price(self):
        for record in self:
            if record.price <= 0:
                raise ValidationError("Price must be greather than zero !!! ")
            
    @api.constrains("validity", "date_deadline")
    def _check_validity(self):
        for record in self:
            if record.validity < 0 and record.date_deadline.day < record.create_date.day:
                raise ValidationError("Validity must be greather then zero and Check that\ndeadline date isn\'t below creation date !!!")
    
    
    @api.depends("property_id.status")
    def _compute_property_status(self):
        for record in self:
            record.property_status = True if record.property_id.status != 'offer_recieved' else False
    
    @api.depends("validity")
    def _computed_date_deadline(self):
        for record in self:
            # test con uso di una fallback in var temp 
            record.date_deadline = (temp := record.create_date.date() if record.create_date else fields.Date.today()) + relativedelta(days=record.validity)
    
    def _inverse_date_deadline(self):
        for record in self:
            if record.create_date and record.date_deadline:
                record.validity = (record.date_deadline - record.create_date.date()).days
    
    # METHODS -button view-
    def set_offer_to_refuse(self):
        for record in self:
            if record.property_id.status in ['sold', 'cancelled']:
                raise UserError("Cannot refuse an offer on a sold/cancelled property!")
            record.status = 'refuse'
        return True
    
    def set_offer_to_accept(self):
        for record in self:
            if record.property_id.status in ['sold', 'cancelled']:
                raise UserError("Cannot accept an offer on a sold/cancelled property!")
            record.status = 'accept'
            record.property_id.buyer = record.partner_id.name
            record.property_id.selling_price = record.price
            record.property_id.status = 'sold'
        return True
    
    # METHODS -api model create-
    @api.model_create_multi
    def create(self, vals_list):
        
        for vals in vals_list:
            property_id = vals.get('property_id')
            property = self.env['estate.property'].browse(property_id)
            
            # se ce il price se no fallback sul secondo argomento = 0
            offer_price = vals.get('price', 0)
            
            best_price = 0
            
            
            # checks on creation of che offers in the propperty.estate that offer price mus t be over the 90% of expected price
            if property.expected_price and property.selling_price:
                min_price = property.expected_price * 0.90
                if float_compare(property.selling_price, min_price, precision_digits=2) < 0:
                    raise ValidationError(f"Selling Price [{property.selling_price:.2f}] can\'t be lower than 90% of Expected Price [{min_price:.2f}] ")
                
            
            if property.offer_ids:
                best_price = max(offer.price for offer in property.offer_ids)
            
            if offer_price < best_price:
                raise ValidationError(
                    f"Cannot create offer with price {offer_price:.2f}.\n"
                    f"Best existing offer is {best_price:.2f}."
                )
            
            property.status = 'offer_recieved'
        
        # invia tutt al model pareent
        return super().create(vals_list)
    