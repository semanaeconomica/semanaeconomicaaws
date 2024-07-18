# -*- encoding: utf-8 -*-
{
	'name': 'Pago Masivo de Detracciones',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_multipayment_advance_it'],
	'version': '1.0',
	'description':"""
	- Generar Pago Masivo de Detracciones en Base a Pagos Multiples
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/multipayment_advance_it.xml',
		'views/res_partner_bank.xml',
		'wizards/massive_payment_detractions_wizard.xml'
	],
	'installable': True
}