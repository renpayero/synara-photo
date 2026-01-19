import base64
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
except ImportError:
    _logger.warning("Google Generative AI library not found. Please install it using 'pip install google-generativeai'")

class SynaraBillImportWizard(models.TransientModel):
    _name = 'synara.bill.import.wizard'
    _description = 'Import Vendor Bills with AI'

    file_ids = fields.Many2many('ir.attachment', string='Files', help='Upload PDF or Image files of vendor bills')

    def action_import_bills(self):
        self.ensure_one()
        api_key = self.env['ir.config_parameter'].sudo().get_param('SYNARA_bill_import.gemini_api_key')
        if not api_key:
            raise UserError(_("Please configure the Google Gemini API Key in Settings."))

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        for attachment in self.file_ids:
            self._process_file(model, attachment)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def _process_file(self, model, attachment):
        try:
            if attachment.mimetype not in ['image/jpeg', 'image/png', 'image/webp']:
                 _logger.warning(f"Skipping file {attachment.name}: Only images are supported in this version.")
                 return

            image_data = base64.b64decode(attachment.datas)
            
            prompt = """
            Extract the following information from this invoice and return it as a JSON object:
            - partner_name
            - invoice_date (YYYY-MM-DD)
            - invoice_number
            - total_amount
            - currency_code
            - lines (list of objects with description, quantity, unit_price, tax_percentage)
            
            If a field is missing, return null. Ensure the output is valid JSON.
            """
            
            response = model.generate_content([
                {'mime_type': attachment.mimetype, 'data': image_data},
                prompt
            ])

            content = response.text
            # Clean up markdown code blocks if present
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
                
            data = json.loads(content)
            self._create_invoice(data)

        except Exception as e:
            _logger.error(f"Error processing file {attachment.name}: {str(e)}")
            raise UserError(_(f"Error processing file {attachment.name}: {str(e)}"))

    def _create_invoice(self, data):
        partner_name = data.get('partner_name')
        partner = self.env['res.partner'].search([('name', 'ilike', partner_name)], limit=1)
        if not partner and partner_name:
            partner = self.env['res.partner'].create({'name': partner_name})
        
        if not partner:
            raise UserError(_("Could not identify or create vendor."))

        invoice_lines = []
        for line in data.get('lines', []):
            invoice_lines.append((0, 0, {
                'name': line.get('description', 'Product'),
                'quantity': line.get('quantity', 1),
                'price_unit': line.get('unit_price', 0),
                # Tax handling would be more complex in real life (matching existing taxes)
            }))

        self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': partner.id,
            'invoice_date': data.get('invoice_date'),
            'ref': data.get('invoice_number'),
            'invoice_line_ids': invoice_lines,
        })
