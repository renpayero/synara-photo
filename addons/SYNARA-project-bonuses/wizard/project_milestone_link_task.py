from odoo import models, fields, api

class ProjectMilestoneLinkTask(models.TransientModel):
    _name = 'project.milestone.link.task'
    _description = 'Link Tasks to Milestone'

    milestone_id = fields.Many2one('project.milestone', string="Objetivo", required=True)
    project_id = fields.Many2one('project.project', related='milestone_id.project_id', string="Proyecto", readonly=True)
    
    task_ids = fields.Many2many('project.task', string="Tareas a Vincular", domain="[('project_id', '=', project_id), ('milestone_id', '!=', milestone_id)]")
    
    warning_message = fields.Html(string="Advertencia", compute='_compute_warning_message')
    
    @api.depends('task_ids')
    def _compute_warning_message(self):
        for wizard in self:
            msg = ""
            tasks_with_milestone = wizard.task_ids.filtered(lambda t: t.milestone_id)
            if tasks_with_milestone:
                msg = "<p class='text-warning'><strong>¡Atención!</strong> Las siguientes tareas ya están asignadas a otro objetivo y serán movidas:</p><ul>"
                for task in tasks_with_milestone:
                    msg += f"<li>{task.name} (Objetivo actual: {task.milestone_id.name})</li>"
                msg += "</ul>"
            wizard.warning_message = msg

    def action_link_tasks(self):
        self.ensure_one()
        if self.task_ids:
            self.task_ids.write({'milestone_id': self.milestone_id.id})
        return {'type': 'ir.actions.act_window_close'}
