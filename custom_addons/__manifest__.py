{
    'name': 'Orphan Sponsorship',
    'version': '17.0.1.0.0',
    'summary': 'Manage orphan sponsorships and auto-assign donors',
    'category': 'Social',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/orphan_views.xml',
        'views/donor_views.xml',
        'views/demo_panel_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
}
