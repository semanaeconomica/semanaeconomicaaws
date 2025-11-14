# -*- coding: utf-8 -*-
{
    'name': "Suscripciones",
    'summary': """
        Modulo de registro de Suscripciones""",
    'description': """
        Registro de Suscripciones en modulo de ventas
    """,    'author': "Giovani Alire",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['sale','ebill'],

    'data': [
        'views/suscripciones_sale.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
    ],
 }
