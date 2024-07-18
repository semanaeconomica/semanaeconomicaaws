# -*- encoding: utf-8 -*-
{
	'name': 'Transferencias Gratuitas',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_base_it','account_fields_it'],
	'version': '1.0',
	'description':"""
	Generar Transferencias Gratuitas para facturas de Clientes
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/account_move.xml'
	],
	'installable': True
}