from odoo import models, Command
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)

class EstateProperty(models.Model):
    _inherit = ['estate.property']
    
    def set_status_to_sold(self):
        # debug of the call to the function
        _logger.warning(">>> estate_account: set_status_to_sold called and [OPEN]")
        
        # remeber that move_type is a field selection inside account.move
        # look ref to (~/odoo18/odoo/addons/account/models/account_move.py)
        
        # for record in self:  <---- sobstitute of explicit loop with a comprehension that lists of dict
        self.env['account.move'].create([
                                            {
                                                'partner_id' : record.offer_ids.filtered(lambda o: o.status == 'accept')[0].partner_id.id,
                                                'move_type': 'out_invoice',
                                                # this is a one2many in account_moove that has to be called by Command 
                                                # and access to the create method to that model (account.move.line)
                                                'invoice_line_ids' : [Command.create({
                                                                                        'name': record.name,
                                                                                        'quantity': 1,
                                                                                        'price_unit': record.selling_price * 0.06,
                                                                                    })],
                                            }
                                            for record in self
                                        ])
        
        _logger.warning(">>> estate_account: set_status_to_sold [CLOSED]")
        
        return super().set_status_to_sold()
    
    