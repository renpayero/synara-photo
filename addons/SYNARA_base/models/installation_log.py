from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SynaraInstallationLog(models.Model):
    _name = 'synara.installation.log'
    _description = 'Module Installation Log'
    _order = 'date desc'

    date = fields.Datetime(string='Date', default=fields.Datetime.now, readonly=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft', string='Status', readonly=True)
    line_ids = fields.One2many('synara.installation.log.line', 'log_id', string='Modules', readonly=True)

    def action_execute_installation(self):
        self.ensure_one()
        to_install_lines = self.line_ids.filtered(lambda l: l.status == 'to_install')
        
        if not to_install_lines:
             # Just mark as done if nothing to install
             self.write({'state': 'done'})
             return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Modules to Install'),
                    'message': _('All modules are already installed or missing.'),
                    'type': 'info',
                    'sticky': False,
                    'next': {
                        'type': 'ir.actions.client',
                        'tag': 'reload',
                    }
                }
            }

        module_names = to_install_lines.mapped('name')
        modules = self.env['ir.module.module'].search([('name', 'in', module_names)])
        
        if modules:
            self.write({'state': 'done'})
            # Show notification before restart
            self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                'title': _('Installing Modules'),
                'message': _('The server will restart automatically to complete the installation. Please wait...'),
                'type': 'info',
                'sticky': True,
            })
            # This will install modules and restart the server
            return modules.button_immediate_install()

class SynaraInstallationLogLine(models.Model):
    _name = 'synara.installation.log.line'
    _description = 'Module Installation Log Line'

    log_id = fields.Many2one('synara.installation.log', string='Log', ondelete='cascade')
    name = fields.Char(string='Module Name', required=True)
    status = fields.Selection([
        ('installed', 'Installed'),
        ('to_install', 'To Install'),
        ('missing', 'Missing')
    ], string='Status', required=True)
