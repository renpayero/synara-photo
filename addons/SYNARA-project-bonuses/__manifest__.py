# -*- coding: utf-8 -*-
{
    'name': "SYNARA Project Bonuses",
    'summary': "Gestión de pagos por hitos y bonos para implementadores",
    'description': """
        Este módulo permite gestionar los pagos a los implementadores basados en hitos del proyecto.
        Incluye:
        - Pago inicial del hito basado en el porcentaje de avance.
        - Pago de bono por finalización temprana de hitos.
        - Integración con partes de horas para el cálculo del avance.
    """,
    'author': "HC Sinergia S.A.",
    'website': "https://www.hcsinergia.com",
    'category': 'Project',
    'version': '18.0.1.0.0',
    'depends': ['project', 'hr_timesheet', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/project_milestone_link_task_views.xml',
        'views/project_milestone_views.xml',
        'reports/milestone_report.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
