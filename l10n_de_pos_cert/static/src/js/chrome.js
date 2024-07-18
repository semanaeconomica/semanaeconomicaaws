odoo.define('l10n_de_pos_cert.chrome', function (require) {
    'use strict';

    const widgets = require('point_of_sale.chrome');
    const core = require('web.core');
    const _t = core._t;

    widgets.Chrome.include({
        showFiskalyErrorPopup(error, message) {
            if (error.status === 0) {
                const title = _t('No internet');
                const body = message.noInternet;
                this.gui.show_popup('error', { title, body });
            } else if (error.status === 401 && error.source === 'authenticate') {
                this._showUnauthorizedPopup();
            } else if ((error.status === 400 && error.responseJSON.message.includes('tss_id')) ||
                (error.status === 404 && error.responseJSON.code === 'E_TSS_NOT_FOUND')) {
                this._showBadRequestPopup('TSS ID');
            } else if ((error.status === 400 && error.responseJSON.message.includes('client_id')) ||
                (error.status === 400 && error.responseJSON.code === 'E_CLIENT_NOT_FOUND')) {
                // the api is actually sending an 400 error for a "Not found" error
                this._showBadRequestPopup('Client ID');
            } else {
                const title = _t('Unknown error');
                const body = message.unknown;
                this.gui.show_popup('error', { title, body });
            }
        },
        _showUnauthorizedPopup() {
            const title = _t('Unauthorized error to Fiskaly');
            const body = _t(
                'It seems that your Fiskaly API key and/or secret are incorrect. Update them in your company settings.'
            );
            this.gui.show_popup('error', { title, body });
        },
        _showBadRequestPopup(data) {
            const title = _t('Bad request');
            const body = _.str.sprintf(_t('Your %s is incorrect. Update it in your PoS settings'), data);
            this.gui.show_popup('error', { title, body });
        },
        showTaxError() {
            const rates = Object.keys(this.pos.vatRateMapping);
            const title = _t('Tax error');
            let body;
            if (rates.length) {
                const ratesText = [rates.slice(0,-1).join(', '), rates.slice(-1)[0]].join(' and ');
                body = _.str.sprintf(_t(
                    'Product has an invalid tax amount. Only the following rates are allowed: %s.'
                ), ratesText);
            } else {
                body = _t('There was an error while loading the Germany taxes. Try again later or your Fiskaly API key and secret might have been corrupted, request new ones')
            }
            this.gui.show_popup('error', { title, body });
        },
        showFiskalyNoInternetConfirmPopup(callback) {
            this.gui.show_popup('confirm',{
                'title': _t('Problem with internet'),
                'body': _t(
                    'You can either wait for the connection issue to be resolved or continue with a non-compliant receipt (the order will still be sent to Fiskaly once the connection issue is resolved).\n' +
                    'Do you want to continue with a non-compliant receipt ?'
                ),
                confirm: callback,
            })
        }
    });

});
