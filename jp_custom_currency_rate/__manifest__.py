# -*- coding: utf-8 -*-
{
    'name': "Custom Currency Rate",

    'summary': """
        Utilizar tipos de cambio personalizado en facturas y pagos
        """,

    'description': """
        Este módulo ayuda a publicar los asientos contables tomando
        en cuenta los tipos de cambio personalizados tanto de las factuas
        como también los pagos.
    """,

    'author': "ITGRUPO",
    'website': "http://www.pvodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','account_fields_it'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
        'views/account_move.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
