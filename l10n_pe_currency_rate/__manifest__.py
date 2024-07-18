# -*- coding: utf-8 -*-
# © 2008-2016 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Peruvian Currency Rate Update",
    "version": "1.0",
    "author": "Camptocamp,Odoo Community Association (OCA), FLEXXOONE, ITGRUPO",
    "website": "http://grupoyacck.com",
    "license": "AGPL-3",
    "category": "Financial Management/Configuration",
    "depends": ['account','base','account_base_it'],
    "data": [
        "data/decimal_point.xml",
        "views/res_currency_view.xml",
        "views/currency_rate_update.xml",
        "views/account_config_settings.xml",
        "security/rule.xml",
        "security/ir.model.access.csv",
    ],
    'installable': True
}
