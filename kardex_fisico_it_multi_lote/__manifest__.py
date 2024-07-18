# -*- encoding: utf-8 -*-
{
    'name': 'Kardex Fisico',
    'version': '1.0',
    'author': 'ITGRUPO-COMPATIBLE-BO',
    'website': '',
    'category': 'account',
    'depends': ['product','stock','account','account_base_it'],
    'description': """KARDEX""",
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking_views.xml',
        'wizard/make_kardex_view.xml',
        'views/einvoice_catalog_12.xml'
    ],
    'auto_install': False,
    'installable': True
}
