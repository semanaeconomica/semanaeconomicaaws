# -*- encoding: utf-8 -*-
{
	'name': 'Generacion de Letras',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it'],
	'version': '1.0',
	'description':"""
		Generar Canje de Letras
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/account_letras_payment.xml',
		'views/account_letras.xml'
	],
	'installable': True
}
