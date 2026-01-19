{
    'name': 'Synara Contacts',
    'version': '1.0',
    'category': 'Contacts',
    'author': 'AI',
    'summary': 'Custom extensions for Contacts',
    'description': """
        This module adds custom fields to the Contacts module.
        - Adds 'Es Gerente' (is_manager) boolean field to contacts.
    """,
    'depends': ['base', 'contacts'],
    'data': [
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
