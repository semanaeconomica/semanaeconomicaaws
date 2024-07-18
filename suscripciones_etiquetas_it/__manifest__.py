# -*- encoding: utf-8 -*-
{
    'name': 'Etiquetas Suscripciones',
    'category': 'purchase',
    'author': 'ITGRUPO',
    'depends': ['sales_subscriptions'],
    'version': '1.0',
    'description':"""
     Etiquetas Suscripciones
    """,
    'auto_install': False,
    'demo': [],
    'data': [
        #'security/ir.model.access.csv',
        'views/grupo.xml',
        'views/views.xml',
        'views/reporte_etiquetas.xml',
        'views/reporte_cargos.xml',

        #'data/plantilla.xml'
        ],
    'installable': True
}
