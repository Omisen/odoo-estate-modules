#region Imports
from odoo import models,fields
#endregion

class EstatePropertyTags(models.Model):
    _name = "estate.property.tag"
    _description = "Estate Property Tags"
    _order = "name"
    
    #region -Property Tag Fields-
    name = fields.Char(required=True)
    color = fields.Integer()
    #endregion