# -*- encoding: utf-8 -*-
{
    'name': 'Ebill CPE',
    'category': 'JESUS SANCHEZ JIBAJA',
    'author': 'ITGRUPO',
    'depends': ['ebill','base','account_base_it','account'],
    'version': '1.0',
    'description':"""
        Ajustes/Tecnico/Parametros CPE
    """,
    'auto_install': False,
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'views/ebill_parameter.xml',
        'views/reporte_factura_einvoice.xml',
        'views/account_move.xml',
        'views/einvoice.xml',
        'views/account_tax_repartition_line.xml',
        'views/einvoice_line.xml',
        'views/main_parameter.xml',
        'data/einvoice_catalog_09.xml',
        'data/einvoice_catalog_08.xml',
        'views/einvoice_catalog_08.xml'

        ],
    'installable': True
}