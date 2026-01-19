from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_manager = fields.Boolean(string="Es Gerente")
