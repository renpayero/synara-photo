# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProjectMilestone(models.Model):
    _inherit = 'project.milestone'

    # --- CONFIGURACIÓN DEL BONO (Reglas del Juego) ---
    planned_date_start = fields.Datetime(
        string="Fecha Inicio Planificada (Límite Bono)",
        help="Si el objetivo se completa antes de esta fecha, se activa el bono."
    )
    
    x_bonus_percentage = fields.Float(
        string="% Bono Objetivo", 
        default=0.0,
        help="Porcentaje del valor de las tareas que se pagará si se cumple el objetivo (Ej: 10)."
    )

    # --- CÁLCULOS ---
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    x_total_objective_value = fields.Monetary(
        string="Valor Total Objetivo",
        compute='_compute_bonus_status',
        store=True,
        currency_field='currency_id'
    )
    
    x_total_bonus_payout = fields.Monetary(
        string="Total a Pagar (Bono)",
        compute='_compute_bonus_status',
        store=True,
        currency_field='currency_id'
    )

    x_bonus_status = fields.Selection([
        ('pending', 'En Progreso ⏳'),
        ('qualified', 'Califica para Bono 🟢'),
        ('failed', 'No Califica 🔴')
    ], string="Estado del Bono", compute='_compute_bonus_status', store=True, default='pending')

    @api.depends('task_ids', 'task_ids.x_task_value', 'task_ids.state', 'task_ids.date_last_stage_update', 'planned_date_start', 'x_bonus_percentage')
    def _compute_bonus_status(self):
        for milestone in self:
            tasks = milestone.task_ids
            
            # 1. Sumar valor base de las tareas
            total_val = sum(tasks.mapped('x_task_value'))
            milestone.x_total_objective_value = total_val
            
            if not tasks or not milestone.planned_date_start:
                milestone.x_bonus_status = 'pending'
                milestone.x_total_bonus_payout = 0.0
                continue

            # 2. Verificar si TODAS las tareas están cerradas
            # Estados de cierre: '1_done', '1_canceled'
            all_closed = all(t.state in ['1_done', '1_canceled'] for t in tasks)
            
            if not all_closed:
                milestone.x_bonus_status = 'pending'
                milestone.x_total_bonus_payout = 0.0
            else:
                # 3. Validar FECHAS (La fecha real de cierre vs Planificada del Objetivo)
                # Buscamos la fecha de cierre más tardía de todas las tareas
                last_update = max(tasks.mapped('date_last_stage_update') or [fields.Datetime.now()])
                
                # REGLA: Si terminamos todo ANTES de la fecha de inicio planificada del objetivo
                if last_update <= milestone.planned_date_start:
                    milestone.x_bonus_status = 'qualified'
                    # Calculo: Valor Total * (10 / 100)
                    milestone.x_total_bonus_payout = total_val * (milestone.x_bonus_percentage / 100.0)
                else:
                    milestone.x_bonus_status = 'failed'
                    milestone.x_total_bonus_payout = 0.0