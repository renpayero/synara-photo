# -*- coding: utf-8 -*-
"""
Guest checkout defaults for FotoApp.

This controller forces minimal address/billing data for anonymous carts so the
checkout can proceed with only email.
"""

import logging
import re

from odoo import http, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale.controllers.payment import PaymentPortal as WebsiteSalePaymentPortal

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_logger = logging.getLogger(__name__)


class FotoappWebsiteSale(WebsiteSale):
	@http.route(['/shop/address'], type='http', auth="public", website=True, sitemap=False)
	def address(self, **kw):
		order = request.website.sale_get_order()
		is_guest = self._fotoapp_is_guest_checkout(order)

		if request.httprequest.method == 'POST':
			return self.shop_address_submit(**kw)

		if is_guest and order and order.partner_id:
			return request.redirect('/shop/payment')

		# Llama a la implementación base de WebsiteSale (shop_address)
		return super().shop_address(**kw)
	
	def _fotoapp_is_guest_checkout(self, order_sudo):
		# Consider guest if the front-end user is public, even if the order already has a
		# dedicated partner (we assign one when capturing the guest email).
		return bool(order_sudo and (order_sudo._is_anonymous_cart() or request.env.user._is_public()))
	
	## esta funcion fue copiada y adaptada de website_sale/controllers/main.py
	## porque es la unica forma de modificar el comportamiento del checkout guest
	## sin modificar el core de odoo.
	## el objetivo es forzar ciertos campos en la direccion de facturacion
	def _first(self, model, domain, order=None):
		registry = request.env.registry
		if model not in registry:
			return request.env['res.partner'].browse()
		env = request.env.sudo()
		return env[model].search(domain, limit=1, order=order or 'id')

	def _fotoapp_validate_single_photographer(self, order_sudo):
		photo_lines = order_sudo.order_line.filtered(lambda l: l.foto_photographer_id)
		photographers = set(photo_lines.mapped('foto_photographer_id').ids)
		if len(photographers) > 1:
			request.session['website_sale_cart_warning'] = _(
				'No está permitido agregar fotos de varios fotógrafos al carrito. Separá los carritos por favor.'
			)
			return request.redirect('/shop/cart')
		return None


	def _validate_address_values(
		self,
		address_values,
		partner_sudo,
		address_type,
		use_delivery_as_billing,
		required_fields,
		is_main_address,
		**kwargs,
	):
		# VALORES POR DEFECTO PARA CHECKOUT DE INVITADOS
		data = {
				'name': 'Guest Buyer',
				'company_name': 'Guest Buyer',
				'city': 'Rosario',
				'zip': '2000',
				'phone': '2477610123',
				'vat': '43026589',
				'street': 'Calle falsa 123',
				'street2': '4-1',
				'consumidor_final': False,
				'dni_type': False,
				'country_id': False,
				'state_id': False,
			}
		order_sudo = request.website.sale_get_order()
		is_guest = self._fotoapp_is_guest_checkout(order_sudo)

		if is_guest:
			# BUSCAR LOS VALORES
			consumidor_final = request.env['l10n_ar.afip.responsibility.type'].search([('code', '=', '5')], limit=1)
			dni_type = request.env['l10n_latam.identification.type'].search([('name', '=', 'DNI')], limit=1)
			country_id = request.env['res.country'].search([('code', '=', 'AR')], limit=1)
			state_id = request.env['res.country.state'].search([('code', '=', 'S')], limit=1)

			data = {
				'name': 'Guest Buyer',
				'company_name': 'Guest Buyer',
				'city': 'Rosario',
				'zip': '2000',
				'phone': '2477610123',
				'vat': '43026589',
				'street': 'Calle falsa 123',
				'street2': '4-1',
				'consumidor_final': consumidor_final,
				'dni_type': dni_type,
				'country_id': country_id,
				'state_id': state_id,
			}

			# INYECTAR LOS VALORES A LA FUERZA
			if consumidor_final:
				address_values['l10n_ar_afip_responsibility_type_id'] = int(consumidor_final.id)
			if dni_type:
				address_values['l10n_latam_identification_type_id'] = int(dni_type.id)
			if country_id:
				address_values['country_id'] = int(country_id.id)
			if state_id:
				address_values['state_id'] = int(state_id.id)
			address_values['name'] = data['name']
			address_values['company_name'] = data['company_name']
			address_values['city'] = data['city']
			address_values['zip'] = data['zip']
			address_values['phone'] = data['phone']
			address_values['vat'] = data['vat']
			address_values['street'] = data['street']
			address_values['street2'] = data['street2']
			

			email = (address_values.get('email') or '').strip()
			if not email or not EMAIL_RE.match(email):
				return set(), {'email'}, [_('Ingresá un correo válido.')]

			required_fields = 'email'
			use_delivery_as_billing = True

			return super()._validate_address_values(
			address_values,
			partner_sudo,
			address_type,
			use_delivery_as_billing,
			required_fields,
			is_main_address,
			**kwargs,
		)

		return super()._validate_address_values(
			address_values,
			partner_sudo,
			address_type,
			use_delivery_as_billing,
			required_fields,
			is_main_address,
			**kwargs,
		)

	def _check_cart(self, order_sudo):
		redir = super()._check_cart(order_sudo)
		if redir:
			return redir
		return self._fotoapp_validate_single_photographer(order_sudo)

	def shop_address_submit(self, **post):
		order = request.website.sale_get_order()
		is_guest = self._fotoapp_is_guest_checkout(order)
		website_partner = request.website.user_id.sudo().partner_id if request.website and request.website.user_id else None

		if is_guest:
			email = (post.get('email') or '').strip() or (order.partner_id.email if order and order.partner_id else '')
			if not email or not EMAIL_RE.match(email):
				email = 'guest@example.com'
			_logger.info(
				"Guest checkout submit start | order=%s | email_input=%s",
				order and order.id,
				email,
			)

			partner_domain = [('email', '=', email)]
			if website_partner:
				partner_domain.append(('id', '!=', website_partner.id))
			partner = request.env['res.partner'].sudo().search(partner_domain, limit=1)
			if not partner:
				partner = request.env['res.partner'].sudo().create({
					'name': 'Guest Buyer',
					'email': email,
				})
				_logger.info("Guest checkout submit created partner %s for email %s", partner.id, email)
			else:
				_logger.info("Guest checkout submit reusing partner %s for email %s", partner.id, email)

			if order:
				order_vals = {
					'partner_id': partner.id,
					'partner_invoice_id': partner.id,
					'partner_shipping_id': partner.id,
					'fotoapp_delivery_email': email,
				}
				order.sudo().write(order_vals)
				_logger.info(
					"Guest checkout submit wrote order %s with partner %s vals=%s",
					order.id,
					partner.id,
					order_vals,
				)

			return request.redirect('/shop/payment')

		return super().shop_address_submit(**post)

	@http.route(['/shop/payment'], type='http', auth='public', website=True, sitemap=False)
	def shop_payment(self, **post):
		order = request.website.sale_get_order()
		is_guest = self._fotoapp_is_guest_checkout(order)

		if is_guest and order:
			# Asegura partner en el pedido
			if not order.partner_id:
				guest = request.website.user_id.sudo().partner_id
				order.sudo().write({
					'partner_id': guest.id,
					'partner_invoice_id': guest.id,
					'partner_shipping_id': guest.id,
				})
			# Renderiza directamente la página de pago sin redirecciones intermedias
			values = self._get_shop_payment_values(order, **post)
			values['fotoapp_guest'] = True
			_logger.info(
				"FotoApp shop_payment render guest | order=%s | user=%s | fotoapp_guest=%s | values_keys=%s",
				order.id,
				request.env.user.id,
				values.get('fotoapp_guest'),
				sorted(list(values.keys())),
			)
			return request.render("website_sale.payment", values)

		return super().shop_payment(**post)


class FotoappPaymentPortal(WebsiteSalePaymentPortal):
	@http.route('/fotoapp/guest_email', type='json', auth='public', website=True, csrf=False)
	def fotoapp_set_guest_email(self, email=None):
		order = request.website.sale_get_order()
		# Debug incoming payload to ensure the frontend is reaching this endpoint
		raw_body = request.httprequest.get_data(cache=True, as_text=True, parse_form_data=False)
		content_type = request.httprequest.content_type
		# Allow both JSON-RPC payloads and raw JSON bodies
		if not email:
			payload = {}
			try:
				payload = request.get_json_data() or {}
			except Exception:  # noqa: BLE001 - defensive, we ignore parse errors
				payload = {}
			email = payload.get('email') or payload.get('params', {}).get('email')
		_logger.info(
			"Guest email endpoint received | content_type=%s | email_kw=%s | payload=%s | raw=%s",
			content_type,
			email,
			payload,
			raw_body[:2000],
		)
		email_val = (email or '').strip()
		website_partner = request.website.user_id.sudo().partner_id if request.website and request.website.user_id else None
		if not order or not email_val or not EMAIL_RE.match(email_val):
			_logger.warning(
				"Guest email endpoint rejected | order=%s | email=%s",
				order and order.id,
				email,
			)
			return {'ok': False}
		_logger.info("Guest email endpoint start | order=%s | email=%s", order.id, email_val)
		partner_domain = [('email', '=', email_val)]
		if website_partner:
			partner_domain.append(('id', '!=', website_partner.id))
		partner = request.env['res.partner'].sudo().search(partner_domain, limit=1)
		if not partner:
			partner = request.env['res.partner'].sudo().create({
				'name': email_val,
				'email': email_val,
			})
			_logger.info("Guest email endpoint created partner %s for %s", partner.id, email_val)
		else:
			partner.sudo().write({'email': email_val})
			_logger.info("Guest email endpoint updated partner %s email to %s", partner.id, email_val)
		order.sudo().write({
			'partner_id': partner.id,
			'partner_invoice_id': partner.id,
			'partner_shipping_id': partner.id,
			'fotoapp_delivery_email': email_val,
		})
		_logger.info(
			"Guest email endpoint wrote order %s partner=%s delivery_email=%s",
			order.id,
			partner.id,
			email_val,
		)
		return {'ok': True}

	@http.route('/shop/payment/transaction/<int:order_id>', type='json', auth='public', website=True)
	def shop_payment_transaction(self, order_id, access_token, **kwargs):
		"""Captura guest_email antes de delegar en el flujo estándar de website_sale."""
		order_sudo = request.env['sale.order'].sudo().browse(order_id).exists()
		website_partner = request.website.user_id.sudo().partner_id if request.website and request.website.user_id else None
		raw_body = request.httprequest.get_data(cache=True, as_text=True, parse_form_data=False)
		content_type = request.httprequest.content_type
		email = (
			kwargs.pop('guest_email', '')
			or request.httprequest.form.get('guest_email')
			or ''
		).strip()
		order_delivery_email = (order_sudo.fotoapp_delivery_email or '').strip() if order_sudo else ''
		partner_email = ''
		if order_sudo and order_sudo.partner_id and website_partner and order_sudo.partner_id.id != website_partner.id:
			partner_email = (order_sudo.partner_id.email or '').strip()
		elif order_sudo and order_sudo.partner_id and not website_partner:
			partner_email = (order_sudo.partner_id.email or '').strip()
		if not email and order_delivery_email:
			email = order_delivery_email
		if not email and partner_email:
			email = partner_email

		_logger.info(
			"FotoApp shop_payment_transaction - guest email: %s | order_delivery_email: %s | partner_email: %s | kwargs keys: %s | form keys: %s | content_type=%s | raw_body=%s | order_id: %s",
			email,
			order_delivery_email,
			partner_email,
			list(kwargs.keys()),
			list(request.httprequest.form.keys()),
			content_type,
			raw_body[:2000],
			order_id,
		)

		if order_sudo and email and EMAIL_RE.match(email):
			partner_domain = [('email', '=', email)]
			if website_partner:
				partner_domain.append(('id', '!=', website_partner.id))
			partner = request.env['res.partner'].sudo().search(partner_domain, limit=1)
			if not partner:
				partner = request.env['res.partner'].sudo().create({
					'name': email,
					'email': email,
				})
				_logger.info(
					"Payment transaction created partner %s for email %s | order=%s",
					partner.id,
					email,
					order_sudo and order_sudo.id,
				)
			else:
				partner.sudo().write({'email': email})
				_logger.info(
					"Payment transaction updated partner %s email to %s | order=%s",
					partner.id,
					email,
					order_sudo and order_sudo.id,
				)
			order_sudo.sudo().write({
				'partner_id': partner.id,
				'partner_invoice_id': partner.id,
				'partner_shipping_id': partner.id,
				'fotoapp_delivery_email': email,
			})
			_logger.info(
				"Payment transaction wrote order %s partner=%s delivery_email=%s",
				order_sudo and order_sudo.id,
				partner.id,
				email,
			)
		else:
			_logger.warning(
				"FotoApp shop_payment_transaction - missing/invalid guest email, skipping partner update. Order: %s",
				order_sudo and order_sudo.id,
			)
			return {'error': _('Ingresá un correo válido para pagar.')}

		return super().shop_payment_transaction(order_id, access_token, **kwargs)