# -*- encoding: utf-8 -*-
{
	'name': 'Multipayment to Statement',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['deltatech_payment_to_statement','account_multipayment_advance_it'],
	'version': '1.0',
	'description':"""
	Modulo para crear extractos desde pagos multiples
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/multipayment_advance_it.xml'
	],
	'installable': True
}