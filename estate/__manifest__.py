{
    'name': 'Estate',
    'version': '1.0',
    'license': 'LGPL-3',
    'category': '',
    'summary': 'Estate module for training purpouse',
    'depends': ['base'],
    
    'web_app_name': 'Real Estate', 
    'web_icon': 'estate,static/description/icon.png',
    'application': True,
    'sequence' : 1,
    'installable': True,
    
    'data': [
        'security/ir.model.access.csv',
        'data/estate.property.type.csv',
        'data/estate.property.tag.csv',
        'views/estate_property_offer_view.xml',
        'views/estate_property_tag_views.xml',
        'views/estate_property_type_views.xml',
        'views/estate_property_views.xml',
        'views/res_users_view.xml',
        'views/estate_menus.xml',
    ],
    'assets': {},
    'author': 'Simone',
}