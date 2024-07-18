# -*- encoding: utf-8 -*-
{
    'name': 'Reporte de Orden y Pedido de Venta',
    'category': 'purchase',
    'author': 'ITGRUPO',
    'depends': ['purchase','sale_management','firma_se_sale_it'],
    'version': '1.0',
    'description':"""
    Reporte de Orden y Pedido de Venta
    """,
    'auto_install': False,
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'views/report_semana_economica.xml',
        'views/report_semana_economica2.xml',
        'views/parametros.xml',
        'data/plantilla.xml'
        ],
    'installable': True
}
