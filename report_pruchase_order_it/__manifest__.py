# -*- coding: utf-8 -*-
{
    'name': "Reporte de ordenes de compra SEMANAECONOMICA",
    'author': 'ITGRUPO, Alessandro Pelayo Mollocondo Medrano',
    'category': 'Purchase',
    'description': """Modulo que permite realizar un reporte de compras para obtener y realizar una analisis.""",
    'version': '1.0',
    'summary': 'Modificaciones personalizadas para purchase',
    'depends': ['purchase', 'account', 'base', 'stock', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/resport_purchase_order_invoice_it_wizard.xml',
        'views/resport_purchase_order_invoice_it.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}