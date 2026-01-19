/**
 * FotoApp: update cart badge immediately after adding a photo via AJAX.
 */
odoo.define('fotoapp.gallery_cart_badge', function (require) {
    'use strict';

    const publicWidget = require('web.public.widget');
    const ajax = require('web.ajax');
    const wSaleUtils = require('website_sale.utils');

    publicWidget.registry.FotoappGalleryCart = publicWidget.Widget.extend({
        selector: 'form.fotoapp-add-to-cart',
        events: {
            'submit': '_onSubmit',
        },

        _onSubmit: function (ev) {
            ev.preventDefault();
            const $form = $(ev.currentTarget);
            const action = $form.attr('action');
            const formData = $form.serializeArray();
            formData.push({name: 'ajax', value: 1});

            ajax.post(action, formData).then((res) => {
                if (res && res.error) {
                    // Optional: you could show a toast; keep silent for now.
                    return;
                }
                const qty = res && typeof res.cart_qty !== 'undefined' ? res.cart_qty : null;
                if (qty !== null) {
                    // Ask website_sale to refresh the navbar (keeps compatibility with themes)
                    if (wSaleUtils && wSaleUtils.updateCartNavBar) {
                        wSaleUtils.updateCartNavBar(false, {cart_quantity: qty});
                    }
                    $(document).trigger('cart_quantity_changed', {quantity: qty});
                    // Extra: push into window as some themes read from session var via RPC
                    window.website_sale_cart_quantity = qty;

                    // Manual fallback: update any existing badge
                    const $badge = $('.my_cart_quantity');
                    if ($badge.length) {
                        if (qty > 0) {
                            $badge.text(qty).removeClass('d-none');
                        } else {
                            $badge.text('').addClass('d-none');
                        }
                    }
                }
            }).guardedCatch(() => {
                // Fallback to normal submit on failure
                $form.off('submit');
                $form.trigger('submit');
            });
        },
    });

    return publicWidget.registry.FotoappGalleryCart;
});
