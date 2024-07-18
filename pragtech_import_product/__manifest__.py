# -*- coding: utf-8 -*-
{
    'name': 'Odoo Import Product Data Utility',
    'version': '13.0.0',
    'sequence': 4,
    'summary': 'Easy to import odoo data of products through Excel import/CSV import import product data',
    'category': 'Extra Tools',
    'description': """
        Import product from CSV and Excel file
        ======================================
        <keywords>
        import product
        product data
        import product data
     """,
    'author': 'Pragmatic TechSoft Pvt Ltd.',
    'website': 'https://www.pragtech.co.in',
    'depends': ['base','popup_it','account_base_it','import_journal_entry_it'],
    'data': [
        'security/product_import_security.xml',
        'data/attachment_sample.xml',
        'views/product_import_view.xml',
    ],
    'images': ['static/description/Animated-import-productdata.gif'],
    'live_test_url': 'https://www.pragtech.co.in/company/proposal-form.html?id=310&name=import-data-product',
    'license': 'OPL-1',
    'price': 10,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
}
