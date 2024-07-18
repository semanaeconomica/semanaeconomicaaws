# -*- encoding: utf-8 -*-
{
	'name': 'Anticipos en Lineas de Factura',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it'],
	'version': '1.0',
	'description':"""
	Aplicar Tipo y Nro de Dodumento a lineas de Anticipo
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/account_move.xml',
		'wizards/account_anticipos_wizard.xml'
	],
	'installable': True
}
