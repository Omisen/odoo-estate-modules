{
    # ------ Identity ------
    'name': 'Estate',
    'version': '1.0',
    'license': 'LGPL-3',
    'category': '',
    'summary': 'Estate module for training purpouse',
    'author': 'Simone',

    # ------ Dependencies ------
    'depends': ['base'],

    # ----- Application ------
    'application': True,
    'installable': True,
    'sequence': 1,
    'web_app_name': 'Real Estate',
    'web_icon': 'estate,static/description/icon.png',
    

    # ----- Data ------
    'data': [
        'security/ir.model.access.csv',
        'data/estate.property.type.csv',
        'data/estate.property.tag.csv',
        'data/estate_property.xml',
        'demo/estate.property.offer.xml',
        'report/estate_property_report.xml',
        'views/estate_property_offer_view.xml',
        'views/estate_property_tag_views.xml',
        'views/estate_property_type_views.xml',
        'views/estate_property_views.xml',
        'views/res_users_view.xml',
        'views/estate_menus.xml',
    ],

    # ----- Assets -----
    'assets': {
        'web.assets_backend': [
            'estate/static/src/css/kanban.css',
        ],
    },

}