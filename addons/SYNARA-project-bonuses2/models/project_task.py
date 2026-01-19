# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProjectTask(models.Model):
    _inherit = 'project.task'

    # --- VALOR DE LA TAREA ---
    x_task_value = fields.Monetary(
        string="Valor de la Tarea", 
        currency_field='company_currency_id', 
        default=0.0
    )
    
    company_currency_id = fields.Many2one(
        'res.currency', 
        related='company_id.currency_id', 
        readonly=True
    )

    # --- CAMPOS ESPEJO DEL HITO (Para Reportes) ---
    x_milestone_bonus_percentage = fields.Float(
        related='milestone_id.x_bonus_percentage',
        string="% Bono (Obj)",
        readonly=True,
        store=True
    )
    
    x_milestone_bonus_status = fields.Selection(
        related='milestone_id.x_bonus_status',
        string="Estado Bono",
        readonly=True,
        store=True
    )

    # --- CÁLCULO INDIVIDUAL (Lo que cobra Juan) ---
    x_final_bonus_payout = fields.Monetary(
        string="Pago Bono Individual", 
        compute='_compute_individual_payout', 
        store=True,
        currency_field='company_currency_id'
    )
    
    x_bonus_paid = fields.Boolean(string="¿Pagado?", default=False)

    @api.depends('x_task_value', 'x_milestone_bonus_status', 'x_milestone_bonus_percentage')
    def _compute_individual_payout(self):
        for task in self:
            # Si el Objetivo Califica...
            if task.x_milestone_bonus_status == 'qualified':
                # Pago = Valor de ESTA tarea * % del Objetivo
                # Ej: 100 * 10% = 10
                task.x_final_bonus_payout = task.x_task_value * (task.x_milestone_bonus_percentage / 100.0)
            else:
                task.x_final_bonus_payout = 0.0

    def action_toggle_bonus_paid(self):
        for task in self:
            task.x_bonus_paid = not task.x_bonus_paid