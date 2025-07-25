# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Odoo 13 Assets Management',
    'version': '13.0.1.2.0',
    'author': 'Odoo Mates, Odoo SA-ITGRUPO',
    'depends': ['account','account_fields_it','popup_it','report_tools'],
    'description': """Manage assets owned by a company or a person. 
    Keeps track of depreciation's, and creates corresponding journal entries""",
    'summary': 'Odoo 13 Assets Management',
    'category': 'Accounting',
    'sequence': 32,
    'license': 'LGPL-3',
    'images': ['static/description/assets.gif'],
    'data': [
        'security/account_asset_security.xml',
        'security/ir.model.access.csv',
        'wizard/asset_modify_views.xml',
        'views/account_asset_views.xml',
        'views/account_invoice_views.xml',
        'views/account_asset_templates.xml',
        'views/product_views.xml',
        'views/account_asset_book.xml',
        'views/account_asset_71_book.xml',
        'views/account_asset_74_book.xml',
        'report/account_asset_report_views.xml',
        'data/account_asset_data.xml',
        'wizard/asset_depreciation_confirmation_wizard_views.xml',
        'wizard/account_asset_free_depreciation_wizard.xml',
        'wizard/account_asset_rep.xml',
        'wizard/account_asset_71_rep.xml',
        'wizard/account_asset_74_rep.xml',
        'activos.sql'
    ],
    'qweb': [
        "static/src/xml/account_asset_template.xml",
    ],
}
