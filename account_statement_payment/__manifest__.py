# -*- encoding: utf-8 -*-
{
	'name': 'Account Statement Payment',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it'],
	'version': '1.0',
	'description':"""
	Modulo para obtener pagos en base al statement_id del Asiento Contable
	""",
	'auto_install': False,
	'demo': [],
	'data':	['views/account_bank_statement.xml',
			 'views/account_payment.xml'],
	'installable': True
}
