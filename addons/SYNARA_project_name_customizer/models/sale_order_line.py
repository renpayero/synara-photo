from odoo import models

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _timesheet_create_project(self):
        res = super()._timesheet_create_project()

        for line in self:
            project = line.project_id
            order = line.order_id
            if project and order.partner_id:
                partner = order.partner_id
                cuit = partner.vat or "SIN-CUIT"
                nombre = partner.name or "Sin nombre"
                solicitud = order.name or "SXXXXX"
                if "_" in project.name:
                    sufijo = project.name.split("_")[-1]
                else:
                    sufijo = "001"
                project.name = f"{solicitud} - {cuit} - {nombre}"

        return res
