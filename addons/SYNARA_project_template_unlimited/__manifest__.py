# -*- coding: utf-8 -*-
# my_project_template_unlimited/__manifest__.py

{
    'name': "Project Template Unlimited Tasks",
    'summary': """Removes the 40 task limit when creating projects from templates.""",
    'description': """
        This module overrides the default behavior of Odoo Project Templates
        to allow the creation of more than 40 tasks when a project is generated
        from a template.
    """,
    'author': "Tu Nombre o Compañía",
    'website': "http://www.yourcompany.com", # O tu sitio web
    'category': 'Project',
    'version': '1.0',
    'depends': ['project'], # Depende del módulo de proyectos estándar
    'data': [], # No necesitamos archivos de datos/vistas en este caso
    'installable': True,
    'application': False,
    'license': 'LGPL-3', # O la licencia que prefieras
}