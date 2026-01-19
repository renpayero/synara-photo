/**
 * FotoApp: update cart badge immediately after adding a photo via AJAX.
 * Uses delegated listener instead of publicWidget to ensure it binds
 * even inside website editor or dynamic blocks.
 */
odoo.define('fotoapp.gallery_cart_badge', function (require) {
    'use strict';

    const ajax = require('web.ajax');
    const wSaleUtils = require('website_sale.utils');
    const domReady = require('web.dom_ready');

    const updateBadge = (qty) => {
        const apply = ($el) => {
            if (!$el || !$el.length) { return; }
            if (qty > 0) {
                $el.text(qty).removeClass('d-none o_hidden');
            } else {
                $el.text('').addClass('d-none o_hidden');
            }
        };
        apply($('.my_cart_quantity'));
        apply($('.o_cart_counter'));
        apply($('[data-cart-quantity]'));
        apply($('.o_wsale_my_cart .badge'));
        apply($('.o_wsale_my_cart span'));
        apply($('[data-menu-xmlid*="sale.menu_sale_root"] .badge'));
    };

    domReady(() => {
        if (window.__fotoappCartBound) { return; }
        window.__fotoappCartBound = true;

        $(document).on('submit', 'form.fotoapp-add-to-cart', function (ev) {
            ev.preventDefault();
            const $form = $(ev.currentTarget);
            const action = $form.attr('action');
            const formData = $form.serializeArray();
            formData.push({name: 'ajax', value: 1});

            ajax.post(action, formData).then((res) => {
                let payload = res;
                if (typeof res === 'string') {
                    try {
                        payload = JSON.parse(res);
                    } catch (err) {
                        payload = null;
                    }
                }

                if (payload && payload.error) { return; }
                const qty = payload && typeof payload.cart_qty !== 'undefined' ? payload.cart_qty : null;
                if (qty !== null) {
                    if (wSaleUtils && wSaleUtils.updateCartNavBar) {
                        wSaleUtils.updateCartNavBar(false, {cart_quantity: qty});
                        wSaleUtils.updateCartNavBar();
                    }
                    $(document).trigger('cart_quantity_changed', {quantity: qty});
                    $(document).trigger('update_cart_quantity', qty);
                    window.website_sale_cart_quantity = qty;

                    updateBadge(qty);
                }
            }).guardedCatch(() => {
                $form.off('submit');
                $form.trigger('submit');
            });
        });
    });
});
