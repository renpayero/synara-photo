# -*- coding: utf-8 -*-
# my_project_template_unlimited/models/project_project.py

from odoo import models, fields, _
from odoo.exceptions import UserError

class ProjectProject(models.Model):
    _inherit = 'project.project'

    def _create_template_tasks(self, project_id):
        # El método original tenía una verificación de len(self.template_task_ids) > 40
        # que levantaba un UserError.
        # Al sobrescribir el método y eliminar esa verificación, quitamos el límite.
        # Copiamos la lógica original pero sin la restricción.

        # Esta es la lógica original de Odoo (Odoo 17/18) sin la parte del límite.
        # SI Odoo cambia significativamente este método en el futuro, es posible que necesites
        # ajustar este código.

        if not self.template_task_ids:
            return

        # Prepare values for tasks creation
        tasks_to_create = []
        for template_task in self.template_task_ids:
            # Puedes ajustar qué campos de la plantilla se copian a la tarea
            # según tus necesidades, pero esto es lo básico.
            tasks_to_create.append({
                'name': template_task.name,
                'description': template_task.description,
                'project_id': project_id,
                'user_ids': template_task.user_ids.ids, # Asignar usuarios de la plantilla
                'tag_ids': template_task.tag_ids.ids, # Copiar etiquetas
                'priority': template_task.priority,
                'stage_id': template_task.stage_id.id, # Copiar etapa si existe y es válida
                'kanban_state': template_task.kanban_state,
                'date_deadline': template_task.date_deadline, # Esto suele ser irrelevante en plantillas a menos que uses una fecha base
                'sequence': template_task.sequence,
            })
        
        # Create the tasks
        self.env['project.task'].create(tasks_to_create)

        # Si el proyecto plantilla tenía un mensaje de éxito, podríamos mantenerlo,
        # pero para este override, nos enfocamos solo en el límite.
        # Si el método original hace algo más después, deberías incluirlo aquí.