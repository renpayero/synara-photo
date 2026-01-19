# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProjectMilestone(models.Model):
    _name = 'project.milestone'
    _inherit = ['project.milestone', 'mail.thread', 'mail.activity.mixin']

    planned_date_start = fields.Date(string="Fecha de Inicio Planificada", tracking=True)
    planned_date_end = fields.Date(string="Fecha de Fin Planificada", tracking=True)
    
    currency_id = fields.Many2one('res.currency', related='project_id.company_id.currency_id', string="Moneda", readonly=True)
    milestone_amount = fields.Monetary(string="Monto del Objetivo", currency_field='currency_id', tracking=True)
    
    user_id = fields.Many2one('res.users', string="Implementador Asignado", tracking=True)
    
    bonus_percentage = fields.Float(string="Porcentaje de Bono", help="Porcentaje del monto del objetivo a pagar como bono si se completa antes de tiempo.", tracking=True)
    required_progress_percentage = fields.Float(string="% Avance Requerido para Pago Inicial", default=10.0, tracking=True)
    
    payment_status = fields.Selection([
        ('draft', 'Borrador'),
        ('to_pay', 'A Pagar'),
        ('paid', 'Pagado')
    ], string="Estado Pago Inicial", default='draft', copy=False, tracking=True)
    
    bonus_payment_status = fields.Selection([
        ('draft', 'Borrador'),
        ('to_pay', 'A Pagar'),
        ('paid', 'Pagado'),
        ('not_eligible', 'Fuera de Plazo')
    ], string="Estado Pago Bono", default='draft', copy=False, tracking=True)
    
    total_planned_hours = fields.Float(compute='_compute_hours_and_progress', string="Total Horas Planificadas", store=True)
    total_effective_hours = fields.Float(compute='_compute_hours_and_progress', string="Total Horas Reales", store=True)
    progress_percentage = fields.Float(compute='_compute_hours_and_progress', string="Porcentaje de Avance", store=True)
    
    task_ids = fields.One2many('project.task', 'milestone_id', string="Tareas")
    
    bonus_amount = fields.Monetary(compute='_compute_bonus_amount', string="Monto del Bono", currency_field='currency_id', store=True)
    total_milestone_cost = fields.Monetary(compute='_compute_total_cost', string="Costo Total del Objetivo", currency_field='currency_id', store=True)

    @api.depends('milestone_amount', 'bonus_percentage')
    def _compute_bonus_amount(self):
        for milestone in self:
            milestone.bonus_amount = milestone.milestone_amount * (milestone.bonus_percentage / 100)

    @api.depends('milestone_amount', 'bonus_amount', 'bonus_payment_status')
    def _compute_total_cost(self):
        for milestone in self:
            cost = milestone.milestone_amount
            if milestone.bonus_payment_status == 'paid':
                cost += milestone.bonus_amount
            milestone.total_milestone_cost = cost

    @api.depends('task_ids.allocated_hours', 'task_ids.effective_hours')
    def _compute_hours_and_progress(self):
        for milestone in self:
            tasks = milestone.task_ids
            total_planned = sum(tasks.mapped('allocated_hours'))
            total_effective = sum(tasks.mapped('effective_hours'))
            
            milestone.total_planned_hours = total_planned
            milestone.total_effective_hours = total_effective
            
            if total_planned > 0:
                milestone.progress_percentage = (total_effective / total_planned) * 100
            else:
                milestone.progress_percentage = 0.0
                
            # Check for start payment eligibility automatically
            # Allow reverting to draft if progress drops below requirement AND it hasn't been paid yet.
            if milestone.payment_status != 'paid':
                if milestone.progress_percentage >= milestone.required_progress_percentage:
                    milestone.payment_status = 'to_pay'
                else:
                    milestone.payment_status = 'draft'

    def write(self, vals):
        res = super(ProjectMilestone, self).write(vals)
        for milestone in self:
            # Re-evaluate start payment if required_progress_percentage changes
            if 'required_progress_percentage' in vals:
                if milestone.payment_status != 'paid':
                    if milestone.progress_percentage >= milestone.required_progress_percentage:
                        milestone.payment_status = 'to_pay'
                    else:
                        milestone.payment_status = 'draft'

            # Re-evaluate bonus eligibility if is_reached changes or date changes
            if 'is_reached' in vals or 'deadline' in vals or 'planned_date_start' in vals or 'planned_date_end' in vals:
                if milestone.is_reached:
                    # Check if all tasks are done
                    tasks = milestone.task_ids
                    
                    completion_date = milestone.deadline or fields.Date.today()
                    # Check against Planned End Date (inclusive) for Early Completion Bonus
                    if milestone.planned_date_end and completion_date <= milestone.planned_date_end:
                        if milestone.bonus_payment_status != 'paid':
                            milestone.bonus_payment_status = 'to_pay'
                    else:
                        if milestone.bonus_payment_status != 'paid':
                            milestone.bonus_payment_status = 'not_eligible'
                else:
                    # If milestone is no longer reached, revert bonus status if not paid
                    if milestone.bonus_payment_status != 'paid':
                        milestone.bonus_payment_status = 'draft'
                        
        return res
    
    def action_mark_start_payment_paid(self):
        self.ensure_one()
        self.payment_status = 'paid'
        
    def action_mark_bonus_payment_paid(self):
        self.ensure_one()
        self.bonus_payment_status = 'paid'
