# -*- coding: utf-8 -*-
from odoo import models


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    def get_base_url(self):
        """Prefer the configured web.base.url so we always keep HTTPS even behind HTTP proxies."""
        config_base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if config_base_url:
            return config_base_url.rstrip('/') + '/'
        return super().get_base_url()

    def _build_request_headers(self, method, endpoint, payload, **kwargs):
        headers = super()._build_request_headers(method, endpoint, payload, **kwargs)
        seller_token = kwargs.get('seller_access_token')
        if self.code == 'mercado_pago' and seller_token:
            headers = dict(headers or {})
            headers['Authorization'] = f'Bearer {seller_token}'
        return headers
