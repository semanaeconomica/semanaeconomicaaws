# -*- encoding: utf-8 -*-
{
	'name': 'Detracciones',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_base_it'],
	'version': '1.0',
	'description':"""
	Generar Detracciones en Facturas de Clientes y Proveedores
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/account_detractions_wizard.xml',
		'views/account_move.xml'
	],
	'installable': True
}
