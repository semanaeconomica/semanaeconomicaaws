# -*- coding: utf-8 -*-
{
    'name': "Campos nuevos al reporte de ventas",
    'summary': """
        Campos nuevos al reporte de ventas""",
    'description': """
        Campos nuevos al reporte de ventas
    """,    'author': "ITGrupo",
    'category': 'Sale',
    'version': '0.1',
    'depends': ['sale_enterprise','sales_subscriptions'],

    'data': [
        'views/sale_report_view.xml',
    ],
    'installable': True,
    'application': False,
 }