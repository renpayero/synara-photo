# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.http import request


class FotoappAuthSignup(AuthSignupHome):
    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        """Validate that signup accepts terms before creating the user."""
        if request.httprequest.method == 'POST' and not kw.get('accept_terms'):
            qcontext = self.get_auth_signup_qcontext()
            qcontext.update(kw)
            qcontext['error'] = _("You must accept the Terms and Conditions to create an account.")
            return request.render('website_auth_signup.signup', qcontext)

        return super().web_auth_signup(*args, **kw)
