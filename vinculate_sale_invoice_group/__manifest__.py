# -*- coding: utf-8 -*-
{
    'name': "Agregar grupo invoice",
    'author': 'ITGRUPO, Alessandro Pelayo Mollocondo Medrano',
    'category': 'Sale',
    'description': """Agregar funcionaldiad para que solo un grupo de usuario pueda hacer el cambio a este campo""",
    'version': '1.0',
    'summary': 'Modificaciones personalizadas para sale',
    'depends': ['sale','vinculate_sale_invoice_js_it'],
    'data': [
        'views/sale_order.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}