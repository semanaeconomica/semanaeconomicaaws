# -*- encoding: utf-8 -*-
{
	'name': 'Reporte PLE SUNAT',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_journal_rep_it','account_purchase_rep_it','account_sale_rep_it','account_fee_rep_it','account_percep_rep_it'],
	'version': '1.0',
	'description':"""
		Nuevo menu SUNAT para generar PLEs
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'sql_functions.sql',
		'security/security.xml',
		'views/account_sunat_menu.xml',
		'wizards/wizard_cuo_generator.xml',
		'wizards/account_sunat_rep.xml'
	],
	'installable': True
}