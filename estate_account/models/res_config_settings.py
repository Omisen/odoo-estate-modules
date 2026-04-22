from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    
    estate_commission_rate = fields.Float(
        string="Commission Rate",
        config_parameter="estate_account.commission_rate",
        default= 0.06)