# -*- coding: utf-8 -*-

{
    'name': "Campo Fomato en reporte ventas",
    'category': "sales",
    'author':'ITGRUPO',
    'description': """
        Campo Fomato en reporte ventas
    """,
    'depends': ['web_dashboard','modificaciones_formatos_ventas_it'],
    'data': [
        'view/sale_repord_add.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}
