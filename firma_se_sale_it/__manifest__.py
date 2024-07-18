# -*- encoding: utf-8 -*-
{
    'name': 'Firma en Ventas y reporte',
    'category': 'purchase',
    'author': 'ITGRUPO',
    'depends': ['base','sale_management','web_digital_sign'],
    'version': '1.0',
    'description':"""
     Firma en Ventas y reporte
    """,
    'auto_install': False,
    'demo': [],
    'data': [
        #'security/ir.model.access.csv',
        'views/views.xml',
        #'data/secuence.xml'
        ],
    'installable': True
}