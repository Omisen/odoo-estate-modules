{
    # ------ Identity ------
    'name' : 'Estate Account',
    'version': '1.0',
    'license': 'LGPL-3',
    
    'category': 'Real Estate',
    'summary': 'Automatic invoicing for sold real estate properties.',
    'description': 'Extends the Estate module with accounting integration: generates a customer invoice upon property sale, including a configurable commission line and a fixed administrative fee. Commission rate is configurable from Odoo Settings.',
    'author': 'Simone',
    
    # ------ Dependencies ------
    'depends': ['estate', 'account'],
    
    # ----- Application ------
    'web_app_name': 'Estate Account',
    'application': True,
    'sequence': 2,
    'installable': True,
    
    # ----- Data ------
    'data': [
        'views/estate_property_views.xml',
        'views/res_config_settings_views.xml'
    ],
    
    # ----- Assets -----
    'assets': {},
}