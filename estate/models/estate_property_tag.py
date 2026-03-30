from odoo import models,fields

class EstatePropertyTags(models.Model):
    _name = "estate.property.tag"
    _description = "Estate Property Tags"
    _order = "name"
    
    name = fields.Char(required=True)
    color = fields.Integer()