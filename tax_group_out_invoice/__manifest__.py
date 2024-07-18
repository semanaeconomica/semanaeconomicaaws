# -*- encoding: utf-8 -*-
{
	'name': 'Tax Group',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['base','account'],
	'version': '1.0',
	'description':"""
	Agregar Widget en Facturas de Clientes
	""",
	'auto_install': False,
	'demo': [],
	'data':	['views/account.xml',
			'views/account_move.xml'],
    'qweb': [
        'static/src/xml/tax_group.xml'
    ],
	'installable': True
}