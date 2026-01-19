{
    'name': 'SYNARA Bill Import',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Import Vendor Bills using AI',
    'description': """
        This module allows users to upload vendor bills (PDF/Image) and uses OpenAI to extract information
        and create Vendor Bills in Odoo automatically.
    """,
    'author': 'HC Sinergia S.A.',
    'website': 'https://www.hcsinergia.com',
    'depends': ['account'],
    'external_dependencies': {
        'python': ['google.generativeai'],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'wizard/bill_import_wizard_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
