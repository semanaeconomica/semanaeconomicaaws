# -*- coding: utf-8 -*-
# © 2008-2016 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Peruvian Currency Rate Update For Companies",
    "version": "1.0",
    "author": "ITGRUPO",
    "category": "account",
    "depends": ['l10n_pe_currency_rate'],
    "data": [
        #"data/cron.xml",
        "wizard/currency_rate_update_wizard_view.xml",
        "wizard/currency_rate_update_now.xml",
        "view/res_currency.xml"
    ],
    'installable': True
}
