# -*- encoding: utf-8 -*-
{
	'name': 'Account Batch Payment IT',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it','account_batch_payment'],
	'version': '1.0',
	'description':"""
	Herencia del Modulo Account Batch Payment para cambiar su comportamiento
	""",
	'auto_install': False,
	'demo': [],
	'data':	['views/account_batch_payment.xml',
			 'views/account_payment.xml'],
	'installable': True
}
