#region Imports
from odoo import models, fields
#endregion

class ResUsers(models.Model):
    _inherit = "res.users"
    
    #region -Res User Fields-
    property_ids = fields.One2many(
                                    "estate.property",
                                    "salesperson_id",
                                    string="Properties",
                                    domain="[('status', 'in', ['new', 'offer_recieved','sold'])]",
                                    )
    #endregion