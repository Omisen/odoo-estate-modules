from odoo import models, fields

class EstateProperty(models.Model):
    _inherit = ['estate.property']
    
    def set_status_to_sold(self):
        return super().set_status_to_sold()