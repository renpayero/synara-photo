import base64
import io
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import openpyxl
except ImportError:
    _logger.warning("openpyxl library not found. Please install it using 'pip install openpyxl'")

class SynaraModuleInstallerLine(models.TransientModel):
    _name = 'synara.module.installer.line'
    _description = 'Module Installer Line'
    _order = 'status, name'

    wizard_id = fields.Many2one('synara.module.installer.wizard', string='Wizard', ondelete='cascade')
    name = fields.Char(string='Module Name', required=True)
    status = fields.Selection([
        ('installed', 'Installed'),
        ('to_install', 'To Install'),
        ('missing', 'Missing')
    ], string='Status', required=True)

class SynaraModuleInstallerWizard(models.TransientModel):
    _name = 'synara.module.installer.wizard'
    _description = 'Install Modules from XLSX'

    excel_file = fields.Binary(string='Excel File', required=True, help="Upload an XLSX file with module technical names in the first column.")
    file_name = fields.Char(string='File Name')
    
    state = fields.Selection([('draft', 'Draft'), ('review', 'Review')], default='draft', string='Status')
    
    line_ids = fields.One2many('synara.module.installer.line', 'wizard_id', string='Modules')

    def action_analyze_file(self):
        self.ensure_one()
        if not self.excel_file:
            raise UserError(_("Please upload an Excel file."))

        try:
            file_content = base64.b64decode(self.excel_file)
            workbook = openpyxl.load_workbook(io.BytesIO(file_content), data_only=True)
            sheet = workbook.active
            
            # Clear existing lines
            self.line_ids.unlink()
            
            lines_to_create = []
            
            # Iterate through rows, assuming column A contains module names
            # Start from row 2 to skip header
            for row in sheet.iter_rows(min_row=2, max_col=1, values_only=True):
                module_name = row[0]
                
                # Stop if we encounter an empty cell or non-string value
                if not module_name or not isinstance(module_name, str) or not module_name.strip():
                    break
                    
                module_name = module_name.strip()
                
                # Skip header if it matches common names (case insensitive)
                if module_name.lower() in ['technical name', 'nombre técnico', 'nombre tecnico', 'module name', 'módulo', 'modulo', 'name']:
                    continue
                        
                module = self.env['ir.module.module'].search([('name', '=', module_name)], limit=1)
                if module:
                    if module.state == 'installed':
                        status = 'installed'
                    else:
                        status = 'to_install'
                else:
                    status = 'missing'
                
                lines_to_create.append({
                    'wizard_id': self.id,
                    'name': module_name,
                    'status': status,
                })
            
            if lines_to_create:
                self.env['synara.module.installer.line'].create(lines_to_create)
            
            self.write({'state': 'review'})
            
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'synara.module.installer.wizard',
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'new',
            }

        except Exception as e:
            _logger.error(f"Error processing Excel file: {str(e)}")
            raise UserError(_(f"Error processing Excel file: {str(e)}"))

    def action_generate_report(self):
        self.ensure_one()
        
        # Create installation log
        log_lines = []
        for line in self.line_ids:
            log_lines.append({
                'name': line.name,
                'status': line.status,
            })
            
        log = self.env['synara.installation.log'].create({
            'line_ids': [(0, 0, val) for val in log_lines]
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'synara.installation.log',
            'view_mode': 'form',
            'res_id': log.id,
            'target': 'current',
        }
