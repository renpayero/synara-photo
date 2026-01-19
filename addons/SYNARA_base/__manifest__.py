{
    'name': 'SYNARA Base',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Base module for SYNARA ERP customizations',
    'description': """
        This module provides base utilities for SYNARA ERP.
        Features:
        - Module Installer Wizard: Install modules from an XLSX file.
    """,
    'author': 'HC Sinergia S.A.',
    'website': 'https://www.hcsinergia.com',
    'depends': ['base'],
    'external_dependencies': {
        'python': ['openpyxl'],
    },
    'data': [
        'security/ir.model.access.csv',
        'wizard/module_installer_wizard_view.xml',
        'views/installation_log_view.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
