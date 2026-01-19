# -*- coding: utf-8 -*-
import base64
import io
from datetime import datetime
from collections import defaultdict

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class FotoappPhotographerStatement(models.Model):
    _name = 'fotoapp.photographer.statement'
    _description = 'Liquidaciones de fotógrafos'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'period_end desc, id desc'

    name = fields.Char(string='Referencia', required=True, copy=False, default=lambda self: _('Comisiones'))
    partner_id = fields.Many2one('res.partner', string='Fotógrafo', required=True, domain="[('is_photographer', '=', True)]")
    period_start = fields.Date(string='Periodo desde', required=True)
    period_end = fields.Date(string='Periodo hasta', required=True)
    period_month = fields.Char(string='Mes', compute='_compute_period_month', store=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id, required=True)
    commission_percent = fields.Float(string='Comisión aplicada (%)', default=0.0, help='Porcentaje total aplicado (plan + fee).')
    sale_total = fields.Monetary(string='Ventas brutas')
    commission_total = fields.Monetary(string='Total comisión')
    adjustment_total = fields.Monetary(string='Ajustes', help='Montos manuales positivos o negativos.')
    payout_total = fields.Monetary(string='Pago neto', compute='_compute_totals', store=True)
    payout_date = fields.Date(string='Fecha de pago')
    payment_reference = fields.Char(string='Referencia bancaria')
    line_ids = fields.One2many('fotoapp.photographer.statement.line', 'statement_id', string='Detalle')
    sale_count = fields.Integer(string='Cantidad de ventas', compute='_compute_totals', store=True)

    @api.depends('period_start')
    def _compute_period_month(self):
        for statement in self:
            if statement.period_start:
                statement.period_month = statement.period_start.strftime('%Y-%m')
            else:
                statement.period_month = False

    @api.depends('sale_total', 'commission_total', 'adjustment_total', 'line_ids.net_amount')
    def _compute_totals(self):
        for statement in self:
            sale_total = sum(statement.line_ids.mapped('sale_amount'))
            commission_total = sum(statement.line_ids.mapped('commission_amount'))
            net_total = sum(statement.line_ids.mapped('net_amount'))
            statement.sale_total = sale_total
            statement.commission_total = commission_total
            statement.sale_count = len(statement.line_ids)
            statement.payout_total = net_total + (statement.adjustment_total or 0.0)

    @api.model
    def cron_generate_monthly_commissions(self):
        today = fields.Date.context_today(self)
        first_day_current = today.replace(day=1)
        period_start = first_day_current - relativedelta(months=1)
        period_end = first_day_current - relativedelta(days=1)
        return self._generate_commission_statements(period_start, period_end)

    @api.model
    def _generate_commission_statements(self, period_start, period_end):
        if not period_start or not period_end:
            return False
        start_dt = datetime.combine(period_start, datetime.min.time())
        end_dt = datetime.combine(period_end, datetime.max.time())

        Order = self.env['sale.order'].sudo()
        orders = Order.search([
            ('fotoapp_photographer_id', '!=', False),
            ('state', 'in', ['sale', 'done']),
            ('date_order', '>=', fields.Datetime.to_string(start_dt)),
            ('date_order', '<=', fields.Datetime.to_string(end_dt)),
        ])

        paid_orders = orders.filtered(lambda o: any(tx.state == 'done' for tx in o.transaction_ids))
        if not paid_orders:
            return True

        grouped = defaultdict(list)
        for order in paid_orders:
            plan = order.fotoapp_plan_id
            commission_percent = order.fotoapp_commission_percent or (plan.commission_percent if plan else 0.0)
            fee_percent = plan.transaction_fee_percent if plan and plan.transaction_fee_percent else 0.0
            total_percent = (commission_percent or 0.0) + fee_percent
            for line in order.order_line.filtered(lambda l: l.foto_photographer_id):
                if not line.foto_asset_id:
                    continue
                sale_amount = line.price_total
                grouped[order.fotoapp_photographer_id.id].append({
                    'asset_id': line.foto_asset_id.id,
                    'album_id': False,
                    'sale_order_line_id': line.id,
                    'customer_id': order.partner_id.id,
                    'sale_date': order.date_order,
                    'sale_amount': sale_amount,
                    'commission_percent': total_percent,
                })

        for partner_id, line_payloads in grouped.items():
            partner = self.env['res.partner'].browse(partner_id)
            currency = paid_orders.filtered(lambda o: o.fotoapp_photographer_id.id == partner_id)[:1].currency_id or self.env.company.currency_id
            statement = self.search([
                ('partner_id', '=', partner_id),
                ('period_start', '=', period_start),
                ('period_end', '=', period_end),
            ], limit=1)
            commands = [fields.Command.create(payload) for payload in line_payloads]
            vals = {
                'name': _('Comisiones %(month)s - %(partner)s') % {
                    'month': period_start.strftime('%Y-%m'),
                    'partner': partner.display_name,
                },
                'partner_id': partner_id,
                'period_start': period_start,
                'period_end': period_end,
                'currency_id': currency.id,
                'line_ids': commands,
            }
            if statement:
                statement.write({'line_ids': [(5, 0, 0)] + commands, 'currency_id': currency.id})
            else:
                self.create(vals)
        return True

    @api.model
    def _prepare_export_rows(self, statements):
        rows = []
        for st in statements:
            rows.append([
                st.partner_id.display_name,
                st.period_month or '',
                st.sale_total or 0.0,
                st.commission_total or 0.0,
                st.payout_total or 0.0,
            ])
        return rows

    @api.model
    def _action_export_xlsx(self, active_ids=None, active_domain=None):
        domain = active_domain or []
        records = self.search(domain) if domain else self.browse(active_ids or [])
        if not records:
            records = self.search([])
        # Defensive import to avoid runtime errors if dependency is missing.
        try:
            import xlsxwriter
        except ImportError:
            raise UserError(_('No se encontró xlsxwriter para exportar a Excel.'))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Comisiones')
        header = ['Fotógrafo', 'Mes', 'Ventas brutas', 'Comisión', 'Neto fotógrafo']
        bold = workbook.add_format({'bold': True})
        money = workbook.add_format({'num_format': '#,##0.00'})

        for col, title in enumerate(header):
            sheet.write(0, col, title, bold)

        for row_idx, row in enumerate(self._prepare_export_rows(records), start=1):
            sheet.write(row_idx, 0, row[0])
            sheet.write(row_idx, 1, row[1])
            sheet.write_number(row_idx, 2, row[2], money)
            sheet.write_number(row_idx, 3, row[3], money)
            sheet.write_number(row_idx, 4, row[4], money)

        workbook.close()
        output.seek(0)
        data = output.read()
        filename = 'comisiones_fotoapp.xlsx'
        attachment = self.env['ir.attachment'].sudo().create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(data),
            'res_model': 'fotoapp.photographer.statement',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=1',
            'target': 'self',
        }


class FotoappPhotographerStatementLine(models.Model):
    _name = 'fotoapp.photographer.statement.line'
    _description = 'Detalle de liquidación de fotógrafo'
    _order = 'sale_date desc, id desc'

    statement_id = fields.Many2one('fotoapp.photographer.statement', required=True, ondelete='cascade')
    asset_id = fields.Many2one('tienda.foto.asset', string='Foto vendida', required=True)
    album_id = fields.Many2one('tienda.foto.album', string='Álbum relacionado')
    sale_order_line_id = fields.Many2one('sale.order.line', string='Línea de venta')
    customer_id = fields.Many2one('res.partner', string='Cliente final')
    sale_date = fields.Datetime(string='Fecha de venta')
    sale_amount = fields.Monetary(string='Venta bruta', currency_field='currency_id', required=True)
    commission_percent = fields.Float(string='Comisión aplicada (%)', default=0.0)
    commission_amount = fields.Monetary(string='Monto comisión', currency_field='currency_id', compute='_compute_net_amount', store=True)
    net_amount = fields.Monetary(string='Pago neto', currency_field='currency_id', compute='_compute_net_amount', store=True)
    currency_id = fields.Many2one('res.currency', related='statement_id.currency_id', store=True, readonly=True)

    @api.depends('sale_amount', 'commission_percent')
    def _compute_net_amount(self):
        for line in self:
            commission = (line.sale_amount or 0.0) * (line.commission_percent or 0.0) / 100.0
            line.commission_amount = commission
            line.net_amount = (line.sale_amount or 0.0) - commission
