# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class FotoappPhotographerStatementWizard(models.TransientModel):
    _name = 'fotoapp.photographer.statement.wizard'
    _description = 'Generar comisiones por fotógrafo'

    period_month = fields.Date(
        string='Mes',
        required=True,
        default=lambda self: self._default_period_month(),
    )

    @api.model
    def _default_period_month(self):
        today = fields.Date.context_today(self)
        today_date = fields.Date.from_string(today)
        period_start = today_date.replace(day=1)
        return fields.Date.to_string(period_start)

    def action_generate_statements(self):
        self.ensure_one()
        if not self.period_month:
            raise UserError(_('Seleccioná un mes para calcular las comisiones.'))
        period_start = fields.Date.from_string(self.period_month)
        period_start = period_start.replace(day=1)
        period_end = (period_start + relativedelta(months=1)) - relativedelta(days=1)
        self.env['fotoapp.photographer.statement']._generate_commission_statements(period_start, period_end)
        self.env.user.notify_info(_('Se recalcularon las comisiones para %s.') % period_start.strftime('%Y-%m'))
        return {'type': 'ir.actions.act_window_close'}
