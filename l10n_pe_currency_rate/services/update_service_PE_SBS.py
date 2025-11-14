# -*- coding: utf-8 -*-
# © 2009 Camptocamp
# © 2013-2014 Agustin Cruz openpyme.mx
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .currency_getter_interface import CurrencyGetterInterface
from odoo import fields
from datetime import datetime
import pytz

import logging
_logger = logging.getLogger(__name__)


class PeSbsGetter(CurrencyGetterInterface):
    """Implementation of Currency_getter_factory interface
    for SBS service

    """
    code = 'PE_SBS'
    name = 'Superintendencia de Banca, Seguros'
    supported_currency_array = [
        "NOK", "USD", "SEK", "JPY", "CAD", "GBP", "MXN","EUR", "CHF", "PEN"]

    def rate_retrieve(self, date = None):
        """ Get currency exchange from Banxico.xml and proccess it
        TODO: Get correct data from xml instead of process string
        """
        if not date:
            today = datetime.utcnow()
            tz_name = "America/Lima"
            today_utc = pytz.timezone('UTC').localize(today, is_dst=False)
            context_today = today_utc.astimezone(pytz.timezone(tz_name))
            date = fields.Date.to_string(context_today) 
        url = ('http://api.grupoyacck.com/tipocambio/sbs/%s/'%date) # '2018-03-17'
        import json

        logger = logging.getLogger(__name__)
        logger.debug("SBS currency rate service : connecting...")
        rawfile = self.get_url(url)

        data = json.loads(str(rawfile, 'utf-8'))
        if data.get('rates'):
            logger.debug("SBS sent a valid json file")
        else:
            purchase = False
            sale = False
        rates = {}
        for rate in data.get('rates', []):
            rates[rate.get('name', '')] = rate
        return rates

    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days=1, date = None):
        """implementation of abstract method of Curreny_getter_interface"""
        logger = logging.getLogger(__name__)
        # we do not want to update the main currency
        if main_currency in currency_array:
            currency_array.remove(main_currency)

        # Suported currencies
        suported = [
        "NOK", "USD", "SEK", "JPY", "CAD", "GBP", "MXN","EUR", "CHF", "PEN"]
        rates = self.rate_retrieve(date)
        if rates:
            for curr in currency_array:
                if curr in suported:
                    rate = rates.get(curr)
                    rate['purchase_value'] = rates.get(curr).get('purchase_value') or 0
                    rate['sale_value'] =  rates.get(curr).get('sale_value') or 0
                    self.updated_currency[curr] =rate
                else:
                    # No other currency supported
                    continue
                logger.debug("Rate retrieved : %s = %s %s" %
                             (main_currency, str(rates), curr))
        return self.updated_currency, self.log_info
