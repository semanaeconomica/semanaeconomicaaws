# -*- encoding: utf-8 -*-
{
	'name': 'Currency Rate Personalize',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account','base','account_fields_it','l10n_pe_currency_rate'],
	'version': '1.0',
	'description':"""
	USO DE TIPOS DE CAMBIO PERSONALIZADOS EN FORMULARIOS DE FACTURAS, RECTIFICATIVAS Y PAGOS 
	""",
	'auto_install': False,
	'demo': [],
	'data':	['views/account_move.xml',
			'views/account_payment.xml'],
	'installable': True
}
