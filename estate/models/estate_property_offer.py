from odoo import models,fields,api
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta

class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Estate Property Offer"
    _order = "price desc"
    
    property_type_id = fields.Many2one("estate.property.type", string="Type")
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
    
    @api.constrains("price")
    def _check_price(self):
        for record in self:
            if record.price <=0:
                raise ValidationError("Price must be greather than zero !!! ")
            
    @api.constrains("validity", "date_deadline")
    def _check_validity(self):
        for record in self:
            if record.validity < 0 and record.date_deadline.day < record.create_date.day :
                raise ValidationError("Validity must be greather then zero and Check that\ndeadline date isn\'t below creation date !!!")
    
    
    
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
    
    