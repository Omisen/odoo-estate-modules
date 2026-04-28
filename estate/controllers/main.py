from odoo import http
from odoo.http import request

class EstateWebsite(http.Controller):
    
    # GET --- routs ---
    @http.route('/', auth='public', website=True)
    def home(self, **kwargs):
        Property = request.env['estate.property'].sudo()
        latest_properties = Property.search(
            [('status', 'not in', ['sold', 'cancelled'])],
            order='id desc', limit=3
        )
        total_available = Property.search_count([('status', 'not in', ['sold', 'cancelled'])])
        total_sold = Property.search_count([('status', '=', 'sold')])
        return request.render('estate.website_home', {
            'latest_properties': latest_properties,
            'total_available': total_available,
            'total_sold': total_sold,
        })
    
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