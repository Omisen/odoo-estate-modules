from odoo import http
from odoo.http import request

class EstateWebsite(http.Controller):
    
    # GET --- routs ---
    @http.route('/properties', auth='public', website = True)
    def property_list(self, **kwargs):
        properties = request.env['estate.property'].sudo().search([
            ('status', 'not in', ['sold', 'cancelled'])
        ])
        return request.render('estate.website_property_list', {'properties': properties})
    
    @http.route('/properties/<int:property_id>', auth='public', website=True)
    def property_detail(self, property_id, **kwargs):
        prop = request.env['estate.property'].sudo().browse(property_id)
        if not prop.exists():
            return request.not_found()
        return request.render('estate.website_property_detail', {'property': prop})