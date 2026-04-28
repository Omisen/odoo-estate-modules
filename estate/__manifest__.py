{
    # ------ Identity ------
    'name': 'Estate',
    'version': '1.0',
    'license': 'LGPL-3',

    'summary': 'Manage real estate properties, offers, and sales pipeline.',
    'description': 'Full real estate management: property listings, buyer offers, offer acceptance, and automated sold/cancelled status transitions. Includes kanban dashboard, tags, property types, and PDF reports.',
    'category': 'Real Estate',
    'author': 'Simone',

    # ------ Dependencies ------
    'depends': ['base', 'web', 'mail', 'website'],

    # ----- Application ------
    'application': True,
    'installable': True,
    'sequence': 1,
    'web_app_name': 'Real Estate',
    'web_icon': 'estate,static/description/icon.png',
    

    # ----- Data ------
    'data': [
        'security/estate_security.xml',
        'security/ir.model.access.csv',
        'data/estate_sequence.xml',
        'data/estate.property.type.csv',
        'data/estate.property.tag.csv',
        'data/estate_property.xml',
        'demo/estate.property.offer.xml',
        'report/estate_property_report.xml',
        'views/estate_property_offer_view.xml',
        'views/estate_property_tag_views.xml',
        'views/estate_property_type_views.xml',
        'views/estate_property_views.xml',
        'views/estate_dashboard_action.xml',
        'views/res_users_view.xml',
        'views/estate_menus.xml',
        # last order for websites views relative to the  frontend
        'views/website/website_templates.xml',
        'views/website/website_navbar.xml',
        'views/website/website_footer.xml',
    ],

    # ----- Assets -----
    'assets': {
        'web.assets_backend': [
            'estate/static/src/css/kanban.css',
            'estate/static/src/components/dashboard/dashboard.css',
            'estate/static/src/components/dashboard/dashboard.js',
            'estate/static/src/components/offer_count_badge_widget/offer_count_badge.css',
            'estate/static/src/components/offer_count_badge_widget/offer_count_badge.js',
            'estate/static/src/components/status_badge_widget/status_badge.css',
            'estate/static/src/components/status_badge_widget/status_badge.js',
            'estate/static/src/components/dashboard/dashboard.xml',
            'estate/static/src/components/offer_count_badge_widget/offer_count_badge.xml',
            'estate/static/src/components/status_badge_widget/status_badge.xml',
        ],
    },

}