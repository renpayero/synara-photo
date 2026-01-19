# -*- coding: utf-8 -*-
# Copyright 2024 HC Sinergia S.A. <hola@hcsinergia.com>
# License LGPLv3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

{
    'name': "SYNARA Project Bonuses2",
    'summary': """Añade campos para la gestión de bonos de rendimiento en tareas de proyecto.""",
    'description': """
        Este módulo añade dos campos al modelo project.task (Tareas):
        1. x_bono_base: Valor base del bono, para cálculo.
        2. x_bono_final: Valor final del bono, para liquidación.
    """,
    'author': "HC sinergia S.A.",
    'website': "https://www.hcsinergia.com",
    'category': 'Project Management',
    'version': '18.0.1.0.0',
    
    # Dependencias: Este módulo solo funciona si el módulo base de proyectos está instalado.
    'depends': ['project', 'base_automation'],
    
    # Archivos de datos (vistas, seguridad, etc.)
    'data': [
        'data/automated_actions.xml',
        'data/reports_menu.xml',
        'views/project_task_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}