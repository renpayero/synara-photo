from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    synara_gemini_api_key = fields.Char(
        string="Google Gemini API Key",
        config_parameter='SYNARA_bill_import.gemini_api_key',
        help="API Key for Google Gemini integration"
    )
