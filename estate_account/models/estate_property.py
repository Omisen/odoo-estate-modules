from odoo import models
import logging

_logger = logging.getLogger(__name__)

class EstateProperty(models.Model):
    _inherit = ['estate.property']
    
    def set_status_to_sold(self):
        _logger.info(">>> estate_account: set_status_to_sold called")
        return super().set_status_to_sold()